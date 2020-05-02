"""
Functionality to query market data using the 'investpy' package, querying data from Investing.com.
"""
import datetime
import functools
from typing import Optional, Sequence, Tuple

import investpy
import numpy as np
from pandas import DataFrame


# Countries to consider in order of preference for etf/stock information
PREFERRED_COUNTRIES = ["netherlands", "united states", "united kingdom"]


def densify_history(history_df: DataFrame, dates: Sequence[datetime.date]) -> np.ndarray:
    """Expand the history data to include every date in the 'dates' array."""
    values = np.zeros(shape=len(dates))
    df_dates = list(history_df["Date"])
    df_close = list(history_df["Close"])
    previous_value = df_close[0]
    for date_index, date in enumerate(dates):
        if date in df_dates:
            df_index = df_dates.index(dates[date_index])
            value = df_close[df_index]
            previous_value = value
        else:
            value = previous_value
        values[date_index] = value
    return values


@functools.lru_cache()
def to_euro_modifier(currency: str, dates: Tuple[datetime.date]) -> np.ndarray:
    """Retrieves currency-to-EUR conversion for the given dates. Cached to make sure this is only queried once for
    a given currency & date-range."""
    from_date = dates[0].strftime("%d/%m/%Y")
    to_date = (dates[-1] + datetime.timedelta(days=7)).strftime("%d/%m/%Y")
    history = investpy.get_currency_cross_historical_data(currency_cross=f"EUR/{currency}",
                                                          from_date=from_date, to_date=to_date)
    history = history.reset_index()
    values = densify_history(history, dates)
    return 1 / values


@functools.lru_cache()
def get_data_by_isin(isin: str, dates: Tuple[datetime.date], is_etf: bool) -> Tuple[Optional[np.ndarray], str]:
    """Retrieves stock/ETF prices in EUR by ISIN for the given dates. Cached to make sure this is only queried once for
    a given currency & date-range."""
    from_date = dates[0].strftime("%d/%m/%Y")
    to_date = (dates[-1] + datetime.timedelta(days=7)).strftime("%d/%m/%Y")

    # Retrieves stock/etf information based on the ISIN
    try:
        if is_etf:
            data = investpy.search_etfs(by="isin", value=isin)
        else:
            data = investpy.search_stocks(by="isin", value=isin)
    except RuntimeError:
        print(f"[DGPC] Warning, could not retrieve {'ETF' if is_etf else 'stock'} data for ISIN {isin}.")
        return None, ""

    # When a stock/ETF is listed in multiple countries, take one of the preferred countries if found
    for country in PREFERRED_COUNTRIES:
        local_data = data[data["country"] == country]
        if local_data.shape[0] > 0:
            break
    else:
        # Taking the first country from the results if none of the preferred countries is found
        country = data["country"][0]
        local_data = data

    # Retrieves the actual historical prices for the stock/etf
    currency = list(local_data["currency"])[0]
    if is_etf:
        name = list(local_data["name"])[0]
        history = investpy.get_etf_historical_data(name, country=country, from_date=from_date, to_date=to_date)
    else:
        name = list(local_data["symbol"])[0]
        history = investpy.get_stock_historical_data(name, country=country, from_date=from_date, to_date=to_date)
    history = history.reset_index()
    values = densify_history(history, dates)

    # Convert the results to euro
    if currency != "EUR":
        currency_modifier = to_euro_modifier(currency, tuple(dates))
        values *= currency_modifier

    return values, name
