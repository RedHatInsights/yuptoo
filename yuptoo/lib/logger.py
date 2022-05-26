import logging

from yuptoo.lib.config import LOG_LEVEL

request_obj = None
logger = None


def initialize_logging():
    logging.basicConfig(
            level=LOG_LEVEL,
            format="%(threadName)s %(levelname)s %(name)s - %(message)s",
    )


def set_logger_name(name):
    global logger
    logger = logging.getLogger(name)


def set_request_object(req_obj):
    global request_obj
    request_obj = req_obj
    log_str = f"for account={request_obj['account']} org_id={request_obj['org_id']} " \
              f"and request_id={request_obj['request_id']}."
    request_obj['log_string'] = "{msg} " + log_str


def info(msg):
    if request_obj:
        logger.info(request_obj['log_string'].format(msg=msg))
    else:
        logger.info(msg)


def error(msg):
    if request_obj:
        logger.error(request_obj['log_string'].format(msg=msg))
    else:
        logger.error(msg)


def warning(msg):
    if request_obj:
        logger.warning(request_obj['log_string'].format(msg=msg))
    else:
        logger.warning(msg)


def debug(msg):
    if request_obj:
        logger.debug(request_obj['log_string'].format(msg=msg))
    else:
        logger.debug(msg)
