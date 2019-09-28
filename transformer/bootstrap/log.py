from logging import basicConfig
from logging.config import dictConfig
import logging


def setup_logging(logging_config=None, default_level=logging.INFO):
    """Setup logging configuration

    """
    if logging_config is None:
        print('Using basicConfig for logger, could not open file')
        basicConfig(level=default_level)
    else:
        dictConfig(logging_config)
