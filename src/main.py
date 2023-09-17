import sys

import constants
from connections import connect_dydx
from positions import abort_all_positions

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
