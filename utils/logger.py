import sys
from loguru import logger

class LoggerConfig:
    def __init__(self, log_level="INFO"):
        self.log_level = log_level

        logger.remove()
        logger.add(
            sink=sys.stderr,
            level=self.log_level,
        )

    @staticmethod
    def get_logger():
        return logger