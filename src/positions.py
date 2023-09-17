import time
from datetime import datetime, timedelta

from dydx3.errors import DydxApiError

from constants import ORDERS_LOG
from utils import format_number, log_order


# Place order
def place_market_order(
    client,
    market,
    side,
    size,
    price,
    limit_fee="0.015",
    reduce_only=False,
    log_order=False,
):
    print("place_market_order()")
    # Get PositionId
    account_response = client.private.get_account()
    position_id = account_response.data["account"]["positionId"]

    # Get expiration time
    server_time = client.public.get_time()
    expiration = datetime.fromisoformat(
        server_time.data["iso"].replace("Z", "+00:00")
    ) + timedelta(seconds=70)

    # Place an order
    """
    Order definition from Google Collab sheet:
    placed_order = client.private.create_order(
        position_id=position_id,  # required for creating the order signature
        market="BTC-USD",
        side="BUY",
        order_type="MARKET",
        post_only=False,
        size='0.001',
        price='100000',
        limit_fee='0.015',
        expiration_epoch_seconds=expiration.timestamp(),
        time_in_force="FOK",
        reduce_only=False
    )
    """
    placed_order = client.private.create_order(
        position_id=position_id,  # required for creating the order signature
        market=market,
        side=side,
        order_type="MARKET",
        post_only=False,
        size=size,
        price=price,
        limit_fee=limit_fee,
        expiration_epoch_seconds=expiration.timestamp(),
        time_in_force="FOK",
        reduce_only=reduce_only,
    )
    print(f"placed_order.id: {placed_order.data['order']['id']}")
    placed_order_data = placed_order.data
    if ORDERS_LOG and log_order:
        log_order(placed_order_data["order"])
    return placed_order_data


# Abort all open positions
def abort_all_positions(client):
    print("abort_all_positions()")
    client.private.cancel_all_orders()
    time.sleep(0.75)  # Protect API

    # Get markets for reference of tick size
    markets = client.public.get_markets().data
    time.sleep(0.75)  # Protect API

    # Get all open positions
    positions = client.private.get_positions(status="OPEN")
    all_positions = positions.data["positions"]
    print(f"all_positions to abort: {len(all_positions)}")

    closed_orders = []
    error_orders = []
    for position in all_positions:
        market = position["market"]
        side = "SELL" if position["side"] == "LONG" else "BUY"
        print(f"position: {position}")
        print(f"market: {market}, side: {side}")

        # Get price
        price = float(position["entryPrice"])
        accept_price = price * 1.7 if side == "BUY" else price * 0.3
        tick_size = markets["markets"][market]["tickSize"]
        accept_price = format_number(accept_price, tick_size)

        # Place order to close
        try:
            order = place_market_order(
                client=client,
                market=market,
                side=side,
                size=position["sumOpen"],
                price=accept_price,
                reduce_only=True,
            )
        except DydxApiError as e:
            print(f"Error closing position ({side}){market}: {e}")
            error_orders.append(
                {
                    "market": market,
                    "side": side,
                    "size": position["sumOpen"],
                    "price": accept_price,
                    "reduce_only": True,
                }
            )
        else:
            closed_orders.append(order)
        time.sleep(0.25)  # Protect API

    print(f"closed_orders: {len(closed_orders)}")
    if error_orders:
        print(f"error_orders: {len(error_orders)}")
    if ORDERS_LOG:
        log_order([d["order"] for d in closed_orders])
    return closed_orders, error_orders
