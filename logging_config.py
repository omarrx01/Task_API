import logging


def setup_logger():
    logging.basicConfig(level=logging.INFO)

    logger = logging.getLogger("task_api")

    return logger