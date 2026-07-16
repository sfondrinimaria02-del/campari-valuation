"""Integration tests against the real Yahoo Finance API - excluded from the
default run (see the `integration` marker in pyproject.toml); run explicitly
with `pytest -m integration`.
"""

from __future__ import annotations

import pytest

from campari_valuation.data import fetch_snapshot, fetch_weekly_returns
from campari_valuation.validate import CAMPARI_TICKER, PEER_TICKERS, run_validation

pytestmark = pytest.mark.integration


def test_fetch_snapshot_real_campari():
    snapshot = fetch_snapshot(CAMPARI_TICKER)
    assert snapshot.price > 0
    assert snapshot.ebitda > 0
    assert not snapshot.currency_mismatch  # CPR.MI: EUR price, EUR financials


def test_fetch_snapshot_flags_the_known_diageo_currency_mismatch():
    snapshot = fetch_snapshot("DGE.L")
    assert snapshot.currency_mismatch  # documented, empirically-verified Yahoo quirk


def test_fetch_weekly_returns_real_data():
    returns = fetch_weekly_returns(CAMPARI_TICKER, years=1.0)
    assert len(returns) > 40


def test_run_validation_end_to_end():
    report = run_validation()

    assert report.campari.ticker == CAMPARI_TICKER
    assert len(report.peers) == len(PEER_TICKERS)
    assert report.live_peer_median_ev_ebitda > 0
    assert -2.0 < report.live_raw_beta_home < 3.0  # a sanity range, not a precise claim
