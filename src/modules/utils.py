from .globals import globals_instance


def calculate_order_percentage(wallet_balance, order_info, main_lev=1):
    quantity = float(order_info['q'])
    price = float(order_info['p']) if 'p' in order_info else None

    order_value = quantity * price if price else None

    if order_value and wallet_balance > 0:
        percentage_of_balance = (order_value / (wallet_balance * main_lev))

        # Prepare the log message
        log_message = (
            f"\n________________________"
            f"Balance: {wallet_balance}, Quantity: {quantity}, Price: {price}, "
            f"Order Value: {order_value}, Main Lev: {main_lev}, "
            f"Percentage of Balance: {percentage_of_balance}\n"
        )

        # Append the log message to the file
        with open("q_log.txt", "a") as log_file:
            log_file.write(log_message)

        return percentage_of_balance
    else:
        print(f"Unable to calculate the percentage for Order ID: {order_info['i']}.")
        return -1


def sum_total_asset_in_open_orders(client, symbol):
    try:
        open_orders = client.futures_get_open_orders(symbol=symbol)
        total_asset = 0

        for order in open_orders:
            quantity = float(order['origQty'])  # original quantity of the order
            total_asset += quantity

        print(f"Total asset quantity in open orders for {symbol}: {total_asset}")
        return total_asset
    except Exception as e:
        print("An error occurred: ", e)
        return None


def is_part_of_otoco(order_info):
    si = order_info.get('si')
    order_type = order_info['o']

    if int(si) == 0 and not (order_type in ['TAKE_PROFIT_MARKET', 'STOP_MARKET']):
        print("Order is NOT OTOCO")
        return False

    print("Order is OTOCO")
    return True


def extract_order_params(order_info):
    """
    Extracts specific parameters from the order_info dictionary and returns them in a new_params structure.
    """
    # Define the keys to extract and their corresponding names in the new_params structure
    keys_to_extract = {
        's': 'symbol',
        'S': 'side',
        'o': 'type',
        'f': 'timeInForce',
        'q': 'quantity',
        'p': 'price',
        'i': 'orderId',  # Assuming you want the original order ID
        'c': 'newClientOrderId',  # Assuming you want to set a new client order ID
        'T': 'recvWindow',  # Assuming you want to set a recvWindow
    }

    # Initialize an empty dictionary for the new parameters
    new_params = {}

    # Iterate over the order_info dictionary
    for key, value in order_info.items():
        # Check if the current key is in the keys_to_extract dictionary
        if key in keys_to_extract:
            # If it is, add the key-value pair to the new_params dictionary
            new_params[keys_to_extract[key]] = value

    # Return the new_params dictionary
    return new_params


def extract_tp_sl(order_info):
    tp_sl_info = {
        "id": order_info['i'],
        "quantity": order_info['q'],
        "symbol": order_info['s'],
        "side": order_info['S'],
        "stop_price": order_info.get('sp', None),
        "working_type": order_info.get('wt')
    }

    return tp_sl_info


def get_child_id(order_id):
    for order_key, order_value in globals_instance.orders_data.items():
        if order_value['info']['i'] == order_id:
            return order_key
