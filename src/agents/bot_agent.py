import sys
import time
from datetime import datetime

from src.notifications.telegram import send_message
from src.positions import check_order_status, place_market_order


class BotAgent:
    """ """

    def __init__(
        self,
        client,
        market_1,
        market_2,
        base_side,
        base_size,
        base_price,
        quote_side,
        quote_size,
        quote_price,
        accept_failsafe_base_price,
        z_score,
        half_life,
        hedge_ratio,
    ):
        self.client = client
        self.market_1 = market_1
        self.market_2 = market_2
        self.base_side = base_side
        self.base_size = base_size
        self.base_price = base_price
        self.quote_side = quote_side
        self.quote_size = quote_size
        self.quote_price = quote_price
        self.accept_failsafe_base_price = accept_failsafe_base_price
        self.z_score = z_score
        self.half_life = half_life
        self.hedge_ratio = hedge_ratio

        # output variable, pair status options are FAILED, LIVE, CLOSE, ERROR
        self.order_dict = {
            "market_1": market_1,
            "market_2": market_2,
            "hedge_ratio": hedge_ratio,
            "z_score": z_score,
            "half_life": half_life,
            "order_id_m1": "",
            "order_m1_size": base_size,
            "order_m1_side": base_side,
            "order_time_m1": "",
            "order_id_m2": "",
            "order_m2_size": quote_size,
            "order_m2_side": quote_side,
            "order_time_m2": "",
            "pair_status": "",
            "comments": "",
        }
        self.EXIT_MSG = "Shutting down bot"

    # Check order status by ID
    def check_order_status_by_id(self, order_id):
        time.sleep(2)  # Allow time to process

        order_status = check_order_status(self.client, order_id)

        # Check if order canceled, move onto next Pair
        if order_status == "CANCELED":
            print(f"[CANCELED] {self.market_1} vs {self.market_2}.")
            self.order_dict["pair_status"] = "FAILED"
            return "failed"

        # Check if order not filled, wait until order expire
        if order_status != "FAILED":
            time.sleep(15)
            order_status = check_order_status(self.client, order_id)

            # Check if order canceled, move onto next Pair
            if order_status == "CANCELED":
                print(f"[CANCELED] {self.market_1} vs {self.market_2}.")
                self.order_dict["pair_status"] = "FAILED"
                return "failed"

            # Check if not filled, cancel order
            if order_status != "FILLED":
                self.client.private.cancel_order(order_id)
                self.order_dict["pair_status"] = "ERROR"
                print(f"[ERROR] {self.market_1} vs {self.market_2}.")

        return "live"

    def open_trades(self):
        print("*******")
        print(f"[ORDER] {self.market_1}: Placing first order.")
        print(f"[ORDER] Side: {self.base_side}.")
        print(f"[ORDER] Size: {self.base_size}.")
        print(f"[ORDER] Price: {self.base_price}.")
        print("*******")

        # Place order
        try:
            base_order = place_market_order(
                client=self.client,
                market=self.market_1,
                side=self.base_side,
                size=self.base_size,
                price=self.base_price,
                reduce_only=False,
            )

            self.order_dict["order_id_m1"] = base_order["order"]["id"]
            self.order_dict["order_time_m1"] = datetime.now().isoformat()
        except Exception as e:
            self.order_dict["pair_status"] = "ERROR"
            error = f"[ERROR] Market 1 {self.market_1}: Order error {e}."
            self.order_dict["comments"] = error
            print(error)
            return self.order_dict

        # Ensure order is live before processing
        order_status_m1 = self.check_order_status_by_id(
            self.order_dict["order_id_m1"]
        )

        # Abort if order failed
        if order_status_m1 != "live":
            self.order_dict["pair_status"] = "ERROR"
            error = f"[ERROR] {self.market_1} failed to fill."
            self.order_dict["comments"] = error
            print(error)
            return self.order_dict

        print("*******")
        print(f"[ORDER] {self.market_2}: Placing second order.")
        print(f"[ORDER] Side: {self.quote_side}.")
        print(f"[ORDER] Size: {self.quote_size}.")
        print(f"[ORDER] Price: {self.quote_price}.")
        print("*******")

        # Place order
        try:
            quote_order = place_market_order(
                client=self.client,
                market=self.market_2,
                side=self.quote_side,
                size=self.quote_size,
                price=self.quote_price,
                reduce_only=False,
            )

            self.order_dict["order_id_m2"] = quote_order["order"]["id"]
            self.order_dict["order_time_m2"] = datetime.now().isoformat()
        except Exception as e:
            self.order_dict["pair_status"] = "ERROR"
            error = f"[ERROR] Market 2 {self.market_2}: Order error {e}."
            self.order_dict["comments"] = error
            print(error)
            send_message(
                f"Failed to execute. Code red! Error code: 102"
                f"\n{error}\n{self.EXIT_MSG}"
            )
            return self.order_dict

        order_status_m2 = self.check_order_status_by_id(
            self.order_dict["order_id_m2"]
        )
        if order_status_m2 != "live":
            self.order_dict["pair_status"] = "ERROR"
            error = f"[ERROR] {self.market_2} failed to fill."
            self.order_dict["comments"] = error
            print(error)
            # return self.order_dict

            # close base order
            try:
                close_order = place_market_order(
                    client=self.client,
                    market=self.market_1,
                    side=self.quote_side,
                    size=self.base_size,
                    price=self.accept_failsafe_base_price,
                    reduce_only=True,
                )

                # Ensure order is live before proceeding
                time.sleep(2)
                order_status_close_order = check_order_status(
                    self.client, close_order["order"]["id"]
                )

                send_message("Failed to execute. Code red! Error code: 100")

                if order_status_close_order != "FILLED":
                    print("[ERROR] ABORT PROGRAM. Unexpected Error")
                    print(order_status_close_order)

                    # send notification
                    send_message(
                        f"Failed to execute. Code red! Error code: "
                        f"101\n{self.EXIT_MSG}"
                    )
                    sys.exit(1)
            except Exception as e:
                self.order_dict["pair_status"] = "ERROR"
                error = f"[ERROR] Close Market 1 {self.market_1} error {e}."
                self.order_dict["comments"] = error
                print(error)
                print("[ERROR] ABORT PROGRAM. Unexpected Error")
                # send notification
                send_message(
                    f"Failed to execute. Code red! Error code: 102"
                    f"\n{error}\n{self.EXIT_MSG}"
                )
                sys.exit(1)
        else:
            self.order_dict["pair_status"] = "LIVE"
            return self.order_dict
