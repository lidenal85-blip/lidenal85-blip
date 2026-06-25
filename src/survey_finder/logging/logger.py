import logging
import structlog


def init_logger():
    logging.basicConfig(level=logging.INFO)

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ]
    )

    return structlog.get_logger()
