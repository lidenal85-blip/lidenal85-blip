import logging
import json
import sys

class Logger:
    def __init__(self):
        self.logger = logging.getLogger("survey-finder")
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        self.logger.addHandler(handler)

    def info(self, msg: str, **kwargs):
        self.logger.info(json.dumps({"level": "info", "msg": msg, **kwargs}))

    def error(self, msg: str, **kwargs):
        self.logger.error(json.dumps({"level": "error", "msg": msg, **kwargs}))
