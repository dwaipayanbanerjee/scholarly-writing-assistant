# cost_tracker.py

from threading import Lock


class CostTracker:
    def __init__(self):
        self._total_cost = 0.0
        self._lock = Lock()

    def add_cost(self, cost: float):
        with self._lock:
            self._total_cost += cost

    def get_total_cost(self) -> float:
        with self._lock:
            return self._total_cost


cost_tracker = CostTracker()
