"""
Tests for the stock/etf/currency market queries.
"""
import datetime

import numpy as np

import src.market as market


def test_etf_history() -> None:
    """Tests querying historical ETF information using investpy, based on two open market days followed by 3 market
    closing days afterwards ('dag van de arbeid' and Saturday)."""
    dates = [datetime.date(2020, 4, 28) + datetime.timedelta(days=days) for days in range(0, 5)]
    print(dates)
    market_info, etf_name = market.get_data_by_isin(isin="IE00B4L5Y983", dates=tuple(dates), is_etf=True)
    assert etf_name == "iShares Core MSCI World UCITS"
    np.testing.assert_allclose(market_info, [50.58, 51.55, 50.51, 50.51, 50.51])
