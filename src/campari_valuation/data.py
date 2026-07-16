"""Live market/fundamental data fetching, with the currency-unit handling that
free equity data genuinely requires - verified empirically against real tickers
rather than assumed (see docs in the module functions below).
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import pandas as pd
import yfinance as yf

# Yahoo's quote-summary endpoint (Ticker.info) occasionally 502s transiently;
# a short retry makes real runs reliable without masking a genuine failure.
_RETRY_ATTEMPTS = 3
_RETRY_DELAY_SECONDS = 2.0


@dataclass(frozen=True)
class CompanySnapshot:
    """A single company's market + fundamental data, in consistent, correctly
    scaled units (major currency unit throughout - see `_fetch_info_with_retry`
    for why that isn't as trivial as it sounds for London-listed tickers)."""

    ticker: str
    name: str
    price_currency: str
    financial_currency: str
    price: float
    market_cap: float
    enterprise_value: float
    shares_outstanding: float
    ebitda: float
    revenue: float
    net_income: float
    book_value_per_share: float
    total_debt: float
    total_cash: float
    trailing_pe: float | None
    price_to_book: float | None

    @property
    def currency_mismatch(self) -> bool:
        """True when Yahoo reports this ticker's price and its fundamentals in
        different currencies - verified empirically for DGE.L (LSE, priced in
        GBp, but `financialCurrency` reported as USD while `marketCap` and
        `enterpriseValue` are nonetheless GBP-scale). Rather than guess at an
        FX correction that could silently make things worse, this flag is
        surfaced so multiples for an affected ticker are read with caution.
        """
        # "GBp" (pence) and "GBP" (pounds) are the same underlying currency at
        # different scales, not a mismatch - normalize before comparing.
        normalized_price_currency = "GBP" if self.price_currency == "GBp" else self.price_currency
        return normalized_price_currency.upper() != self.financial_currency.upper()


def _fetch_info_with_retry(ticker: str) -> dict:
    last_error: Exception | None = None
    for attempt in range(_RETRY_ATTEMPTS):
        try:
            info = yf.Ticker(ticker).info
            if not info or info.get("regularMarketPrice") is None:
                raise ValueError(f"empty or incomplete quote response for {ticker!r}")
            return info
        except Exception as exc:  # noqa: BLE001 - retried below, re-raised if exhausted
            last_error = exc
            if attempt < _RETRY_ATTEMPTS - 1:
                time.sleep(_RETRY_DELAY_SECONDS)
    raise RuntimeError(f"failed to fetch quote data for {ticker!r} after retries") from last_error


def _major_unit_price(info: dict) -> float:
    """Yahoo quotes some London-listed tickers (currency 'GBp') in pence while
    still reporting marketCap/enterpriseValue in pounds - verified empirically:
    for DGE.L, price * shares == the naive (uncorrected) marketCap field, i.e.
    fast_info['marketCap'] does NOT self-correct for this. `regularMarketPrice`
    behaves the same way. Divide by 100 whenever the currency code is pence.
    """
    price = float(info["regularMarketPrice"])
    if info.get("currency") == "GBp":
        return price / 100.0
    return price


def fetch_snapshot(ticker: str) -> CompanySnapshot:
    """Fetch a single company's current market and fundamental snapshot."""
    info = _fetch_info_with_retry(ticker)

    required = ["marketCap", "enterpriseValue", "sharesOutstanding", "ebitda", "totalRevenue"]
    missing = [key for key in required if info.get(key) is None]
    if missing:
        raise ValueError(f"{ticker!r} quote response is missing required fields: {missing}")

    return CompanySnapshot(
        ticker=ticker,
        name=str(info.get("shortName") or ticker),
        price_currency=str(info.get("currency", "")),
        financial_currency=str(info.get("financialCurrency", "")),
        price=_major_unit_price(info),
        market_cap=float(info["marketCap"]),
        enterprise_value=float(info["enterpriseValue"]),
        shares_outstanding=float(info["sharesOutstanding"]),
        ebitda=float(info["ebitda"]),
        revenue=float(info["totalRevenue"]),
        net_income=float(info.get("netIncomeToCommon") or float("nan")),
        book_value_per_share=float(info.get("bookValue") or float("nan")),
        total_debt=float(info.get("totalDebt") or float("nan")),
        total_cash=float(info.get("totalCash") or float("nan")),
        trailing_pe=(float(info["trailingPE"]) if info.get("trailingPE") is not None else None),
        price_to_book=(float(info["priceToBook"]) if info.get("priceToBook") is not None else None),
    )


def fetch_weekly_returns(ticker: str, years: float) -> pd.Series:
    """Weekly total-return series for beta regression (Friday closes)."""
    period_days = int(years * 365.25) + 10
    history = yf.Ticker(ticker).history(period=f"{period_days}d", interval="1wk", auto_adjust=True)
    if history.empty:
        raise ValueError(f"no price history returned for {ticker!r}")
    closes = history["Close"].dropna()
    if len(closes) < 10:
        raise ValueError(f"insufficient price history for {ticker!r} to compute a beta")
    return closes.pct_change().dropna()
