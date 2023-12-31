from datetime import datetime, timedelta

import pandas as pd

from constants import ORDERS_LOG_PATH


# Format number
def format_number(curr_num, match_num) -> str:
    """

    :param curr_num:
    :param match_num:
    :return:
    """
    match_num_str = f"{match_num}"

    if "." in match_num_str:
        match_decimals = len(match_num_str.split(".")[1])
        curr_num_str = f"{curr_num:.{match_decimals}f}"
        curr_num_str = curr_num_str[:]
        return curr_num_str

    return f"{int(curr_num)}"


# Add order to log
def log_order(order_data: dict | list[dict]):
    """
    log entry:
    placed_order.data:
    {
        'id': '62f80c8a014788ab3716ad0',
        'clientId': '9690414608779876',
        'accountId': '41379924-2e19-5bf0-8434-ac230128f673',
        'market': 'AAVE-USD',
        'side': 'SELL',
        'price': '18.02',
        'triggerPrice': None,
        'trailingPercent': None,
        'size': '1',
        'reduceOnlySize': None,
        'remainingSize': '1',
        'type': 'MARKET',
        'createdAt': '2023-09-17T17:20:48.862Z',
        'unfillableAt': None,
        'expiresAt': '2023-09-17T17:21:58.347Z',
        'status': 'PENDING',
        'timeInForce': 'FOK',
        'postOnly': False,
        'reduceOnly': True,
        'cancelReason': None
    }

    :return:
    """
    df = pd.DataFrame(order_data)
    with open(f"../{ORDERS_LOG_PATH}", "a") as f:
        df.to_csv(f, header=f.tell() == 0)


# Format time
def format_time(timestamp):
    return timestamp.replace(microsecond=0).isoformat()


# Get ISO Times
def get_iso_times(date_start=None, limit=100) -> dict:
    # Get timestamps
    date_start_0 = date_start if date_start else datetime.now()
    date_start_1 = date_start_0 - timedelta(hours=limit)

    # Format datetimes
    from_iso = format_time(date_start_1)
    to_iso = format_time(date_start_0)

    return {
        "date_start_0": date_start_0,
        "date_start_1": date_start_1,
        "from_iso": from_iso,
        "to_iso": to_iso,
    }


def get_iso_times_ranges(n=4, date_start=None):
    for _ in range(n):
        t_frame = get_iso_times(date_start=date_start)
        date_start = t_frame["date_start_1"]
        yield t_frame
