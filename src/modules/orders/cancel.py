from ..globals import globals_instance


def cancel_tp_sl_orders(client):
    try:
        open_orders = client.futures_get_open_orders()
        if not open_orders:
            print("No open futures orders to cancel.")
            return

        for order in open_orders:
            if order.get('type') in ["TAKE_PROFIT_MARKET", "STOP_MARKET"]:
                result = client.futures_cancel_order(symbol=order['symbol'], orderId=order['orderId'])
                print(f"Cancelled Order: {order['symbol']} - Order ID: {order['orderId']}, Status: {result['status']}")
    except Exception as e:
        print("An error occurred: ", e)


def cancel_futures_order(client, symbol, order_id):
    try:
        result = client.futures_cancel_order(symbol=symbol, orderId=order_id)
        print(f"Cancelled Order: {symbol} - Order ID: {order_id}, Status: {result['status']}")
    except Exception as e:
        print("An error occurred while canceling the order: ", e)


def cancel_all_futures_orders(client):
    try:
        open_orders = client.futures_get_open_orders()
        print(f"Length of open orders: {len(open_orders)}")
        if not open_orders:
            print("No open futures orders to cancel.")
            return

        for order in open_orders:
            result = client.futures_cancel_order(symbol=order['symbol'], orderId=order['orderId'])
            print(f"Cancelled Order: {order['symbol']} - Order ID: {order['orderId']}, Status: {result['status']}")
    except Exception as e:
        print("An error occurred: ", e)


def handle_order_cancellation(order_id, lev_client):
    for order_key, order_value in globals_instance.orders_data.items():
        if order_value['info']['i'] == order_id:
            print("\n"
                  "Canceling order,\n"
                  f"Id: {order_key},\n"
                  f"Parent Id: {order_id}")

            cancel_futures_order(client=lev_client, symbol=order_value['info']['s'], order_id=order_key)
            del globals_instance.orders_data[order_key]
            return

    for Si, otoco_order_data in globals_instance.OTOCO_orders_data.items():
        main_order = otoco_order_data.get('main_order')
        tp_order = otoco_order_data.get('tp_order')
        sl_order = otoco_order_data.get('sl_order')

        if main_order and main_order.get('i') == order_id:
            print("Canceling OTOCO main order for Si:", Si, "Order ID:", order_id)
            cancel_futures_order(client=lev_client, symbol=main_order['s'], order_id=main_order["i"])
            del globals_instance.OTOCO_orders_data[Si]
            return None

        if tp_order and tp_order.get('i') == order_id:
            tp_child = tp_order["child"]
            if not tp_child:
                print("No Child Found For TP")
                return

            child_id = tp_child["orderId"]
            if not child_id:
                print("TP Child Found, But Has No ID")
                return

            print("Canceling OTOCO TP order for Si: ", Si, "Parent Order ID: ", order_id, "Child: ",
                  child_id)
            cancel_futures_order(client=lev_client, symbol=main_order['s'], order_id=child_id)
            return None

        if sl_order and sl_order.get('i') == order_id:
            sl_child = sl_order["child"]
            if not sl_child:
                print("No Child Found For SL")
                return

            child_id = sl_child["orderId"]
            if not child_id:
                print("SL Child Found, But Has No ID")
                return

            print("Canceling OTOCO SL order for Si: ", Si, "Parent Order ID: ", order_id, "Child: ",
                  child_id)
            cancel_futures_order(client=lev_client, symbol=main_order['s'], order_id=child_id)
            return None

    print("Order not found for cancellation in both orders_data and OTOCO_orders_data.")


def cancel_tp_or_sl(client, mode="TP"):
    for Si, otoco_order_data in globals_instance.OTOCO_orders_data.items():
        if not otoco_order_data:
            continue

        order_to_cancel = otoco_order_data.get(f'{mode.lower()}_order')
        print(Si, otoco_order_data, order_to_cancel)
        if not order_to_cancel:
            print(f"there's no TP/SL order to cancel based on mode: {mode}")
            continue

        child = order_to_cancel.get("child", {})
        child_order_id = child.get('orderId')
        if not child or not child_order_id:
            print(f"No {mode} child order to cancel for Si: {Si}")
            continue

        symbol = otoco_order_data.get('main_order', {}).get('s')
        if not symbol:
            print(f"Missing symbol for Si: {Si}")
            continue

        print(f"Canceling OTOCO {mode} order because of change, Si: {Si}, Child: {child_order_id}")
        try:
            cancel_futures_order(client=client, symbol=symbol, order_id=child_order_id)
            otoco_order_data[f'{mode.lower()}_order'] = None
        except Exception as e:
            print(f"Failed to cancel {mode} order for Si: {Si}. Error: {e}")
