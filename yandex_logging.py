import logging

def init_logging(level = logging.INFO):
    # Enable logging
    logger = logging.getLogger(__name__)
    logging.getLogger().setLevel(level)
    root_handler = logging.getLogger().handlers[0]
    root_handler.setFormatter(
        YandexFormatter("[%(levelname)s] %(name)s: %(message)s")
    )
    logger.debug("Starting the main module")
    return logger

class YandexFormatter(logging.Formatter):
    def format(self, record):
        return super().format(record).replace("\n", "\r")

logger = init_logging()
