"""Regression beta and the Blume adjustment, reproducing the Excel model's
own methodology (Campari_DCF_Model.xlsx, Assumptions!D15) so the live
cross-check is apples-to-apples rather than a differently-defined number
that merely happens to look similar.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def regression_beta(asset_returns: pd.Series, market_returns: pd.Series) -> float:
    """OLS beta of asset returns on market returns: Cov(asset, market) / Var(market)."""
    aligned = pd.concat([asset_returns, market_returns], axis=1, join="inner").dropna()
    if len(aligned) < 10:
        raise ValueError("at least 10 overlapping return observations are required")
    asset, market = aligned.iloc[:, 0], aligned.iloc[:, 1]
    market_variance = float(np.var(market, ddof=1))
    if market_variance == 0.0:
        raise ValueError("market returns have zero variance; cannot regress")
    covariance = float(np.cov(asset, market, ddof=1)[0, 1])
    return covariance / market_variance


def blume_adjust(raw_beta: float) -> float:
    """Blume (1975) mean-reversion adjustment toward 1.0, using the exact
    0.67/0.33 weights from the Excel model's Assumptions tab (`=0.67*C15+0.33`),
    not the textbook-generic 2/3-1/3 - they round to the same two-decimal
    result here, but matching the model's own literal formula is the point.
    """
    return 0.67 * raw_beta + 0.33
