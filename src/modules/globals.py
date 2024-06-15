from .timer_manager import TimerManager


class Globals:
    def __init__(self):
        self.orders_data = {}
        self.OTOCO_orders_data = {}
        self.last_tp = {}
        self.last_sl = {}
        self.last_side = ""
        self.is_expired = False
        self.timer_manager = TimerManager()


globals_instance = Globals()
