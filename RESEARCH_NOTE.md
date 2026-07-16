# Davide Campari-Milano N.V. (BIT: CPR) — Valuation Note

*Maria Sfondrini — July 2026 · Academic portfolio project, not investment advice*
*Companion file: Campari_DCF_Model.xlsx (all figures reproduce from the model)*

## 1. Company and setup

Campari is a global premium-spirits group (Aperol, Campari, Espolòn, Wild Turkey, Courvoisier)
with FY2025 net sales of €3,051m (+2.4% organic), EBITDA-adjusted of €785m (25.7% margin) and
net financial debt of €1,958m (2.5x EBITDA, down from a 3.6x peak in Sept 2024). The stock
closed at €5.49 on July 2, 2026 (market cap €6.6bn) — down sharply over the past year amid a
sector-wide spirits downturn, US tariff headwinds (~€30m guided for 2026) and non-core
disposals (~€(70)m perimeter effect). The question this note asks: **does €5.49 already price
in the bad news?**

## 2. Method

Two approaches, triangulated: (i) a 5-year FCFF DCF with both Gordon-growth and exit-multiple
terminal values; (ii) trading comparables against Diageo, Pernod Ricard, Rémy Cointreau and
Brown-Forman. Key assumptions (full rationale in the model's Assumptions tab):

| Assumption | Value | Basis |
|---|---|---|
| Revenue growth 2026E → 2030E | +0.5% → +2.5-3.0% | 2026 ~flat on guided tariffs + disposals; then premium-spirits recovery |
| EBITDA-adj margin 2026E → 2030E | 26.0% → 27.0% | SG&A programme (200bps by 2027) partly reinvested |
| Capex (% sales) | 7.0% → 4.5% | Extraordinary capex programme (€143m in 2025) rolling off |
| NWC (% sales) | 42.6% | Actual Dec-25 operating WC €1,299m — ageing inventory is structural in spirits |
| WACC | 5.5% | rf 3.01% (Bund), Blume-adjusted beta 0.62, ERP 5.5%, 23% debt |
| Terminal g / exit multiple | 2.0% / 11.5x | ≤ nominal GDP / around peer median |

## 3. Results

| Method | Implied price | vs €5.49 |
|---|---|---|
| DCF — Gordon growth | €9.75 | +78% |
| DCF — exit multiple (11.5x) | €6.79 | +24% |
| Trading comps — median (11.7x) | €6.00 | +9% |
| Trading comps — range (9.4x–14.2x) | €4.54 – €7.64 | — |
| Sensitivity centre (WACC 6.5%, g 2.0%) | €7.29 | +33% |

**The Gordon number should not be taken at face value.** With WACC at 5.5% and g at 2.0%, the
spread is only 3.5pp and terminal value is 85% of enterprise value — the estimate is extremely
sensitive to two unobservable parameters (each ±0.5pp on WACC moves the price by roughly ±€1.5,
see the sensitivity grid). The exit-multiple DCF (€6.79) and the comps (€6.00 at median) are
the more defensible anchors, and they bracket the sell-side consensus target of €6.93.

## 4. View

Triangulating on the exit-multiple DCF and comps, fair value sits around **€6.50–7.00**,
roughly 20–25% above the current price. The market appears to be pricing the current spirits
downturn as semi-permanent; the balance sheet deleveraging (2.5x and falling), the margin
programme and the resilience of the aperitif portfolio argue against that. The main ways this
view is wrong: a prolonged US tariff escalation, a structural (not cyclical) decline in
spirits consumption among younger consumers, and the working-capital intensity limiting FCF
conversion if growth re-accelerates.

## 5. Limitations

Forecasts rest on management guidance and my own judgement, not proprietary information. The
WACC uses a Blume-adjusted regression beta (raw 0.43 → 0.62); a peer-average unlevered beta
would be a useful cross-check. Comps are point-in-time and the peer set trades on depressed
earnings (Pernod at 9.4x vs its ~13x history), which mechanically deflates the median. No
sum-of-the-parts or brand-level analysis was attempted. All market data as of early July 2026
and should be refreshed before any use.

## 6. Live validation findings

The `campari_valuation` Python package (`src/campari_valuation/`) independently re-derives the
two model inputs a live market data source can actually confirm or refute: beta and peer
trading multiples. Two findings from that exercise are worth stating explicitly, because they
are genuine discoveries about data and methodology, not restatements of the Excel's own numbers.

**Beta depends heavily on both benchmark choice and lookback window - neither alone tells the
full story.** At a fixed 2-year weekly-return window, four candidate European indices produced
raw betas from 0.49 (FTSE MIB, Campari's home listing) to 0.85 (STOXX Europe 600, a broad
pan-European benchmark) - a >70% range from benchmark choice alone. Varying the lookback from
1 to 5 years within each benchmark separately shows window length matters too, and differently
for each: FTSE MIB rises from 0.32 (1Y) to 0.49 (2Y) to 0.60 (5Y), while STOXX 600 is higher
and flatter across the same windows (0.64 / 0.84 / 0.85). The Excel's vendor-sourced raw beta
of 0.43 sits closest to the home-market benchmark at short-to-medium windows - consistent with
(though not proof of) the vendor having used FTSE MIB rather than a pan-European index.
Practically: **stating a stock's beta without stating the benchmark and window it was
regressed over is an incomplete claim**, and this is easy to miss when consuming a single
vendor-reported number rather than re-deriving it.

**A real data-quality issue, not a bug, explains most of the Diageo comp's divergence.** Live
EV/EBITDA for three of the four peers (Pernod Ricard, Rémy Cointreau, Brown-Forman) lands
within roughly 4% of the Excel's Comps tab. Diageo is the outlier (9.4x live vs. 11.25x in the
Excel). Investigating why surfaced that Yahoo Finance's quote-summary endpoint returns Diageo's
share price in pence (currency code `GBp`) while separately labeling its reported financials
`financialCurrency: USD` - yet its `marketCap` and `enterpriseValue` fields are nonetheless
GBP-scale, not USD-scale. That is an internally inconsistent set of fields from a single API
response for a single security, not a currency conversion this package could safely apply
without risking making the number worse. The package detects this
(`CompanySnapshot.currency_mismatch`) and flags the affected ticker in its output rather than
silently trusting the inconsistent data or guessing at a correction. This is the kind of
data-quality trap that is invisible unless you specifically cross-check a live provider's
internal field consistency -
exactly the discipline this project's live-validation layer exists to apply.
