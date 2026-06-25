class Metrics:
    def __init__(self):
        self.counters = {
            "dlq_items": 0,
            "adapter_failures": 0,
            "circuit_open": 0
        }

    def inc(self, key: str):
        if key in self.counters:
            self.counters[key] += 1

    def snapshot(self):
        return dict(self.counters)
