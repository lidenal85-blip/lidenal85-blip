from survey_finder.runtime.metrics import Metrics
from survey_finder.runtime.replay_store import ReplayStore
from survey_finder.runtime.trace import TraceContext

class Orchestrator:
    def __init__(self, adapters, buffer, idempotency, filter_engine, dispatcher, logger=None):
        self.adapters = adapters
        self.buffer = buffer
        self.idempotency = idempotency
        self.filter_engine = filter_engine
        self.dispatcher = dispatcher

        self.metrics = Metrics()
        self.replay = ReplayStore()
        self.logger = logger

    def run_cycle(self, cycle, profile):
        trace = TraceContext(cycle_id=cycle.cycle_id)
        self.metrics.inc("cycles_started")

        self.replay.record(cycle.cycle_id, {
            "event": "cycle_start",
            "trace_id": trace.trace_id
        })

        all_surveys = []

        for adapter in self.adapters:
            try:
                surveys = adapter.fetch(cycle)
                all_surveys.extend(surveys)
            except Exception as e:
                self.metrics.inc("adapter_failures")
                self.replay.record(cycle.cycle_id, {
                    "event": "adapter_failure",
                    "error": str(e)
                })
                continue

        for survey in all_surveys:
            key = f"{survey.source}:{survey.id}"

            if not self.idempotency.check_and_mark(key):
                continue

            if not self.filter_engine.allow(survey, profile):
                continue

            self.buffer.push(survey)

            self.replay.record(cycle.cycle_id, {
                "event": "survey_accepted",
                "survey_id": survey.id
            })

        self._drain_buffer(cycle)

        self.metrics.inc("cycles_success")
        self.replay.record(cycle.cycle_id, {
            "event": "cycle_complete"
        })

    def _drain_buffer(self, cycle):
        while True:
            event = self.buffer.pop()
            if not event:
                break

            try:
                self.dispatcher.send(event)
                self.metrics.inc("notifications_sent")
            except Exception as e:
                self.metrics.inc("cycles_failed")
                self.replay.record(cycle.cycle_id, {
                    "event": "dispatch_failure",
                    "error": str(e)
                })
