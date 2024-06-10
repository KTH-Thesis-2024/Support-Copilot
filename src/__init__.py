import logging
import os

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

log_format = "%(asctime)s - %(module)s - %(levelname)s - %(message)s"
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter(log_format))

logger.addHandler(stream_handler)
