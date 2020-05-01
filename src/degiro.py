import csv
import datetime
from pathlib import Path
from typing import Dict, Tuple, List

import numpy as np

from . import market


# Header of the Account.csv file from DeGiro export
CSV_HEADER = "Datum,Tijd,Valutadatum,Product,ISIN,Omschrijving,FX,Mutatie,,Saldo,,Order Id"

# If any of these words are found in a shares name, it is considered to be an ETF
# TODO: Find a more sophisticated way to find out
SUBSTRINGS_IN_ETF = ["Vanguard", "IShares"]


def read_account(account_csv: Path) -> Tuple[List[List[str]], datetime.date]:
    """Opens a DeGiro 'Account.csv' file and returns the contents as well as the first date"""
    csv_data = list(csv.reader(account_csv.open()))
    if csv_data[0] != CSV_HEADER.split(","):
        raise RuntimeError(f"Error while parsing '{account_csv}' file, unexpected header"
                           f"\nFound: {csv_data[0]}\nExpected: {CSV_HEADER.split(',')}")
    first_date = datetime.datetime.strptime(csv_data[-1][0], "%d-%m-%Y").date()
    return csv_data, first_date


def parse_account(csv_data: List[List[str]], dates: List[datetime.date]
                  ) -> Tuple[Dict[str, np.ndarray], Dict[str, np.ndarray]]:

    # Initial values
    num_days = len(dates)
    invested = np.zeros(shape=num_days)
    cash = np.zeros(shape=num_days)
    shares_value = np.zeros(shape=num_days)
    bank_cash = 0

    # Parse the CSV data
    done_parsing = False
    date_index = 0
    for row in csv_data[1:][::-1]:
        date = row[0]
        if date == "":
            continue
        row_date = datetime.datetime.strptime(date, "%d-%m-%Y").date()
        while row_date != dates[date_index]:
            date_index += 1
            if date_index == num_days:
                done_parsing = True
                break
        if done_parsing:
            break

        _, _, _, name, isin, description, _, currency, mutation, _, _, _ = row
        mutation = float(mutation.replace(",", ".")) if mutation != '' else 0
        currency_modifier = market.to_euro_modifier(currency, tuple(dates))[date_index] if currency not in ("", "EUR") else 1

        if description in ("iDEAL storting",):
            if bank_cash > mutation:
                bank_cash -= mutation
            else:
                invested[date_index:] += (mutation - bank_cash)
                cash[date_index:] += (mutation - bank_cash)
                bank_cash = 0

        elif description in ("Terugstorting",):
            bank_cash -= mutation

        elif description.split(" ")[0] in ("Koop", "Verkoop"):
            buy_or_sell = "sell" if description.split(" ")[0] == "Verkoop" else "buy"
            multiplier = -1 if buy_or_sell == "sell" else 1
            num_shares = int(description.split(" ")[1])
            is_etf = any([etf_subname.lower() in name.lower() for etf_subname in SUBSTRINGS_IN_ETF])
            this_share_value = market.get_data_by_isin(isin, tuple(dates), is_etf=is_etf)
            if this_share_value is None:  # no historical prices available for this stock/etf
                this_share_value = np.zeros(shape=num_days) + (-mutation / num_shares)
            this_share_value_eur = this_share_value[date_index] * currency_modifier
            print(f"[DGPC] {date}: {buy_or_sell:4s} {num_shares:4d} @ {this_share_value_eur:8.2f} EUR of {name}")

            shares_value[date_index:] += multiplier * num_shares * this_share_value[date_index:]
            cash[date_index:] += mutation * currency_modifier

        elif description == "Contante Verrekening Aandelen":
            cash[date_index:] += mutation
            print(f"[DGPC] {date}: special sell for {mutation} EUR")

        elif description == "DEGIRO transactiekosten":
            cash[date_index:] += mutation

        elif description == "Dividend":
            cash[date_index:] += mutation * currency_modifier

    # Set the absolute value metrics
    total_account = shares_value + cash
    absolutes = {"invested": invested, "cash": cash, "total account": total_account}

    # Set the relative metrics
    performance = np.divide(total_account, invested, out=np.zeros_like(invested), where=invested != 0)
    relatives = {"account performance":  performance}
    return absolutes, relatives
