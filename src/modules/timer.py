from threading import Thread, Event
from time import sleep
from typing import Any, Callable


def count_down(seconds: int, stop_event: Event, callback: Callable, *args: Any, **kwargs: Any) -> None:
    """Function with the timer."""
    for _ in range(seconds):
        if stop_event.is_set():
            print("Timer stopped prematurely")
            return
        sleep(1)
    if not stop_event.is_set():
        callback(*args, **kwargs)


def start_timer(seconds: int, stop_event: Event, callback: Callable, *args: Any, **kwargs: Any) -> Thread:
    """Starts a timer on a separate thread."""
    my_thread = Thread(target=count_down, args=(seconds, stop_event, callback, *args), kwargs=kwargs)
    my_thread.start()
    return my_thread
