from src.modules.log import save_dict_to_json


def create_tp_order(client, tp_info_input):
    try:
        response = client.futures_create_order(
            symbol=tp_info_input['symbol'],
            side=tp_info_input['side'],
            type='TAKE_PROFIT_MARKET',
            quantity=tp_info_input['quantity'],
            stopPrice=tp_info_input['stop_price'],
            reduceOnly='TRUE',
            priceProtect=('TRUE'
                          if tp_info_input['working_type'] == 'MARK_PRICE'
                          else 'FALSE'),
            workingType=tp_info_input['working_type'],
            newClientOrderId=f"custom_tp_{tp_info_input['id']}"
        )
        print("TP order created:", response['orderId'])
        return response
    except Exception as e:
        print("Error in creating TP order:", e)
        return None


def custom_tp(
        lev_client,
        order_info,
        otoco_orders_data,
        new_quantity,
        tp_info,
        # entry_price=-1
):
    new_tp_info = tp_info
    new_tp_info['quantity'] = new_quantity

    # temp change due to release

    # side = order_info['S']
    # new_tp_info['stop_price'] = -1
    # if side == 'BUY':
    #     new_tp_info['stop_price'] = round(entry_price * 1.009, 1)
    # elif side == 'SELL':
    #     new_tp_info['stop_price'] = round(entry_price * 0.991, 1)

    save_dict_to_json(directory="custom_orders", filename=f"TP_{tp_info['id']}", dictionary=new_tp_info)

    first_otoco_order_data = next(iter(otoco_orders_data.values()), None)
    if first_otoco_order_data is not None:
        child = create_tp_order(client=lev_client, tp_info_input=new_tp_info)

        order_info['child'] = child
        first_otoco_order_data['tp_order'] = order_info
        return otoco_orders_data
    else:
        print(" ---- OTOCO_orders_data is empty.")
