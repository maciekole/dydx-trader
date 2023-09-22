import json
import time

from cointegration import calculate_zscore
from constants import AGENTS_DATA_PATH, CLOSE_AT_ZSCORE_CROSS
from positions import place_market_order
from public import get_candles_recent
from utils import format_number


def manage_trade_exits(client):
    """
    Manage exiting open positions based upon criteria set in constants
    :param client:
    :return:
    """
    save_output = []

    # Opening active trades JSON file
    try:
        open_positions_file = open(AGENTS_DATA_PATH)
        open_positions_dict = json.load(open_positions_file)
    except Exception as e:
        print(f"Exception opening file {AGENTS_DATA_PATH}: {e}")
        return "complete"

    # Exit if no open positions in file
    if len(open_positions_dict) < 1:
        return "complete"

    # Get all open positions per trading platform
    exchange_pos = client.private.get_positions(status="OPEN")
    all_exc_pos = exchange_pos.data["positions"]
    markets_live = []
    for pos in all_exc_pos:
        markets_live.append(pos["market"])

    time.sleep(0.5)

    # Check all saved positions match order record
    for position in open_positions_dict:
        # Init is_close trigger
        is_close = False

        # Extract position information for market 1
        position_market_m1 = position["market_1"]
        position_size_m1 = position["order_m1_size"]
        position_side_m1 = position["order_m1_side"]

        # Extract position information for market 2
        position_market_m2 = position["market_2"]
        position_size_m2 = position["order_m2_size"]
        position_side_m2 = position["order_m2_side"]
        time.sleep(0.25)

        # Get order info m1 per exchange
        order_m1 = client.private.get_order_by_id(position["order_id_m1"])
        order_market_m1 = order_m1.data["order"]["market"]
        order_size_m1 = order_m1.data["order"]["size"]
        order_side_m1 = order_m1.data["order"]["side"]
        time.sleep(0.25)

        # Get order info m2 per exchange
        order_m2 = client.private.get_order_by_id(position["order_id_m2"])
        order_market_m2 = order_m2.data["order"]["market"]
        order_size_m2 = order_m2.data["order"]["size"]
        order_side_m2 = order_m2.data["order"]["side"]
        time.sleep(0.25)

        # matching checks
        check_m1 = (
            position_market_m1 == order_market_m1
            and position_size_m1 == order_size_m1
            and position_side_m1 == order_side_m1
        )
        check_m2 = (
            position_market_m2 == order_market_m2
            and position_size_m2 == order_size_m2
            and position_side_m2 == order_side_m2
        )
        check_live = (
            position_market_m1 in markets_live
            and position_market_m2 in markets_live
        )

        # If checks failed exit
        if not check_live and not check_m1 and not check_m2:
            print(
                f"[WARNING] Not all open positions match exchange records "
                f"for {position_market_m1} and {position_market_m2}."
            )
            continue

        # Get prices
        series_1 = get_candles_recent(client, position_market_m1)
        time.sleep(0.25)
        series_2 = get_candles_recent(client, position_market_m2)
        time.sleep(0.25)

        # Get markets for reference
        markets = client.public.get_markets().data
        time.sleep(0.25)

        # Trigger close based on ZScore
        if CLOSE_AT_ZSCORE_CROSS:
            # print(f"series_1: {series_1[-1]}")
            # print(f"series_2: {series_2[-1]}")
            hedge_ration = position["hedge_ratio"]
            z_score_traded = position["z_score"]
            if len(series_1) > 0 and len(series_1) == len(series_2):
                spread = series_1 - (hedge_ration * series_2)
                z_score_current = calculate_zscore(spread).values.tolist()[-1]

            # Trigger
            z_score_level_check = abs(z_score_current) >= abs(z_score_traded)
            z_score_cross_check = (
                z_score_current < 0 and z_score_traded > 0
            ) or (z_score_current > 0 and z_score_traded < 0)

            # Close trade
            if z_score_cross_check and z_score_level_check:
                # Init close trigger
                is_close = True

        if is_close:
            side_m1 = "BUY" if position_side_m1 == "SELL" else "SELL"
            side_m2 = "BUY" if position_side_m2 == "SELL" else "SELL"

            price_m1 = float(series_1[-1])
            price_m2 = float(series_2[-1])
            accept_price_m1 = (
                price_m1 * 1.05 if side_m1 == "BUY" else price_m1 * 0.95
            )
            accept_price_m2 = (
                price_m2 * 1.05 if side_m2 == "BUY" else price_m2 * 0.95
            )

            tick_size_m1 = markets["markets"][position_market_m1]["tickSize"]
            tick_size_m2 = markets["markets"][position_market_m2]["tickSize"]
            accept_price_m1 = format_number(accept_price_m1, tick_size_m1)
            accept_price_m2 = format_number(accept_price_m2, tick_size_m2)

            # Close positions
            try:
                # Close market 1
                print(f"[CLOSE] Closing m1 position for {position_market_m1}")
                close_order_m1 = place_market_order(
                    client=client,
                    market=position_market_m1,
                    side=side_m1,
                    size=position_size_m1,
                    price=accept_price_m1,
                    reduce_only=True,
                )
                print(f"[CLOSE] {close_order_m1['order']['id']}")
                time.sleep(1)
            except Exception as e:
                print(
                    f"[CLOSE ERROR] Exit failed for {position_market_m1}: {e}"
                )
                save_output.append(position)

            try:
                # Close market 2
                print(f"[CLOSE] Closing m2 position for {position_market_m2}")
                close_order_m2 = place_market_order(
                    client=client,
                    market=position_market_m2,
                    side=side_m2,
                    size=position_size_m2,
                    price=accept_price_m2,
                    reduce_only=True,
                )
                print(f"[CLOSE] {close_order_m2['order']['id']}")
            except Exception as e:
                print(
                    f"[CLOSE ERROR] Exit failed for {position_market_m2}: {e}"
                )
                save_output.append(position)
        else:
            # Keep record if items and save
            save_output.append(position)

    # Save remaining
    print(f"{len(save_output)} Items remaining. Saving file")
    with open(AGENTS_DATA_PATH, "w") as f:
        json.dump(save_output, f)
