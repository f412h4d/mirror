from src.modules.log import save_dict_to_json


def create_sl_order(client, sl_info_input):
    try:
        response = client.futures_create_order(
            symbol=sl_info_input['symbol'],
            side=sl_info_input['side'],
            type='STOP_MARKET',
            quantity=sl_info_input['quantity'],
            stopPrice=sl_info_input['stop_price'],
            reduceOnly='TRUE',
            priceProtect=('TRUE'
                          if sl_info_input['working_type'] == 'MARK_PRICE'
                          else 'FALSE'),
            workingType=sl_info_input['working_type'],
            newClientOrderId=f"custom_sl_{sl_info_input['id']}"
        )
        print("SL order created:", response['orderId'])
        return response
    except Exception as e:
        print("Error in creating SL order:", e)
        return None


def custom_sl(lev_client, order_info, otoco_orders_data, new_quantity, sl_info):
    new_sl_info = sl_info
    new_sl_info['quantity'] = new_quantity

    save_dict_to_json(directory="custom_orders", filename=f"SL_{sl_info['id']}", dictionary=new_sl_info)

    first_otoco_order_data = next(iter(otoco_orders_data.values()), None)
    if first_otoco_order_data is not None:
        child = create_sl_order(client=lev_client, sl_info_input=new_sl_info)

        order_info['child'] = child
        first_otoco_order_data['sl_order'] = order_info
        return otoco_orders_data
    else:
        print(" ---- OTOCO_orders_data is empty.")
