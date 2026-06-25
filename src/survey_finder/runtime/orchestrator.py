from survey_finder.runtime.metrics import Metrics

class Orchestrator:
    def __init__(self, adapters, buffer, idempotency, filter_engine, dispatcher, shutdown=None):
        self.adapters = adapters
        self.buffer = buffer
        self.idempotency = idempotency
        self.filter_engine = filter_engine
        self.dispatcher = dispatcher
        self.shutdown = shutdown

        self.metrics = Metrics()

    def run_cycle(self, cycle, profile):
        self.metrics.inc("cycles_started")

        all_surveys = []

        for adapter in self.adapters:
            if self.shutdown and self.shutdown.is_shutdown():
                break

            try:
                all_surveys.extend(adapter.fetch(cycle))
            except Exception:
                self.metrics.inc("adapter_failures")
                continue

        for survey in all_surveys:
            if self.shutdown and self.shutdown.is_shutdown():
                break

            key = f"{survey.source}:{survey.id}"
            if not self.idempotency.check_and_mark(key):
                continue

            if not self.filter_engine.allow(survey, profile):
                continue

            try:
                self.buffer.push(survey)
            except RuntimeError as e:
                # BACKPRESSURE -> propagate shutdown signal
                if str(e) == "BACKPRESSURE_LIMIT_REACHED":
                    if self.shutdown:
                        self.shutdown.initiate_shutdown()
                break

        self._drain()

        self.metrics.inc("cycles_success")

    def _drain(self):
        while True:
            event = self.buffer.pop()
            if not event:
                break

            try:
                self.dispatcher.send(event)
                self.metrics.inc("notifications_sent")
            except Exception:
                self.metrics.inc("cycles_failed")
                continue
