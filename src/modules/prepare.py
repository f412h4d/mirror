import os

from .globals import globals_instance
from .orders.cancel import cancel_tp_sl_orders, cancel_all_futures_orders
from .positions import get_positions_info


def clean(client, lev_client):
    os.makedirs('../logs/partial_fills', exist_ok=True)
    with open("../logs/partial_fills/partial_fills.txt", "a") as partial_fills_file:
        partial_fills_file.write("\n__________________\n")

    # Use TimerManager to stop the timer
    globals_instance.timer_manager.stop_timer()

    """Clean up the environment by resetting global variables and canceling orders."""
    # Cancel TP/SL orders
    cancel_tp_sl_orders(client)
    cancel_tp_sl_orders(lev_client)

    # Cancel all futures orders
    cancel_all_futures_orders(lev_client)
    cancel_all_futures_orders(client)

    # Reset global variables
    globals_instance.last_side = ""
    globals_instance.orders_data = {}
    globals_instance.OTOCO_orders_data = {}
    globals_instance.is_expired = False


def conditional_clean(client, lev_client):
    _, position_q = get_positions_info(client=client, is_main=True)

    if float(position_q) == 0:
        print("No Position Is Left, Cleaning Up!")
        clean(client, lev_client)
        return
