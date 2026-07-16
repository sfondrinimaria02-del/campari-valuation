import numpy as np
import pandas as pd
import pytest

from campari_valuation.beta import blume_adjust, regression_beta


def test_regression_beta_recovers_a_known_linear_relationship():
    rng = np.random.default_rng(0)
    market = pd.Series(rng.normal(0, 0.01, 500))
    true_beta = 1.5
    asset = true_beta * market  # noise-free: beta must recover exactly

    assert regression_beta(asset, market) == pytest.approx(true_beta, abs=1e-9)


def test_regression_beta_uses_only_the_overlapping_index_range():
    # market spans dates 0-19; asset spans dates 10-29. Only 10-19 overlaps.
    # Within that overlap asset = 2 * market exactly; outside it asset takes
    # unrelated values that would wreck the beta estimate if wrongly included.
    market = pd.Series(np.linspace(-0.05, 0.05, 20), index=range(0, 20))
    overlap_asset_values = 2.0 * market.loc[10:19]
    unrelated_values = pd.Series([-10.0] * 10, index=range(20, 30))
    asset = pd.concat([overlap_asset_values, unrelated_values])

    beta = regression_beta(asset, market)

    assert beta == pytest.approx(2.0, abs=1e-9)


def test_regression_beta_rejects_too_few_observations():
    with pytest.raises(ValueError, match="at least 10"):
        regression_beta(pd.Series([0.01, 0.02]), pd.Series([0.01, 0.02]))


def test_regression_beta_rejects_zero_variance_market():
    flat_market = pd.Series([0.0] * 15)
    asset = pd.Series(np.linspace(-0.05, 0.05, 15))
    with pytest.raises(ValueError, match="zero variance"):
        regression_beta(asset, flat_market)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (0.43, 0.67 * 0.43 + 0.33),
        (1.0, 1.0),  # a beta of exactly 1.0 is unaffected by mean-reversion toward 1.0
        (0.0, 0.33),
    ],
)
def test_blume_adjust_matches_the_excel_models_exact_formula(raw, expected):
    assert blume_adjust(raw) == pytest.approx(expected)
