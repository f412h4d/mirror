import json
from pathlib import Path


def generate_and_log_order_info(order_event):
    """
    Generate detailed order event information as a multi-line string, log it to a file, and print it.
    Includes handling for keys not explicitly given a custom tag.
    """
    log_lines = "\nOrder Event Details:\n"
    log_lines += "--------------------\n"
    log_lines += f"Event Type: {order_event.get('e', 'N/A')}\n"
    log_lines += f"Event Time: {order_event.get('E', 'N/A')}\n"

    order_info = order_event.get('o', {})
    if order_info:
        # Custom-tagged information
        custom_tags = {
            's': "Symbol",
            'c': "Client Order ID",
            'i': "Order ID",
            'p': "Order Price",
            'q': "Order Quantity",
            'X': "Order Status",
            'x': "Execution Type",
            'S': "Order Side",
            'o': "Order Type",
            'f': "Time in Force",
            'sp': "Stop Price",
            'T': "Order Create Time",
            't': "Order Update Time",
            'R': "Reduce Only",
            'po': "Post Only",
            'e': "Completed Trade Volume",
            'ec': "Completed Trade Amount",
        }

        log_lines += "\nOrder Information:\n"
        for key, label in custom_tags.items():
            if key in order_info:
                if key == 'X' and order_info[key] == "PARTIALLY_FILLED":
                    continue
                log_lines += f"{label}: {order_info[key]}\n"

        # Handle unspecified keys
        unspecified_keys = set(order_info.keys()) - set(custom_tags.keys())
        if unspecified_keys:
            log_lines += "\nOther Information:\n"
            for key in unspecified_keys:
                # Convert key names to more human-readable form
                readable_key = key.replace('_', ' ').capitalize()
                log_lines += f"{readable_key}: {order_info[key]}\n"
    else:
        log_lines += "No detailed order information available.\n"

    # Print to console
    print(log_lines)

    # Append to log.txt file
    with open("log.txt", "a") as log_file:
        log_file.write(log_lines)


def save_dict_to_json(directory, filename, dictionary):
    base = Path(directory)
    base.mkdir(exist_ok=True)
    jsonpath = base / filename
    jsonpath.write_text(json.dumps(dictionary, indent=4))
