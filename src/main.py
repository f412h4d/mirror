#!/usr/bin/env python3

import copy
import os

from binance import Client, ThreadedWebsocketManager

from modules.balance import get_client_balances
# internal modules
from modules.env import load_environment
from modules.globals import globals_instance
from modules.log import generate_and_log_order_info, save_dict_to_json
from modules.orders.cancel import (cancel_tp_sl_orders,
                                   cancel_tp_or_sl,
                                   handle_order_cancellation)
from modules.orders.create import handle_normal_new_order, handle_otoco_new_order
from modules.orders.sl import custom_sl
from modules.orders.tp import custom_tp
from modules.positions import get_positions_info
from modules.prepare import clean, conditional_clean
from modules.utils import (is_part_of_otoco,
                           calculate_order_percentage)

api_key, api_secret, lev_api_key, lev_api_secret, main_lev, sub_lev = load_environment()


def main():
    client = Client(api_key, api_secret, testnet=False)
    lev_client = Client(lev_api_key, lev_api_secret, testnet=False)

    get_client_balances("\nMain Account", client)
    client.futures_change_leverage(symbol='BTCUSDT', leverage=main_lev)
    lev_client.futures_change_leverage(symbol='BTCUSDT', leverage=sub_lev)
    get_client_balances("\n10X Account", lev_client)

    twm = ThreadedWebsocketManager(api_key=api_key,
                                   api_secret=api_secret,
                                   testnet=False)
    twm.start()

    def handle_socket_message(msg):
        if msg['e'] == 'ORDER_TRADE_UPDATE':
            generate_and_log_order_info(msg)

            order_info = msg['o']
            order_status = order_info['X']
            order_exec_type = order_info['x']
            order_id = order_info['i']
            symbol = order_info.get('s')
            side = order_info.get('S')
            order_type = order_info.get('o')
            quantity = order_info.get('q')
            price = order_info.get('p')

            if order_status == "PARTIALLY_FILLED" and order_type == "LIMIT":
                return

            if order_status == "PARTIALLY_FILLED":
                # Ignoring FILL Event that is for quantity increment
                if globals_instance.last_side == side:
                    os.makedirs('../logs/partial_fills_QI', exist_ok=True)
                    with open("../logs/partial_fills/partial_fills_QI.txt", "a") as partial_fills_file:
                        partial_fills_file.write(str(msg) + "\n")
                    return

                # Logging the partial fill events
                os.makedirs('../logs/partial_fills', exist_ok=True)
                with open("../logs/partial_fills/partial_fills.txt", "a") as partial_fills_file:
                    partial_fills_file.write(str(msg) + "\n")

                globals_instance.timer_manager.start_new_timer(
                    seconds=5,
                    callback=conditional_clean,
                    client=client,
                    lev_client=lev_client
                )
                return

            if order_status == "EXPIRED" or order_exec_type == "EXPIRED":
                globals_instance.is_expired = True
                return

            if order_type == 'LIMIT' and order_status == "FILLED" and order_exec_type == "TRADE":
                entry_price, position_q = get_positions_info(client=client, is_main=True)
                _, lev_position_q = get_positions_info(client=lev_client, is_main=False)

                if float(position_q) == 0 or float(lev_position_q) == 0:
                    print("No Position Is Added Quiting")
                    return

                if float(position_q) == float(order_info['q']):
                    print("No Custom Order For First Order")
                    return

                cancel_tp_or_sl(client=lev_client, mode="SL")
                cancel_tp_or_sl(client=lev_client, mode="TP")

                cancel_tp_sl_orders(client)

                tp_order_info = copy.deepcopy(order_info)
                sl_order_info = copy.deepcopy(order_info)
                lev_tp_order_info = copy.deepcopy(order_info)
                lev_sl_order_info = copy.deepcopy(order_info)

                # temp change for release
                custom_tp(lev_client=client,
                          order_info=tp_order_info,
                          otoco_orders_data=globals_instance.OTOCO_orders_data,
                          tp_info=globals_instance.last_tp,
                          new_quantity=round(float(position_q), 3))
                custom_sl(lev_client=client,
                          order_info=sl_order_info,
                          otoco_orders_data=globals_instance.OTOCO_orders_data,
                          new_quantity=round(float(position_q), 3),
                          sl_info=globals_instance.last_sl)

                globals_instance.OTOCO_orders_data = custom_tp(lev_client=lev_client,
                                                               order_info=lev_tp_order_info,
                                                               otoco_orders_data=globals_instance.OTOCO_orders_data,
                                                               new_quantity=round(float(lev_position_q), 3),
                                                               # entry_price=lev_entry_price  removed due to release
                                                               tp_info=globals_instance.last_tp)
                globals_instance.OTOCO_orders_data = custom_sl(lev_client=lev_client,
                                                               order_info=lev_sl_order_info,
                                                               otoco_orders_data=globals_instance.OTOCO_orders_data,
                                                               new_quantity=round(float(lev_position_q), 3),
                                                               sl_info=globals_instance.last_sl)

            if order_type == 'MARKET' and not (order_info["ot"] in ["STOP_MARKET", "TAKE_PROFIT_MARKET"]) or (
                    order_type == "MARKET" and order_status == "NEW"
            ):
                # Ignoring the events if we are in expire phase
                if globals_instance.is_expired:
                    return

                _, lev_position_q = get_positions_info(lev_client, is_main=False)
                order_info["q"] = round(float(lev_position_q), 3)
                # change the quantity and letting it reach the other block

            if order_type == 'MARKET' and order_status == "FILLED":
                # Ignoring MARKET Event that is for quantity increment
                if globals_instance.last_side == side:
                    return

                clean(client=client, lev_client=lev_client)

                print("Reset is done")
                return

            if order_status == "CANCELED":
                handle_order_cancellation(order_id=order_id, lev_client=lev_client)
                return

            if not is_part_of_otoco(order_info) and order_status == "NEW" and order_exec_type == "NEW":
                custom_order_id = str(order_info["c"])
                if custom_order_id and custom_order_id.split("_")[0] == "custom":
                    # Ignoring the custom tp or sl and loging it
                    save_dict_to_json(directory="ignored_orders", filename=f"{order_info['i']}", dictionary=order_info)
                    return

                wallet_balance = get_client_balances(tag="Main", client=client)
                order_percentage = calculate_order_percentage(wallet_balance=wallet_balance,
                                                              order_info=order_info,
                                                              main_lev=main_lev)

                handle_normal_new_order(order_info=order_info,
                                        client=lev_client,
                                        symbol=symbol,
                                        side=side,
                                        order_type=order_type,
                                        quantity=quantity,
                                        order_percentage=order_percentage,
                                        price=price,
                                        leverage=sub_lev)

            if not is_part_of_otoco(order_info) and order_status == "NEW" and order_exec_type == "AMENDMENT":
                handle_order_cancellation(order_id=order_id, lev_client=lev_client)

                wallet_balance = get_client_balances(tag="Main", client=client)
                order_percentage = calculate_order_percentage(wallet_balance,
                                                              order_info,
                                                              main_lev=main_lev)
                handle_normal_new_order(order_info=order_info,
                                        client=lev_client,
                                        symbol=symbol,
                                        side=side,
                                        order_type=order_type,
                                        quantity=quantity,
                                        order_percentage=order_percentage,
                                        price=price,
                                        leverage=sub_lev)

            elif is_part_of_otoco(order_info) and order_status == "NEW":
                save_dict_to_json(directory="otoco_orders", filename=f"{order_info['i']}", dictionary=order_info)
                handle_otoco_new_order(
                    order_info=order_info,
                    client=client,
                    lev_client=lev_client,
                    main_lev=main_lev, sub_lev=sub_lev
                )

            elif is_part_of_otoco(order_info) and order_status == "AMENDMENT":
                handle_order_cancellation(order_id=order_id, lev_client=lev_client)
                handle_otoco_new_order(
                    order_info=order_info,
                    client=client,
                    lev_client=lev_client,
                    main_lev=main_lev, sub_lev=sub_lev
                )

        else:
            with open("events.txt", "a") as events_file:
                events_file.write(str(msg) + "\n")

    print("Listening for futures account updates...\n")

    def handle_events(msg):
        handle_socket_message(msg)

    # Listen to the futures user data stream
    twm.start_futures_user_socket(callback=handle_events)

    try:
        twm.join()
    except KeyboardInterrupt:
        print("\n"
              "Script execution stopped by user. Exiting gracefully.")
    except Exception as e:
        with open("errors.txt", "a") as error_file:
            error_file.write(str(e) + "\n")
        print("An error occurred. Please check errors.txt for details.")
    finally:
        twm.stop()
        exit(0)


if __name__ == "__main__":
    main()
