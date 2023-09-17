import time

from constants import RESOLUTION
from utils import get_iso_times_ranges

# from pprint import pprint
#
# import numpy as np
# import pandas as pd


# Get relevant time periods for ISO
ISO_TIMES = {}


# Get candles historical
def get_candles_historical(client, market, limit=100):
    print("get_candles_historical()")  # @todo debug
    iso_times = [t_range for t_range in get_iso_times_ranges()]
    close_prices = []

    for timeframe in iso_times:
        # Confirm times needed
        from_iso = timeframe["from_iso"]
        to_iso = timeframe["to_iso"]

        time.sleep(0.25)  # Protect API

        # Get data
        candles = client.public.get_candles(
            market=market,
            resolution=RESOLUTION,
            from_iso=from_iso,
            to_iso=to_iso,
            limit=limit,
        )

        # Structure data
        for candle in candles.data["candles"]:
            close_prices.append(
                {
                    "datetime": candle["startedAt"],
                    market: candle["close"],
                }
            )

    # Construct and return DF
    close_prices.reverse()
    return close_prices


# Construct market prices
def construct_market_prices(client):
    print("construct_market_prices()")  # @todo debug
    historical_candles = get_candles_historical(client, "BTC-USD")
    print(f"historical_candles: {historical_candles}")
