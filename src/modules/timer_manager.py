from threading import Event
from typing import Any, Callable

from .timer import start_timer


class TimerManager:
    def __init__(self):
        self.current_stop_event = None
        self.current_thread = None

    def start_new_timer(self, seconds: int, callback: Callable, *args: Any, **kwargs: Any) -> None:
        """Stops any existing timer and starts a new one."""
        if self.current_stop_event is not None:
            self.current_stop_event.set()
            if self.current_thread is not None:
                self.current_thread.join()

        self.current_stop_event = Event()
        self.current_thread = start_timer(seconds, self.current_stop_event, callback, *args, **kwargs)

    def stop_timer(self):
        """Stops the current timer if it is running."""
        if self.current_stop_event is not None:
            self.current_stop_event.set()
            if self.current_thread is not None:
                self.current_thread.join()
