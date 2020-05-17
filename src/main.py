"""Main DGPC (DeGiro Performance Charts) entry point with argument parser and main function."""
import argparse
import datetime
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

from . import degiro
from . import market
from . import plot


def parse_date(date_string: str) -> datetime.date:
    """Helper to parse a datetime.date from the command line."""
    try:
        return datetime.datetime.strptime(date_string, "%d-%m-%Y").date()
    except ValueError:
        raise argparse.ArgumentTypeError(f"Not a valid date: '{date_string}'")


def parse_arguments() -> Any:
    """Sets the command-line arguments."""
    parser = argparse.ArgumentParser(description="DGPC: DeGiro Performance Chart tool",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i", "--input_file", required=True, help="Location of DeGiro account CSV file", type=Path)
    parser.add_argument("-p", "--output_png", default="dgpc.png", help="Path for output PNG image", type=Path)
    parser.add_argument("-c", "--output_csv", default="dgpc.csv", help="Path for output CSV file", type=Path)
    parser.add_argument("-e", "--end_date", help="End date for plotting, as DD-MM-YYYY", type=parse_date,
                        default=datetime.datetime.now().date())
    parser.add_argument("-s", "--start_date", help="Start date for plotting, as DD-MM-YYYY", type=parse_date,
                        default=datetime.date(2000, 1, 1))
    parser.add_argument("-r", "--reference_isin", default="IE00B4L5Y983", type=str,
                        help="ISIN to plot as reference, by default this is set to IWDA")
    parser.add_argument("-y", "--png_height_pixels", default=1080, type=int,
                        help="Height of image in pixels, width is determined with the standard 16:9 aspect ratio")
    parser.add_argument("--plot_hide_eur_values", action="store_true",
                        help="Hides absolute EUR values in the plot, e.g. for privacy reasons")
    return vars(parser.parse_args())


def compute_reference_invested(reference: np.ndarray, invested: np.ndarray) -> np.ndarray:
    """Given some amount of cash investment over time, compute the reference stock/ETF's value given that all the
    invested cash was used to buy the reference stock/ETF at the time when it was available. Assumes partial shares
    exist."""
    result = np.zeros(shape=reference.shape)
    num_shares = invested[0] / reference[0]
    result += num_shares * reference
    for date_index, investment in enumerate(np.diff(invested)):
        if investment != 0:
            num_shares = investment / reference[date_index + 1]
            result[date_index + 1:] += num_shares * reference[date_index + 1:]
    return result


def store_csv(dates: List[datetime.date], absolute_data: Dict[str, np.ndarray],
              relative_data: Dict[str, np.ndarray], output_file: Path) -> None:
    """Stores all the collected data as a simple CSV file."""
    absolutes = list(absolute_data.keys())
    relatives = list(relative_data.keys())
    with output_file.open("w") as file:
        file.write(",".join(["date", *absolutes, *relatives]).replace(" ", "_") + "\n")
        for date_index, date in enumerate(dates):
            absolute_vals = [str(round(absolute_data[name][date_index], 2)) for name in absolutes]
            relative_vals = [str(round(absolute_data[name][date_index], 2)) for name in absolutes]
            file.write(",".join([str(date), *absolute_vals, *relative_vals]).replace(" ", "_") + "\n")


def dgpc(input_file: Path, output_png: Path, output_csv: Path, end_date: datetime.date, start_date: datetime.date,
         reference_isin: str, png_height_pixels: int, plot_hide_eur_values: bool) -> None:
    """Main entry point of DGPC after parsing the command-line arguments. This function is the main script, calling all
    other functions. The input file needs to point to an 'Account.csv' file from DeGiro, whereas the output file paths
    are the locations of the resulting chart as PNG file and full data CSV. Furthermore, the reference ISIN can be set.
    """
    # pylint: disable=too-many-arguments,too-many-locals

    # Preliminaries: read the CSV file and set the date range structure
    print(f"[DGPC] Reading DeGiro data from '{input_file}'")
    csv_data, first_date = degiro.read_account(input_file)

    num_days = (end_date - first_date).days
    dates = [first_date + datetime.timedelta(days=days) for days in range(0, num_days)]

    # Parse the DeGiro account data
    print(f"[DGPC] Parsing DeGiro data with {len(csv_data)} rows from {dates[0]} till {dates[-1]}")
    absolute_data, relative_data = degiro.parse_account(csv_data, dates)

    # Filter out all values before the chosen 'start_date' (default: today)
    if start_date in dates:
        print(f"[DGPC] Filtering out all data from before {start_date}")
        first_index = dates.index(start_date)
        dates = dates[first_index:]
        for name, values in absolute_data.items():
            absolute_data[name] = values[first_index:]
        # Relative data is recalculated to start at 0% performance at the given start date
        invested = absolute_data["nominal account (without profit/loss)"]
        invested_restart = invested + absolute_data["total account value"][0] - invested[0]
        relative_data["account performance"] = absolute_data["total account value"] / invested_restart

    # Add reference data to compare the graph with
    print(f"[DGPC] Retrieving reference data for {reference_isin}")
    reference, reference_name = market.get_data_by_isin(reference_isin, tuple(dates), is_etf=True)
    if reference is None:
        print(f"[DGPC] Could not find data for reference {reference_isin}: {reference_name}, skipping")
    else:
        invested = absolute_data["nominal account (without profit/loss)"]
        reference_invested = compute_reference_invested(reference, invested)
        absolute_data[f"{reference_name}: given investment"] = reference_invested
        relative_data[f"{reference_name}: all-in day one"] = reference / reference[0]
        relative_data[f"{reference_name}: given investment"] = reference_invested / invested

    # Plotting the final results
    print(f"[DGPC] Plotting results as image '{output_png}'")
    plot.plot(dates, absolute_data, relative_data, output_png, plot_size_y=png_height_pixels,
              hide_eur_values=plot_hide_eur_values)

    # Storing data also as CSV for reference
    print(f"[DGPC] Storing results also as CSV '{output_csv}'")
    store_csv(dates, absolute_data, relative_data, output_csv)


def main() -> None:
    """Main entry point of DGPC from the command-line."""
    dgpc(**parse_arguments())
