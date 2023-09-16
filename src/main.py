import sys

from connections import connect_dydx

if __name__ == "__main__":
    # connect to client
    try:
        client = connect_dydx()
    except Exception as e:
        print(f"Error connecting to client: {e}")  # @todo debug
        sys.exit(1)
