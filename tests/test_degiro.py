"""
Tests for the DeGiro parsing of various kinds, based on modified snippets of real account data.
"""
import csv
import datetime

import numpy as np

import src.degiro as degiro


def test_parse_cash_addition() -> None:
    """Tests adding cash to the account."""
    csv_data = list(csv.reader([
        degiro.CSV_HEADER,
        '12-03-2020,15:45,12-03-2020,,,iDEAL storting,,EUR,"1000,00",EUR,"1046,57",',
        '10-03-2020,10:09,10-03-2020,,,iDEAL storting,,EUR,"500,00",EUR,"1461,52",'
    ]))
    dates = [datetime.date(2020, 3, 9) + datetime.timedelta(days=days) for days in range(0, 4)]

    absolute_data, _ = degiro.parse_account(csv_data, dates)
    np.testing.assert_equal(absolute_data["invested"], absolute_data["cash"])
    np.testing.assert_equal(absolute_data["invested"], [0, 500, 500, 1500])


def test_parse_buy_and_sell() -> None:
    """Tests buying a stock and selling it again in USD."""
    csv_data = list(csv.reader([
        # pylint: disable=line-too-long
        degiro.CSV_HEADER,
        '13-07-2017,18:52,13-07-2017,ADVANCED MICRO DEVICES,US0079031078,"Verkoop 8 @ 32,75 USD",,USD,"262,00",USD,"262,00",7fdd089d-e15e-2fa9-a142-bfbg43e42ff1',
        '11-07-2017,20:19,11-07-2017,ADVANCED MICRO DEVICES,US0079031078,"Koop 8 @ 13,93 USD",,USD,"-111,44",USD,"-111,44",2gfad09a-a935-4b2c-a51a-132egc2bf0ed',
        '11-07-2017,10:09,11-07-2017,,,iDEAL storting,,EUR,"500,00",EUR,"1461,52",'
    ]))
    dates = [datetime.date(2017, 7, 10) + datetime.timedelta(days=days) for days in range(0, 5)]

    absolute_data, _ = degiro.parse_account(csv_data, dates)
    np.testing.assert_allclose(absolute_data["invested"], [0, 500, 500, 500, 500])
    np.testing.assert_allclose(absolute_data["cash"], [0, 402.816779, 402.816779, 632.661502, 632.661502])
    np.testing.assert_allclose(absolute_data["total account"], [0, 499.720938, 502.992033, 632.661502, 632.661502])


def test_parse_transaction_costs() -> None:
    """Tests paying for two sets of transaction costs."""
    csv_data = list(csv.reader([
        # pylint: disable=line-too-long
        degiro.CSV_HEADER,
        '12-07-2017,09:05,12-07-2017,ISHARES EMIM,IE00BKM4GZ66,DEGIRO transactiekosten,,EUR,"-2,00",EUR,"296,97",17e55f46-efaa-4edf-a76e-209e820223f7',
        '12-07-2017,09:05,12-07-2017,ISHARES EMIM,IE00BKM4GZ66,DEGIRO transactiekosten,,EUR,"-0,62",EUR,"298,97",17e55f46-efaa-4edf-a76e-209e820223f7',
        '11-07-2017,10:09,11-07-2017,,,iDEAL storting,,EUR,"500,00",EUR,"1461,52",'
    ]))
    dates = [datetime.date(2017, 7, 10) + datetime.timedelta(days=days) for days in range(0, 3)]

    absolute_data, _ = degiro.parse_account(csv_data, dates)
    np.testing.assert_allclose(absolute_data["invested"], [0, 500, 500])
    np.testing.assert_allclose(absolute_data["cash"], [0, 500, 497.38])
    np.testing.assert_allclose(absolute_data["total account"], [0, 500, 497.38])
