import sys

import constants
from cointegration import store_cointegration_results
from connections import connect_dydx
from positions import abort_all_positions
from public import construct_market_prices

if __name__ == "__main__":
    # connect to client
    try:
        print("Connecting to DYDX Client...")  # @todo debug
        client = connect_dydx()
    except Exception as e:
        print(f"Error connecting to client: {e}")  # @todo debug
        sys.exit(1)

    # Abort all open positions
    if constants.ABORT_ALL_POSITIONS:
        try:
            print("Closing all positions...")  # @todo debug
            closed_orders, _ = abort_all_positions(client)
        except Exception as e:
            print(f"Error closing all positions: {e}")  # @todo debug
            sys.exit(1)

    # Find cointegrated pairs
    if constants.FIND_INTEGRATED:
        # Construct market prices
        try:
            print("Fetching market prices...")  # @todo debug
            df_market_prices = construct_market_prices(client)
        except Exception as e:
            print(f"Error constructing market prices: {e}")  # @todo debug
            sys.exit(1)

        # Store Cointegrated pairs
        try:
            print("Storing Cointegrated pairs...")  # @todo debug
            stores_result = store_cointegration_results(df_market_prices)
            if stores_result != "saved":
                print("Error saving cointegrated pairs")  # @todo debug
                sys.exit(1)
        except Exception as e:
            print(f"Error storing cointegrated pairs: {e}")  # @todo debug
            sys.exit(1)
