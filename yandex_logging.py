import logging
from pythonjsonlogger import jsonlogger


class YandexFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record["logger"] = record.name
        log_record["level"] = record.levelname.replace("WARNING", "WARN").replace(
            "CRITICAL", "FATAL"
        )
        del log_record["levelname"]
        del log_record["name"]

    def format(self, record):
        return super().format(record).replace("\n", "\r")


yandex_handler = logging.StreamHandler()
yandex_handler.setFormatter(YandexFormatter("[%(levelname)s] %(name)s: %(message)s"))

root_logger = logging.getLogger()
root_logger.addHandler(yandex_handler)
