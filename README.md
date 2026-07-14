# Campari Group (BIT: CPR) — DCF & Trading Comparables Valuation

A full equity valuation of Davide Campari-Milano N.V., built in Excel with live formulas:
5-year FCFF forecast, WACC built from scratch, dual terminal value (Gordon growth and exit
EV/EBITDA), WACC × g sensitivity grid, trading comparables (Diageo, Pernod Ricard,
Rémy Cointreau, Brown-Forman) and a football-field summary.

*Author: Maria Sfondrini — Master in Finance, Peking University HSBC Business School;
B.Sc. Computer System Engineering, Politecnico di Milano.*

## Files

- `Campari_DCF_Model.xlsx` — the model. Blue cells = inputs, black = formulas.
  Tabs: README, Assumptions, DCF Model, Comps, Football Field.
- `RESEARCH_NOTE.md` — 2-page write-up: method, results, view, and honest limitations.

## Headline results (market data as of early July 2026)

| Method | Implied price | vs €5.49 |
|---|---|---|
| DCF — Gordon growth | €9.75 | +78% |
| DCF — exit multiple (11.5x) | €6.79 | +24% |
| Trading comps — median (11.7x) | €6.00 | +9% |

Fair value triangulated at **€6.50–7.00**. The Gordon estimate is deliberately not the
headline: with terminal value at 85% of EV and a 3.5pp WACC−g spread, it is hypersensitive
to unobservable inputs — the note discusses why the multiple-based anchors are more
defensible.

## Data sources

FY2025 results and balance sheet: Campari Group FY2025 press release (March 2026).
Market data and peer multiples: stockanalysis.com (July 2026). Risk-free: 10Y Bund
(TradingEconomics). All public information; academic project, not investment advice.
