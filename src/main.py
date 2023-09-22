import sys

import constants
from cointegration import store_cointegration_results
from connections import connect_dydx
from entry_pairs import open_positions
from positions import abort_all_positions
from public import construct_market_prices

if __name__ == "__main__":
    # connect to client
    try:
        print("Connecting to DYDX Client...")
        client = connect_dydx()
    except Exception as e:
        print(f"Error connecting to client: {e}")
        sys.exit(1)

    # Abort all open positions
    if constants.ABORT_ALL_POSITIONS:
        try:
            print("Closing all positions...")
            closed_orders, _ = abort_all_positions(client)
        except Exception as e:
            print(f"Error closing all positions: {e}")
            sys.exit(1)

    # Find cointegrated pairs
    if constants.FIND_INTEGRATED:
        # Construct market prices
        try:
            print("Fetching market prices...")
            df_market_prices = construct_market_prices(client)
        except Exception as e:
            print(f"Error constructing market prices: {e}")
            sys.exit(1)

        # Store Cointegrated pairs
        try:
            print("Storing Cointegrated pairs...")
            stores_result = store_cointegration_results(df_market_prices)
            if stores_result != "saved":
                print("Error saving cointegrated pairs")
                sys.exit(1)
        except Exception as e:
            print(f"Error storing cointegrated pairs: {e}")
            sys.exit(1)

    # @todo more will be added here

    # Place trades for opening positions
    if constants.PLACE_TRADES:
        try:
            print("Finding trading opportunities...")
            open_positions(client)
        except Exception as e:
            print(f"Error trading pairs: {e}")
            sys.exit(1)
