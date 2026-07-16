from unittest.mock import PropertyMock

import pandas as pd
import pytest

from campari_valuation.data import (
    _fetch_info_with_retry,
    fetch_snapshot,
    fetch_weekly_returns,
)

_BASE_INFO = {
    "shortName": "Test Co",
    "currency": "EUR",
    "financialCurrency": "EUR",
    "regularMarketPrice": 10.0,
    "marketCap": 1000.0,
    "enterpriseValue": 1200.0,
    "sharesOutstanding": 100.0,
    "ebitda": 100.0,
    "totalRevenue": 500.0,
    "netIncomeToCommon": 50.0,
    "bookValue": 5.0,
    "totalDebt": 300.0,
    "totalCash": 100.0,
    "trailingPE": 20.0,
    "priceToBook": 2.0,
}


def _mock_ticker_info(mocker, info: dict):
    ticker_class = mocker.patch("campari_valuation.data.yf.Ticker")
    ticker_class.return_value.info = info
    return ticker_class


def test_fetch_snapshot_parses_a_normal_eur_quote(mocker):
    _mock_ticker_info(mocker, dict(_BASE_INFO))

    snapshot = fetch_snapshot("TEST")

    assert snapshot.price == pytest.approx(10.0)
    assert snapshot.market_cap == pytest.approx(1000.0)
    assert snapshot.ebitda == pytest.approx(100.0)
    assert not snapshot.currency_mismatch


def test_fetch_snapshot_converts_pence_to_pounds(mocker):
    info = dict(_BASE_INFO, currency="GBp", financialCurrency="GBP", regularMarketPrice=1531.0)
    _mock_ticker_info(mocker, info)

    snapshot = fetch_snapshot("DGE.L")

    assert snapshot.price == pytest.approx(15.31)


def test_fetch_snapshot_flags_currency_mismatch(mocker):
    info = dict(_BASE_INFO, currency="GBp", financialCurrency="USD")
    _mock_ticker_info(mocker, info)

    snapshot = fetch_snapshot("DGE.L")

    assert snapshot.currency_mismatch


def test_fetch_snapshot_does_not_flag_pence_vs_pounds_as_a_mismatch(mocker):
    info = dict(_BASE_INFO, currency="GBp", financialCurrency="GBP")
    _mock_ticker_info(mocker, info)

    snapshot = fetch_snapshot("DGE.L")

    assert not snapshot.currency_mismatch


def test_fetch_snapshot_raises_on_missing_required_field(mocker):
    info = dict(_BASE_INFO)
    del info["ebitda"]
    _mock_ticker_info(mocker, info)

    with pytest.raises(ValueError, match="ebitda"):
        fetch_snapshot("TEST")


def test_fetch_snapshot_handles_missing_optional_fields(mocker):
    info = dict(_BASE_INFO)
    del info["trailingPE"]
    del info["priceToBook"]
    _mock_ticker_info(mocker, info)

    snapshot = fetch_snapshot("TEST")

    assert snapshot.trailing_pe is None
    assert snapshot.price_to_book is None


def test_fetch_info_with_retry_succeeds_after_transient_failures(mocker):
    ticker_class = mocker.patch("campari_valuation.data.yf.Ticker")
    type(ticker_class.return_value).info = PropertyMock(
        side_effect=[RuntimeError("502"), RuntimeError("502"), dict(_BASE_INFO)]
    )
    mocker.patch("campari_valuation.data.time.sleep")  # skip the real delay in tests

    info = _fetch_info_with_retry("TEST")

    assert info["shortName"] == "Test Co"


def test_fetch_info_with_retry_raises_after_exhausting_attempts(mocker):
    ticker_class = mocker.patch("campari_valuation.data.yf.Ticker")
    type(ticker_class.return_value).info = PropertyMock(side_effect=RuntimeError("502"))
    mocker.patch("campari_valuation.data.time.sleep")

    with pytest.raises(RuntimeError, match="failed to fetch"):
        _fetch_info_with_retry("TEST")


def test_fetch_weekly_returns_computes_pct_change(mocker):
    dates = pd.date_range("2024-01-05", periods=12, freq="W-FRI")
    closes = pd.Series([100.0 + i for i in range(12)], index=dates)
    history_df = pd.DataFrame({"Close": closes})
    ticker_class = mocker.patch("campari_valuation.data.yf.Ticker")
    ticker_class.return_value.history.return_value = history_df

    returns = fetch_weekly_returns("TEST", years=0.25)

    assert len(returns) == 11  # one fewer than the price series, from pct_change


def test_fetch_weekly_returns_rejects_empty_history(mocker):
    ticker_class = mocker.patch("campari_valuation.data.yf.Ticker")
    ticker_class.return_value.history.return_value = pd.DataFrame()

    with pytest.raises(ValueError, match="no price history"):
        fetch_weekly_returns("TEST", years=1.0)


def test_fetch_weekly_returns_rejects_insufficient_history(mocker):
    dates = pd.date_range("2024-01-05", periods=3, freq="W-FRI")
    history_df = pd.DataFrame({"Close": [100.0, 101.0, 102.0]}, index=dates)
    ticker_class = mocker.patch("campari_valuation.data.yf.Ticker")
    ticker_class.return_value.history.return_value = history_df

    with pytest.raises(ValueError, match="insufficient"):
        fetch_weekly_returns("TEST", years=1.0)
