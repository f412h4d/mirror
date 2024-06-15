from .cancel import cancel_tp_or_sl
from ..balance import get_client_balances, calculate_margin_and_quantity
from ..globals import globals_instance
from ..positions import get_positions_info
from ..utils import calculate_order_percentage, extract_tp_sl


def create_futures_order(client,
                         symbol,
                         side,
                         order_type,
                         quantity,
                         leverage,
                         percent,
                         price=None,
                         # stop_price=None,
                         time_in_force='GTC'):
    try:
        balance = get_client_balances(tag="Virtual", client=client)
        client.futures_change_leverage(symbol=symbol, leverage=leverage)

        if order_type == 'LIMIT':
            margin, new_quantity = calculate_margin_and_quantity(balance=balance,
                                                                 percentage=percent,
                                                                 leverage=leverage,
                                                                 price=price)

            print(
                f"New Margin: {margin},"
                f"Percent: {percent},"
                f"New Quantity: {new_quantity},"
                f"Rounded: {round(new_quantity, 3)}"
            )

            new_quantity = round(new_quantity, 3)
            response = client.futures_create_order(symbol=symbol,
                                                   side=side,
                                                   type=order_type,
                                                   quantity=new_quantity,
                                                   price=price,
                                                   timeInForce=time_in_force)
        else:
            response = client.futures_create_order(symbol=symbol,
                                                   side=side,
                                                   type=order_type,
                                                   quantity=quantity)
        return response
    except Exception as e:
        print("An error occurred: ", e)
        return None


def handle_normal_new_order(order_info,
                            client,
                            symbol,
                            side,
                            order_type,
                            quantity,
                            order_percentage,
                            price,
                            leverage=2):
    try:
        order_response = create_futures_order(client=client,
                                              symbol=symbol,
                                              side=side,
                                              order_type=order_type,
                                              quantity=quantity,
                                              leverage=leverage,
                                              percent=order_percentage,
                                              price=price)

        if 'orderId' in order_response:
            order_id = order_response['orderId']

            print("\n"
                  "Created new order,\n"
                  f"Id: {order_id},\n"
                  f"Parent: {order_info['i']}")

            globals_instance.orders_data[order_id] = {'info': order_info, 'id': order_response}
            return order_id
        else:
            print("Order creation failed or returned an unexpected response:",
                  order_response)

    except Exception as e:
        print(f"An error occurred while creating the order: {e}")


def create_strategy_order(
        client,
        order_type,
        symbol,
        side,
        quantity,
        stop_price,
        price_type='MARK_PRICE'
):
    try:
        response = client.futures_create_order(
            symbol=symbol,
            side=side,
            type=order_type,
            quantity=round(float(quantity), 3),
            stopPrice=round(float(stop_price), 3),
            reduceOnly='TRUE',
            priceProtect='TRUE' if price_type == 'MARK_PRICE' else 'FALSE',
            workingType=price_type,
        )
        print(f"{order_type} order created:", response['orderId'])
        return response
    except Exception as e:
        print(f"Error in creating {order_type} order:", e)
        return None


def process_order(order_info, lev_client, order_type, mode):
    if globals_instance.is_expired:
        return

    cancel_tp_or_sl(client=lev_client, mode=mode)

    if mode == "TP":
        globals_instance.last_tp = extract_tp_sl(order_info=order_info)
    else:
        globals_instance.last_sl = extract_tp_sl(order_info=order_info)

    symbol = order_info['s']
    side = order_info['S']
    stop_price = order_info.get('sp', None)
    working_type = order_info.get('wt')

    first_otoco_order_data = next(iter(globals_instance.OTOCO_orders_data.values()), None)
    if first_otoco_order_data is not None:
        entry_price, lev_position_q = get_positions_info(lev_client, is_main=False)
        child = create_strategy_order(
            client=lev_client,
            order_type=order_type,
            symbol=symbol,
            side=side,
            quantity=lev_position_q,
            stop_price=stop_price,
            price_type=working_type
        )

        order_info['child'] = child

        if mode == "TP":
            first_otoco_order_data['tp_order'] = order_info
        else:
            first_otoco_order_data['sl_order'] = order_info

        return child
    else:
        print("OTOCO_orders_data is empty.")


def handle_otoco_new_order(
        order_info,
        client,
        lev_client,
        main_lev,
        sub_lev
):
    if len(globals_instance.OTOCO_orders_data) == 0:
        globals_instance.OTOCO_orders_data[0] = {
            'main_order': None,
            'tp_order': None,
            'sl_order': None,
            'filled': False
        }

    order_status = order_info['X']
    order_exec_type = order_info['x']
    first_otoco_order_data = next(iter(globals_instance.OTOCO_orders_data.values()), None)

    if order_status == "EXPIRED" or order_exec_type == "EXPIRED":
        globals_instance.is_expired = True
        return

    if order_info['o'] == 'LIMIT' and order_status == 'NEW':
        globals_instance.is_expired = False

        first_otoco_order_data['main_order'] = order_info

        symbol = order_info.get('s')
        side = order_info.get('S')
        order_type = order_info.get('o')
        quantity = order_info.get('q')
        price = order_info.get('p')
        wallet_balance = get_client_balances(tag="Main", client=client)
        order_percentage = calculate_order_percentage(wallet_balance=wallet_balance,
                                                      order_info=order_info,
                                                      main_lev=main_lev)
        # Set last side
        globals_instance.last_side = side
        return handle_normal_new_order(order_info=order_info,
                                       side=side,
                                       price=price,
                                       quantity=quantity,
                                       client=lev_client,
                                       symbol=symbol,
                                       leverage=sub_lev,
                                       order_type=order_type,
                                       order_percentage=order_percentage)

    if order_info['ot'] in ['TAKE_PROFIT_MARKET', 'STOP_MARKET'] and order_info['o'] in ['MARKET']:
        if globals_instance.is_expired:
            return

    if order_info['o'] in ['TAKE_PROFIT_MARKET'] and order_status == 'NEW':
        process_order(order_info, lev_client, "TAKE_PROFIT_MARKET", "TP")

    if order_info['o'] in ['STOP_MARKET'] and order_status == 'NEW':
        process_order(order_info, lev_client, "STOP_MARKET", "SL")
