import argparse
import datetime
from pathlib import Path
from typing import Any

import numpy as np

from . import degiro
from . import market
from . import plot


def parse_arguments() -> Any:
    """Sets the command-line arguments"""
    parser = argparse.ArgumentParser(description="DGPC: DeGiro Performance Chart tool")
    parser.add_argument("-i", "--input_file", required=True, help="Location of DeGiro account CSV file", type=Path)
    parser.add_argument("-o", "--output_file", default="dgpc.png", help="Path for output image", type=Path)
    return vars(parser.parse_args())


def compute_reference_invested(reference, invested) -> np.ndarray:
    result = np.zeros(shape=reference.shape)
    num_shares = invested[0] / reference[0]
    result += num_shares * reference
    for date_index, investment in enumerate(np.diff(invested)):
        if investment != 0:
            num_shares = investment / reference[date_index + 1]
            result[date_index + 1:] += num_shares * reference[date_index + 1:]
    return result


def dgpc(input_file: Path, output_file: Path) -> None:
    csv_data, first_date = degiro.read_account(input_file)
    num_days = (datetime.datetime.now().date() - first_date).days
    dates = [first_date + datetime.timedelta(days=days) for days in range(0, num_days)]

    absolute_data, relative_data = degiro.parse_account(csv_data, dates)
    invested = absolute_data["invested"]

    iwda = market.get_data_by_isin("IE00B4L5Y983", tuple(dates), is_etf=True)
    iwda_invested = compute_reference_invested(iwda, invested)

    absolute_data["IWDA given investment"] = iwda_invested
    relative_data["IWDA all-in day one"] = iwda / iwda[0]
    relative_data["IWDA given investment"] = iwda_invested / invested

    plot.plot(dates, absolute_data, relative_data, output_file)


def main() -> None:
    dgpc(**parse_arguments())
