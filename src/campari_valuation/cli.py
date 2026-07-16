"""Command-line entry point: fetch live data and print the validation report."""

from __future__ import annotations

import json
import platform
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from campari_valuation.validate import EXCEL, PEER_TICKERS, ValidationReport, run_validation

RESULTS = Path("results")


def _print_report(report: ValidationReport) -> None:
    print(f"\nCampari (CPR.MI) live snapshot vs. Excel model ({EXCEL.reference_date})")
    print("-" * 72)
    print(f"{'Metric':<32}{'Live':>18}{'Excel':>18}")
    print(f"{'Share price (EUR)':<32}{report.campari.price:>18.2f}{EXCEL.share_price_eur:>18.2f}")
    print(
        f"{'Raw beta vs FTSE MIB (home)':<32}{report.live_raw_beta_home:>18.2f}"
        f"{EXCEL.raw_beta:>18.2f}"
    )
    print(f"{'Raw beta vs STOXX 600 (broad)':<32}{report.live_raw_beta_broad:>18.2f}{'':>18}")
    print(
        f"{'Blume beta vs FTSE MIB (home)':<32}{report.live_blume_beta_home:>18.2f}"
        f"{EXCEL.blume_beta:>18.2f}"
    )
    print(f"{'Blume beta vs STOXX 600 (broad)':<32}{report.live_blume_beta_broad:>18.2f}{'':>18}")
    print(
        f"{'Peer median EV/EBITDA':<32}{report.live_peer_median_ev_ebitda:>17.2f}x"
        f"{peer_median_reference(EXCEL.peer_ev_to_ebitda):>17.2f}x"
    )
    print(
        f"{'Peer median P/E':<32}{report.live_peer_median_pe:>17.2f}x"
        f"{peer_median_reference(EXCEL.peer_pe_forward):>17.2f}x"
    )
    print("  (note: live P/E is trailing; Excel's is forward-looking - expect some gap)")
    print(
        f"{'Implied price @ peer EV/EBITDA':<32}{report.live_implied_price_ev_ebitda:>18.2f}"
        f"{'n/a':>18}"
    )

    print("\nPeer trading multiples (live):")
    for ticker, multiples in zip(PEER_TICKERS, report.peer_multiples, strict=True):
        name = PEER_TICKERS[ticker]
        pe_display = f"{multiples.pe_ratio:.2f}x" if multiples.pe_ratio is not None else "n/a"
        print(f"  {name:<18} EV/EBITDA {multiples.ev_to_ebitda:>6.2f}x   P/E {pe_display:>8}")

    if report.currency_mismatch_tickers:
        print(
            "\nCAUTION - currency mismatch between quoted price and reported financials "
            f"for: {', '.join(report.currency_mismatch_tickers)}. Multiples for these "
            "tickers may be less reliable than the others; see README/RESEARCH_NOTE."
        )


def peer_median_reference(values: dict[str, float]) -> float:
    ordered = sorted(values.values())
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    report = run_validation()
    _print_report(report)

    fig, ax = plt.subplots(figsize=(8, 5))
    names = list(PEER_TICKERS.values())
    live_values = [m.ev_to_ebitda for m in report.peer_multiples]
    excel_values = [EXCEL.peer_ev_to_ebitda[name] for name in names]
    x = range(len(names))
    width = 0.35
    ax.bar([i - width / 2 for i in x], excel_values, width, label="Excel (Jun-Jul 2026)")
    ax.bar([i + width / 2 for i in x], live_values, width, label="Live")
    ax.set_xticks(list(x))
    ax.set_xticklabels(names, rotation=15)
    ax.set_ylabel("EV / EBITDA (x)")
    ax.set_title("Peer EV/EBITDA: Excel model vs. live re-check")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(RESULTS / "peer_multiples_validation.png", dpi=150)
    plt.close(fig)

    metadata = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "python": platform.python_version(),
        "yfinance": version("yfinance"),
        "campari_price_eur": report.campari.price,
        "live_raw_beta_home_ftsemib": report.live_raw_beta_home,
        "live_raw_beta_broad_stoxx600": report.live_raw_beta_broad,
        "live_blume_beta_home_ftsemib": report.live_blume_beta_home,
        "live_blume_beta_broad_stoxx600": report.live_blume_beta_broad,
        "live_peer_median_ev_ebitda": report.live_peer_median_ev_ebitda,
        "live_implied_price_ev_ebitda": report.live_implied_price_ev_ebitda,
        "currency_mismatch_tickers": report.currency_mismatch_tickers,
    }
    (RESULTS / "validation_metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    print(f"\nSaved chart and metadata to {RESULTS}/")


if __name__ == "__main__":
    main()
