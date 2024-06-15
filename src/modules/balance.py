def print_balance_details(balance):
    print("Balance Details:")
    keys_of_interest = ['walletBalance', 'unrealizedProfit', 'marginBalance']
    for key in keys_of_interest:
        if key in balance:
            print(f"{key}: {balance[key]}")


def print_all_balance_details(balance):
    print("Balance Details:")
    for key, value in balance.items():
        print(f"{key}: {value}")


def get_client_balances(tag, client):
    print(f"{tag} Balances:")
    futures_account_info = client.futures_account()
    balances = futures_account_info['assets']
    for balance in balances:
        is_positive = (float(balance['walletBalance']) > 0.0
                       or
                       float(balance['unrealizedProfit']) > 0.0)
        if is_positive:
            print_all_balance_details(balance)
            return float(balance['marginBalance'])


def calculate_margin_and_quantity(balance, percentage, leverage, price):
    """
    Calculate margin and new quantity for futures order.

    Args:
    - balance (float): The balance used for the calculation.
    - percentage (float): The percentage of the balance to be used.
    - leverage (int): The leverage applied to the order.
    - price (float): The price of the asset.

    Returns:
    - tuple: Contains calculated margin and new quantity.
    """
    margin = round((balance * percentage * leverage * 0.95), 3)
    new_quantity = round(margin / float(price), 3)

    # Prepare the log message
    log_message = (
        f"Balance: {balance}, Percentage: {percentage}, Leverage: {leverage}, Price: {price}, "
        f"Margin: {margin}, New Quantity: {new_quantity}\n"
        f"----------------------------------------------\n\n"
    )

    # Append the log message to the file
    with open("q_log.txt", "a") as log_file:
        log_file.write(log_message)

    return margin, new_quantity
