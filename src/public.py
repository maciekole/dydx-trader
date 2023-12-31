import time

import numpy as np
import pandas as pd

from constants import RESOLUTION
from utils import get_iso_times_ranges

# Get relevant time periods for ISO
ISO_TIMES = {}


# Get candles historical
def get_candles_historical(client, market, limit=100):
    print(f"get_candles_historical(market={market})")
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
def construct_market_prices(client, limit=None) -> pd.DataFrame:
    print("construct_market_prices()")
    tradeable_markets = []
    markets = client.public.get_markets()

    # Find tradeable pairs
    for market in markets.data["markets"].keys():
        market_info = markets.data["markets"][market]
        if (
            market_info["status"] == "ONLINE"
            and market_info["type"] == "PERPETUAL"
        ):
            tradeable_markets.append(market)

    # Set initial DataFrame
    close_prices = get_candles_historical(client, tradeable_markets[0])
    df = pd.DataFrame(close_prices)
    df.set_index("datetime", inplace=True)

    left_tradeable_markets = tradeable_markets[1:]
    if limit is not None and limit >= 2:
        if limit <= len(tradeable_markets):
            left_tradeable_markets = tradeable_markets[1:limit]

    print(f"left_tradeable_markets: {len(left_tradeable_markets)}")
    # Append other prices
    for market in left_tradeable_markets:
        close_prices_add = get_candles_historical(client, market)
        df_add = pd.DataFrame(close_prices_add)
        df_add.set_index("datetime", inplace=True)
        df = pd.merge(df, df_add, how="outer", on="datetime", copy=False)
        del df_add  # clear some memory

    # Check any columns with NaNs
    nans = df.columns[df.isna().any()].tolist()
    if len(nans) > 0:
        print(f"Drop NaNs columns: {nans}")
        df.drop(nans, inplace=True)
    return df


# Get candles recent
def get_candles_recent(client, market):
    close_prices = []

    time.sleep(0.25)  # Protect API

    candles = client.public.get_candles(
        market=market, resolution=RESOLUTION, limit=100
    )

    for candle in candles.data["candles"]:
        close_prices.append(candle["close"])

    close_prices.reverse()
    prices_result = np.array(close_prices).astype(float)
    return prices_result
