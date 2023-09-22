import json

import pandas as pd

from agents.bot_agent import BotAgent
from cointegration import calculate_zscore
from constants import (
    AGENTS_DATA_PATH,
    COINTEGRATED_DATA_PATH,
    USD_MIN_COLLATERAL,
    USD_PER_TRADE,
    ZSCORE_THRESHOLD,
)
from positions import is_open_positions
from public import get_candles_recent
from utils import format_number


# Open positions
def open_positions(client):
    """
    Manage finding triggers for trade entry
    Store trades for managing later on exit function
    :param client:
    :return:
    """
    df = pd.read_csv(f"../{COINTEGRATED_DATA_PATH}")

    # print(f"open_positions df:\n{df}")

    # Get market from referencing of min order size, tick size, etc
    markets = client.public.get_markets().data

    bot_agents = []

    print(f"open_positions for {len(df.index)} market pairs")
    print("++++++++++++++++++++++++++++++++++++++++++++++++")

    # Find ZScore triggers
    for index, row in df.iterrows():
        base_market = row["base_market"]
        quote_market = row["quote_market"]
        hedge_ratio = row["hedge_ratio"]
        half_life = row["half_life"]

        print(
            f"base_market - {base_market} [VS] {quote_market} - quote_market"
        )

        # Get prices
        series_1 = get_candles_recent(client, base_market)
        series_2 = get_candles_recent(client, quote_market)

        # Get ZScore
        if len(series_1) > 0 and len(series_1) == len(series_2):
            spread = series_1 - (hedge_ratio * series_2)
            z_score = calculate_zscore(spread).values.tolist()[-1]

            # Establish if potential trade
            if abs(z_score) >= ZSCORE_THRESHOLD:
                # Ensure like-for-like not already open
                is_base_open = is_open_positions(client, base_market)
                is_quote_open = is_open_positions(client, quote_market)

                # Place trade
                if not is_base_open and not is_quote_open:
                    # Determine the side
                    base_side = "BUY" if z_score < 0 else "SELL"
                    quote_side = "BUY" if z_score > 0 else "SELL"

                    # Get acceptable price in string format
                    base_price = series_1[-1]
                    quote_price = series_2[-1]
                    accept_base_price = (
                        float(base_price) * 1.01
                        if z_score < 0
                        else float(base_side) * 0.99
                    )
                    accept_quote_price = (
                        float(quote_price) * 1.01
                        if z_score > 0
                        else float(quote_price) * 0.99
                    )
                    failsafe_base_price = (
                        float(base_price) * 0.05
                        if z_score < 0
                        else float(base_price) * 1.7
                    )
                    base_tick_size = markets["markets"][base_market][
                        "tickSize"
                    ]
                    quote_tick_size = markets["markets"][quote_market][
                        "tickSize"
                    ]

                    # Format prices
                    accept_base_price = format_number(
                        accept_base_price, base_tick_size
                    )
                    accept_quote_price = format_number(
                        accept_quote_price, quote_tick_size
                    )
                    # accept_failsafe_base_price
                    accept_fs_base_price = format_number(
                        failsafe_base_price, base_tick_size
                    )

                    # Get size
                    base_qty = 1 / base_price * USD_PER_TRADE
                    quote_qty = 1 / quote_price * USD_PER_TRADE
                    base_step_size = markets["markets"][base_market][
                        "stepSize"
                    ]
                    quote_step_size = markets["markets"][quote_market][
                        "stepSize"
                    ]

                    # Format sizes
                    base_size = format_number(base_qty, base_step_size)
                    quote_size = format_number(quote_qty, quote_step_size)

                    # Ensure size
                    base_min_order_size = markets["markets"][base_market][
                        "minOrderSize"
                    ]
                    quote_min_order_size = markets["markets"][quote_market][
                        "minOrderSize"
                    ]
                    base_max_position_size = markets["markets"][base_market][
                        "maxPositionSize"
                    ]
                    quote_max_position_size = markets["markets"][quote_market][
                        "maxPositionSize"
                    ]
                    check_base = (
                        float(base_max_position_size)
                        >= float(base_qty)
                        > float(base_min_order_size)
                    )
                    check_quote = (
                        float(quote_max_position_size)
                        >= float(quote_qty)
                        > float(quote_min_order_size)
                    )

                    if check_base and check_quote:
                        # Place order
                        account = client.private.get_account()
                        free_collateral = float(
                            account.data["account"]["freeCollateral"]
                        )
                        print("$$$")
                        print(f"[BALANCE] Available {free_collateral}")
                        print(f"[BALANCE] Minimum  {USD_MIN_COLLATERAL}")
                        print("$$$")

                        # Ensure collateral
                        if free_collateral < USD_MIN_COLLATERAL:
                            break

                        # Create Bot Agent
                        print(
                            f"base_market: {base_market}, "
                            f"base_side: {base_side}, "
                            f"base_size: {base_size}, "
                            f"accept_base_price: {accept_base_price}"
                        )
                        print(
                            f"quote_market: {quote_market}, "
                            f"quote_side: {quote_side}, "
                            f"quote_size: {quote_size}, "
                            f"accept_quote_price: {accept_quote_price}"
                        )
                        bot_agent = BotAgent(
                            client=client,
                            market_1=base_market,
                            market_2=quote_market,
                            base_side=base_side,
                            base_size=base_size,
                            base_price=accept_base_price,
                            quote_side=quote_side,
                            quote_size=quote_size,
                            quote_price=accept_quote_price,
                            accept_failsafe_base_price=accept_fs_base_price,
                            z_score=z_score,
                            half_life=half_life,
                            hedge_ratio=hedge_ratio,
                        )

                        # Open trades
                        bot_open_dict = bot_agent.open_trades()

                        if bot_open_dict["pair_status"] == "LIVE":
                            bot_agents.append(bot_open_dict)
                            del bot_open_dict

                        # Confirm live status
                        print("Trade status: Live")
                        print("######")

    # Save agents
    print(f"Success: {len(bot_agents)} New Pairs.")
    if len(bot_agents) > 0:
        with open(AGENTS_DATA_PATH, "w") as f:
            json.dump(bot_agents, f)
