from survey_finder.execution.orchestrator.controller import ExecutionController

def pipeline(cycle_id: str):
    print(f"[cycle={cycle_id}] execution pipeline running")


def run():
    controller = ExecutionController()
    controller.run_cycle(pipeline)


if __name__ == "__main__":
    run()
