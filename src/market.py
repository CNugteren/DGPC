import datetime
import functools
from typing import Tuple, Optional

import investpy
import numpy as np


# Countries to consider in order of preference for etf/stock information
PREFERRED_COUNTRIES = ["netherlands", "united states", "united kingdom"]


def densify_history(history, dates: Tuple[datetime.date]) -> np.ndarray:
    """Expand the history data to include every date in the 'dates' array"""
    values = np.zeros(shape=len(dates))
    date_index = 0
    for value, date in zip(history["Close"], history["Date"]):
        while date != dates[date_index]:
            values[date_index] = value
            date_index += 1
            if date_index == len(dates):
                return values
        values[date_index] = value
    return values


@functools.lru_cache()
def to_euro_modifier(currency: str, dates: Tuple[datetime.date]) -> np.ndarray:
    from_date = dates[0].strftime("%d/%m/%Y")
    to_date = (dates[-1] + datetime.timedelta(days=7)).strftime("%d/%m/%Y")
    history = investpy.get_currency_cross_historical_data(currency_cross=f"EUR/{currency}",
                                                          from_date=from_date, to_date=to_date)
    history = history.reset_index()
    values = densify_history(history, dates)
    return 1 / values


@functools.lru_cache()
def get_data_by_isin(isin: str, dates: Tuple[datetime.date], is_etf: bool) -> Optional[np.ndarray]:
    from_date = dates[0].strftime("%d/%m/%Y")
    to_date = (dates[-1] + datetime.timedelta(days=7)).strftime("%d/%m/%Y")

    # Retrieves stock/etf information based on the ISIN
    try:
        if is_etf:
            data = investpy.search_etfs(by="isin", value=isin)
        else:
            data = investpy.search_stocks(by="isin", value=isin)
    except RuntimeError:
        return None

    for country in PREFERRED_COUNTRIES:
        local_data = data[data["country"] == country]
        if local_data.shape[0] > 0:
            break
    else:
        country = data["country"][0]  # taking the first country
        local_data = data

    # Retrieves the history for the stock/etf
    currency = list(local_data["currency"])[0]
    if is_etf:
        name = list(local_data["name"])[0]
        history = investpy.get_etf_historical_data(name, country=country, from_date=from_date, to_date=to_date)
    else:
        symbol = list(local_data["symbol"])[0]
        history = investpy.get_stock_historical_data(symbol, country=country, from_date=from_date, to_date=to_date)
    history = history.reset_index()

    values = densify_history(history, dates)

    # Convert to euro
    if currency != "EUR":
        currency_modifier = to_euro_modifier(currency, tuple(dates))
        values *= currency_modifier

    return values
