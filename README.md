# DGPC: DeGiro Performance Charts

DGPC is a small and simple utility that parses CSV-exports from [DeGiro](degiro.nl) and creates portfolio performance charts, such as the following:

<TODO: Insert image>

DGPC is not meant for professional usage and makes many assumptions, can't parse all CSV data (yet), and probably also makes a few mistakes and simplifications here and there. So use it at own risk, feel free to make a pull request to improve the tool.

Stock, ETF, and currency data is queried using the `investpy` package, based on data from [Investing.com](investing.com).

## Requirements

For running the tool itself:
* Python 3.7 or newer
* Several Python packages, run `pip3 -r requirements.txt` to install

For running the tests and linters, you also need `pytest`, `mypy`, and `pylint`.

## Usage

First you'll need to get an `Account.csv` file:
* Log in to your DeGiro account
* Go to `Overzichten` -> `Rekeningoverzicht`
* Select the **full** date range and select `Export`

Now you can run the tool as follows:

    python3 dgpc.py --input_file /path/to/Account.csv

It will output the graph as `dgpc.png` in your current folder. For more options and configurations, run:

    python3 dgpc.py --help
