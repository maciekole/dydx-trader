import sys
import time

import constants
from cointegration import store_cointegration_results
from connections import connect_dydx
from entry_pairs import open_positions
from exit_pairs import manage_trade_exits
from notifications.telegram import send_message
from positions import abort_all_positions
from public import construct_market_prices

if __name__ == "__main__":
    exit_msg = "Shutting down bot"
    send_message("Bot launched successful")

    # connect to client
    try:
        print("Connecting to DYDX Client...")
        client = connect_dydx()
        send_message("Bot Connected to DYDX")
    except Exception as e:
        print(f"Error connecting to client: {e}")
        send_message(f"Error connecting to client: {e}\n{exit_msg}")
        sys.exit(1)

    # Abort all open positions
    if constants.ABORT_ALL_POSITIONS:
        close_msg = "Closing all positions..."
        try:
            print(close_msg)
            send_message(close_msg)
            closed_orders, _ = abort_all_positions(client)
        except Exception as e:
            print(f"Error closing all positions: {e}")
            send_message(f"Error closing all positions: {e}\n{exit_msg}")
            sys.exit(1)

    # Find cointegrated pairs
    if constants.FIND_INTEGRATED:
        # Construct market prices
        try:
            print("Fetching market prices...")
            df_market_prices = construct_market_prices(client)
        except Exception as e:
            print(f"Error constructing market prices: {e}")
            send_message(f"Error constructing market prices: {e}\n{exit_msg}")
            sys.exit(1)

        # Store Cointegrated pairs
        try:
            print("Storing Cointegrated pairs...")
            stores_result = store_cointegration_results(df_market_prices)
            if stores_result != "saved":
                print("Error saving cointegrated pairs")
                send_message(f"Error saving cointegrated pairs.\n{exit_msg}")
                sys.exit(1)
        except Exception as e:
            print(f"Error storing cointegrated pairs: {e}")
            send_message(f"Error storing cointegrated pairs: {e}\n{exit_msg}")
            sys.exit(1)

    # Run always on
    while True:
        # Place trades for closing positions
        if constants.MANAGE_EXITS:
            try:
                print("Manage exit opportunities...")
                manage_trade_exits(client)
            except Exception as e:
                print(f"Error managing exiting positions: {e}")
                send_message(
                    f"Error managing exiting positions: {e}\n{exit_msg}"
                )
                sys.exit(1)

        # Place trades for opening positions
        if constants.PLACE_TRADES:
            try:
                print("Finding trading opportunities...")
                open_positions(client)
            except Exception as e:
                print(f"Error trading pairs: {e}")
                send_message(f"Error trading pairs: {e}\n{exit_msg}")
                sys.exit(1)
        time.sleep(60)
