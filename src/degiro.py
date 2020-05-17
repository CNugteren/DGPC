"""Parsing functionality of a DeGiro 'Account.csv' file."""
import csv
import datetime
from pathlib import Path
from typing import Dict, Sequence, Tuple, List

import numpy as np

from . import market


# Header of the Account.csv file from DeGiro export
CSV_HEADER = "Datum,Tijd,Valutadatum,Product,ISIN,Omschrijving,FX,Mutatie,,Saldo,,Order Id"

# If any of these words (case agnostic) are found in a shares name, it is considered to be an ETF
SUBSTRINGS_IN_ETF = ["Amundi", "X-TR", "ETFS", "ISHARES", "LYXOR", "Vanguard", "WISDOMTR"]
# ... ano others, not complete of course


def read_account(account_csv: Path) -> Tuple[List[List[str]], datetime.date]:
    """Opens a DeGiro 'Account.csv' file and returns the contents as well as the first date"""
    csv_data = list(csv.reader(account_csv.open()))
    if csv_data[0] != CSV_HEADER.split(","):
        raise RuntimeError(f"Error while parsing '{account_csv}' file, unexpected header"
                           f"\nFound: {csv_data[0]}\nExpected: {CSV_HEADER.split(',')}")
    first_date = datetime.datetime.strptime(csv_data[-1][0], "%d-%m-%Y").date()
    return csv_data, first_date


def parse_single_row(row: List[str], dates: Sequence[datetime.date], date_index: int,
                     invested: np.ndarray, cash: np.ndarray, shares_value: np.ndarray, bank_cash: np.ndarray) -> None:
    """Parses a single row of the CSV data, updating all the NumPy arrays (they are both input and output)."""
    # pylint: disable=too-many-locals,too-many-arguments,too-many-statements,too-many-branches

    date, _, _, name, isin, description, _, currency, mutation_string, _, _, _ = row
    mutation = float(mutation_string.replace(",", ".")) if mutation_string != '' else 0.0
    currency_modifier = market.to_euro_modifier(currency, dates)[date_index] if currency not in ("", "EUR") else 1

    # ----- Cash in and out -----

    if description in ("iDEAL storting", "Storting"):
        if bank_cash[date_index] > mutation:
            bank_cash[date_index:] -= mutation
        else:
            invested[date_index:] += (mutation - bank_cash[date_index])
            cash[date_index:] += (mutation - bank_cash[date_index])
            bank_cash[date_index:] = 0

    elif description in ("Terugstorting",):
        bank_cash[date_index:] -= mutation

    # ----- Buying and selling -----

    elif description.split(" ")[0] in ("Koop", "Verkoop"):
        buy_or_sell = "sell" if description.split(" ")[0] == "Verkoop" else "buy"
        multiplier = -1 if buy_or_sell == "sell" else 1
        num_shares = int(description.split(" ")[1].replace(".", ""))
        is_etf = any([etf_subname.lower() in name.lower() for etf_subname in SUBSTRINGS_IN_ETF])
        this_share_value, _ = market.get_data_by_isin(isin, dates, is_etf=is_etf)
        if this_share_value is None:  # no historical prices available for this stock/etf
            this_share_value = np.zeros(shape=len(dates)) + (-mutation / num_shares)

        print(f"[DGPC] {date}: {buy_or_sell:4s} {num_shares:4d} @ {this_share_value[date_index]:8.2f} EUR of {name}")

        shares_value[date_index:] += multiplier * num_shares * this_share_value[date_index:]
        cash[date_index:] += mutation * currency_modifier

    elif description == "Contante Verrekening Aandelen":
        cash[date_index:] += mutation
        print(f"[DGPC] {date}: special sell for {mutation} EUR")

    # ----- DeGiro usage costs -----

    elif description == "DEGIRO transactiekosten":
        cash[date_index:] += mutation

    elif "DEGIRO Aansluitingskosten" in description:
        cash[date_index:] += mutation

    elif "Externe Kosten" in description:
        cash[date_index:] += mutation * currency_modifier

    elif "Stamp Duty" in description:
        cash[date_index:] += mutation * currency_modifier

    # ----- Dividend -----

    elif description == "Dividend":
        cash[date_index:] += mutation * currency_modifier

    elif "dividendbelasting" in description.lower():
        cash[date_index:] += mutation * currency_modifier

    # ----- Implications of cash on the DeGiro account -----

    elif "Koersverandering geldmarktfonds" in description:
        cash[date_index:] += mutation * currency_modifier

    elif description == "DEGIRO Geldmarktfondsen Compensatie":
        cash[date_index:] += mutation * currency_modifier

    elif description == "Fondsuitkering":
        cash[date_index:] += mutation * currency_modifier

    elif description == "Rente":
        cash[date_index:] += mutation * currency_modifier

    elif "Conversie geldmarktfonds" in description:
        pass  # Nothing to do?

    # ----- Others -----

    elif description in ("Valuta Creditering", "Valuta Debitering"):
        pass  # Nothing to do - already taken into account?

    else:
        print(f"[DGPC] {date}: Unsupported type of entry '{description}', contents:")
        print(row)


def parse_account(csv_data: List[List[str]], dates: List[datetime.date]) -> Tuple[Dict[str, np.ndarray],
                                                                                  Dict[str, np.ndarray]]:
    """Parses the csv-data and constructs NumPy arrays for the given date range with cash value, total account value,
    and total invested."""

    # Initial values
    num_days = len(dates)
    invested = np.zeros(shape=num_days)
    cash = np.zeros(shape=num_days)
    shares_value = np.zeros(shape=num_days)

    # We make the assumption that any money going out of the DeGiro account is still on a bank and thus counted here
    # as cash. This value holds the amount of money on the bank at a given time while parsing, with future cash
    # deposits reducing this value.
    bank_cash = np.zeros(shape=num_days)

    # Parse the CSV data
    date_index = 0
    stop_parsing = False
    for row in csv_data[1:][::-1]:

        # Retrieves the data of this CSV row
        if row[0] == "":
            continue
        date = datetime.datetime.strptime(row[0], "%d-%m-%Y").date()

        # Advance the date till we reach the date of the CSV entry
        while date != dates[date_index]:
            date_index += 1
            if date_index == num_days:
                print(f"[DGPC] Warning, CSV date {date} larger than dates range (up to {dates[-1]}), skipping data")
                stop_parsing = True
                break

        if stop_parsing:
            break

        parse_single_row(row, tuple(dates), date_index,
                         invested, cash, shares_value, bank_cash)

    # Set the absolute value metrics
    total_account = shares_value + cash
    absolutes = {"nominal account (without profit/loss)": invested,
                 "cash in DeGiro account": cash,
                 "total account value": total_account,
                 "profit/loss": total_account - invested}

    # Set the relative metrics
    performance = np.divide(total_account, invested, out=np.zeros_like(invested), where=invested != 0)

    relatives = {"account performance":  performance}
    return absolutes, relatives
