import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def create_log(options):
    formatter = logging.Formatter("%(asctime)s;%(levelname)s; %(message)s ")

    stream_handler = logging.StreamHandler()
    # handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(formatter)

    logger = logging.getLogger("log")
    if options.verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    logger.addHandler(stream_handler)
    return logger


def create_event_log(options):
    Path(options.event_log).parent.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter(
        "%(asctime)s %(message)s", "%Y-%m-%d %H:%M:%S")

    file_handler = RotatingFileHandler(options.event_log, mode='a',
                                       maxBytes=options.event_log_max_bytes,
                                       backupCount=options.event_log_backup_count,  # noqa: E501
                                       encoding=None, delay=0)

#    file_handler = logging.FileHandler(options.event_log)
    file_handler.setFormatter(formatter)

    logger = logging.getLogger("event_log")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    return logger
