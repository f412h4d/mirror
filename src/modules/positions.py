def get_positions_info(client, is_main=True):
    positions = client.futures_position_information()

    # Iterate through positions to find the average entry price
    for position in positions:
        symbol = position['symbol']
        if symbol == 'BTCUSDT':
            entry_price = float(position['entryPrice'])
            quantity = abs(float(position['positionAmt']))

            position_log_msg = (
                f"main: {is_main}, "
                f"Entry Price: {entry_price}, "
                f"Amount: {position['positionAmt']}, "
                f"Quantity: {quantity}\n\n")
            print(position_log_msg)

            with open("positions.txt", "a") as position_log_file:
                position_log_file.write(position_log_msg)

            return entry_price, quantity
