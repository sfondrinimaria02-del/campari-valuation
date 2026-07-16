"""Cross-check the Excel model's market-observable assumptions (peer trading
multiples, beta) against a fresh live data pull. Judgment-based forecast
inputs (revenue growth, margins, terminal growth, the equity risk premium)
are not "live-checkable" at all - there is no market data that tells you
whether a 2.0% terminal growth assumption is right - so this module does not
pretend to validate those; it only re-derives the handful of inputs that a
live market data source can, in principle, independently confirm or refute.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from campari_valuation.beta import blume_adjust, regression_beta
from campari_valuation.data import CompanySnapshot, fetch_snapshot, fetch_weekly_returns
from campari_valuation.multiples import (
    Multiples,
    compute_multiples,
    implied_share_price_from_ev_multiple,
    peer_median_ev_to_ebitda,
    peer_median_pe,
)

CAMPARI_TICKER = "CPR.MI"
PEER_TICKERS: dict[str, str] = {
    "DGE.L": "Diageo",
    "RI.PA": "Pernod Ricard",
    "RCO.PA": "Remy Cointreau",
    "BF-B": "Brown-Forman",
}
BETA_LOOKBACK_YEARS = 2.0  # a standard practitioner window for a weekly-return beta

# Beta is reported against two benchmarks rather than one, because the choice
# turns out to matter a lot in practice: an empirical sensitivity check across
# four candidate European indices swung Campari's regression beta from 0.49 to
# 0.85 (see RESEARCH_NOTE.md) - a >70% range driven entirely by benchmark
# choice, at a fixed lookback and frequency. Reporting one number here would
# imply a false precision that a single "the beta is X" claim doesn't have.
BETA_BENCHMARK_HOME = "FTSEMIB.MI"  # Campari's home listing (Borsa Italiana) -
# the conventional default for a single stock's CAPM beta, and empirically the
# benchmark that reconciles most closely with the Excel model's vendor-sourced
# raw beta of 0.43.
BETA_BENCHMARK_BROAD = "^STOXX"  # STOXX Europe 600 - a pan-European alternative,
# relevant because Campari's revenue and peer set are pan-European/global
# rather than Italian-domestic.


@dataclass(frozen=True)
class ExcelAssumptions:
    """Every market-observable figure the Excel model states, transcribed
    verbatim from Campari_DCF_Model.xlsx (Assumptions and Comps tabs) so the
    live comparison has an explicit, auditable reference point rather than a
    number re-typed from the README."""

    reference_date: str = "2026-07-02"
    share_price_eur: float = 5.49
    shares_outstanding_m: float = 1199.0
    net_financial_debt_eur_m: float = 1958.0
    ebitda_adjusted_eur_m: float = 785.0  # FY2025A, company-defined non-GAAP measure
    raw_beta: float = 0.43  # stockanalysis.com, Jul 2026 - a vendor figure, not
    # self-computed in the Excel; this module's live regression is a genuine,
    # independent re-derivation, not a re-statement of the same source.
    risk_free_rate: float = 0.0301  # 10Y Bund, TradingEconomics, Jun 2026
    equity_risk_premium: float = 0.055  # Damodaran mature-market ERP - a judgment
    # input with no live market source; not validated here (see module docstring).
    peer_ev_to_ebitda: dict[str, float] = field(
        default_factory=lambda: {
            "Diageo": 11.25,
            "Pernod Ricard": 9.43,
            "Remy Cointreau": 14.17,
            "Brown-Forman": 12.08,
        }
    )
    peer_pe_forward: dict[str, float] = field(
        default_factory=lambda: {
            "Diageo": 12.79,
            "Pernod Ricard": 10.83,
            "Remy Cointreau": 27.05,
            "Brown-Forman": 15.38,
        }
    )

    @property
    def blume_beta(self) -> float:
        return blume_adjust(self.raw_beta)


EXCEL = ExcelAssumptions()


@dataclass(frozen=True)
class ValidationReport:
    campari: CompanySnapshot
    peers: list[CompanySnapshot]
    campari_multiples: Multiples
    peer_multiples: list[Multiples]
    live_raw_beta_home: float
    live_raw_beta_broad: float
    live_blume_beta_home: float
    live_blume_beta_broad: float
    live_peer_median_ev_ebitda: float
    live_peer_median_pe: float
    live_implied_price_ev_ebitda: float
    currency_mismatch_tickers: list[str]


def run_validation() -> ValidationReport:
    campari = fetch_snapshot(CAMPARI_TICKER)
    peers = [fetch_snapshot(ticker) for ticker in PEER_TICKERS]

    campari_multiples = compute_multiples(campari)
    peer_multiples = [compute_multiples(peer) for peer in peers]

    campari_returns = fetch_weekly_returns(CAMPARI_TICKER, BETA_LOOKBACK_YEARS)
    home_returns = fetch_weekly_returns(BETA_BENCHMARK_HOME, BETA_LOOKBACK_YEARS)
    broad_returns = fetch_weekly_returns(BETA_BENCHMARK_BROAD, BETA_LOOKBACK_YEARS)
    live_raw_beta_home = regression_beta(campari_returns, home_returns)
    live_raw_beta_broad = regression_beta(campari_returns, broad_returns)

    live_median_ev_ebitda = peer_median_ev_to_ebitda(peer_multiples)
    live_median_pe = peer_median_pe(peer_multiples)

    implied_price = implied_share_price_from_ev_multiple(
        campari_ebitda=campari.ebitda,
        peer_median_multiple=live_median_ev_ebitda,
        net_debt=campari.enterprise_value - campari.market_cap,
        shares_outstanding=campari.shares_outstanding,
    )

    mismatched = [s.ticker for s in [campari, *peers] if s.currency_mismatch]

    return ValidationReport(
        campari=campari,
        peers=peers,
        campari_multiples=campari_multiples,
        peer_multiples=peer_multiples,
        live_raw_beta_home=live_raw_beta_home,
        live_raw_beta_broad=live_raw_beta_broad,
        live_blume_beta_home=blume_adjust(live_raw_beta_home),
        live_blume_beta_broad=blume_adjust(live_raw_beta_broad),
        live_peer_median_ev_ebitda=live_median_ev_ebitda,
        live_peer_median_pe=live_median_pe,
        live_implied_price_ev_ebitda=implied_price,
        currency_mismatch_tickers=mismatched,
    )
