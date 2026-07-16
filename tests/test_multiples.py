import pytest

from campari_valuation.data import CompanySnapshot
from campari_valuation.multiples import (
    compute_multiples,
    implied_share_price_from_ev_multiple,
    peer_median_ev_to_ebitda,
    peer_median_pe,
)


def _snapshot(**overrides) -> CompanySnapshot:
    defaults = dict(
        ticker="TEST",
        name="Test Co",
        price_currency="EUR",
        financial_currency="EUR",
        price=10.0,
        market_cap=1000.0,
        enterprise_value=1200.0,
        shares_outstanding=100.0,
        ebitda=100.0,
        revenue=500.0,
        net_income=50.0,
        book_value_per_share=5.0,
        total_debt=300.0,
        total_cash=100.0,
        trailing_pe=20.0,
        price_to_book=2.0,
    )
    defaults.update(overrides)
    return CompanySnapshot(**defaults)


def test_compute_multiples_basic_ratios():
    snapshot = _snapshot(enterprise_value=1200.0, ebitda=100.0, revenue=500.0)

    multiples = compute_multiples(snapshot)

    assert multiples.ev_to_ebitda == pytest.approx(12.0)
    assert multiples.ev_to_sales == pytest.approx(2.4)
    assert multiples.pe_ratio == pytest.approx(20.0)
    assert multiples.price_to_book == pytest.approx(2.0)


def test_compute_multiples_rejects_non_positive_ebitda():
    snapshot = _snapshot(ebitda=0.0)
    with pytest.raises(ValueError, match="EBITDA"):
        compute_multiples(snapshot)


def test_compute_multiples_rejects_non_positive_revenue():
    snapshot = _snapshot(revenue=-1.0)
    with pytest.raises(ValueError, match="revenue"):
        compute_multiples(snapshot)


def test_compute_multiples_handles_missing_pe():
    snapshot = _snapshot(trailing_pe=None, price_to_book=None)

    multiples = compute_multiples(snapshot)

    assert multiples.pe_ratio is None
    assert multiples.price_to_book is None


def test_peer_median_ev_to_ebitda():
    multiples = [
        compute_multiples(_snapshot(enterprise_value=e, ebitda=100.0))
        for e in [900.0, 1100.0, 1300.0]
    ]

    assert peer_median_ev_to_ebitda(multiples) == pytest.approx(11.0)


def test_peer_median_ev_to_ebitda_rejects_empty_list():
    with pytest.raises(ValueError, match="not be empty"):
        peer_median_ev_to_ebitda([])


def test_peer_median_pe_ignores_missing_values():
    multiples = [
        compute_multiples(_snapshot(trailing_pe=10.0)),
        compute_multiples(_snapshot(trailing_pe=None)),
        compute_multiples(_snapshot(trailing_pe=20.0)),
    ]

    assert peer_median_pe(multiples) == pytest.approx(15.0)


def test_peer_median_pe_raises_when_no_peer_has_a_pe():
    multiples = [compute_multiples(_snapshot(trailing_pe=None))]
    with pytest.raises(ValueError, match="no peer"):
        peer_median_pe(multiples)


def test_implied_share_price_from_ev_multiple():
    price = implied_share_price_from_ev_multiple(
        campari_ebitda=785.0,
        peer_median_multiple=11.7,
        net_debt=1958.0,
        shares_outstanding=1199.0,
    )

    expected_ev = 785.0 * 11.7
    expected_equity = expected_ev - 1958.0
    assert price == pytest.approx(expected_equity / 1199.0)
