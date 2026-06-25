class Metrics:
    def __init__(self):
        self.data = {
            "cycles_started": 0,
            "cycles_failed": 0,
            "cycles_success": 0,
            "adapter_failures": 0,
            "dlq_items": 0,
            "circuit_open": 0,
            "notifications_sent": 0
        }

    def inc(self, key: str):
        if key in self.data:
            self.data[key] += 1

    def snapshot(self):
        return dict(self.data)
