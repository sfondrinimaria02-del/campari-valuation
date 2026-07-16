"""Trading multiples and peer-median implied valuation."""

from __future__ import annotations

import statistics
from dataclasses import dataclass

from campari_valuation.data import CompanySnapshot


@dataclass(frozen=True)
class Multiples:
    ticker: str
    ev_to_ebitda: float
    ev_to_sales: float
    pe_ratio: float | None
    price_to_book: float | None


def compute_multiples(snapshot: CompanySnapshot) -> Multiples:
    if snapshot.ebitda <= 0:
        raise ValueError(f"{snapshot.ticker}: EBITDA must be positive to compute EV/EBITDA")
    if snapshot.revenue <= 0:
        raise ValueError(f"{snapshot.ticker}: revenue must be positive to compute EV/Sales")

    return Multiples(
        ticker=snapshot.ticker,
        ev_to_ebitda=snapshot.enterprise_value / snapshot.ebitda,
        ev_to_sales=snapshot.enterprise_value / snapshot.revenue,
        pe_ratio=snapshot.trailing_pe,
        price_to_book=snapshot.price_to_book,
    )


def peer_median_ev_to_ebitda(peer_multiples: list[Multiples]) -> float:
    if not peer_multiples:
        raise ValueError("peer_multiples must not be empty")
    return statistics.median(m.ev_to_ebitda for m in peer_multiples)


def peer_median_pe(peer_multiples: list[Multiples]) -> float:
    values = [m.pe_ratio for m in peer_multiples if m.pe_ratio is not None]
    if not values:
        raise ValueError("no peer has a trailing P/E available")
    return statistics.median(values)


def implied_share_price_from_ev_multiple(
    campari_ebitda: float,
    peer_median_multiple: float,
    net_debt: float,
    shares_outstanding: float,
) -> float:
    """Implied Campari share price from EV = peer median EV/EBITDA x EBITDA."""
    implied_ev = campari_ebitda * peer_median_multiple
    implied_equity_value = implied_ev - net_debt
    return implied_equity_value / shares_outstanding
