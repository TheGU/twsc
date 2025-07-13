# Setup default logging configuration for the application
import logging

def setup_logging(
        name=None, 
        with_time: bool = False, 
        with_name: bool = True,
        level: str = "INFO", 
        ibapi_level: str = "WARNING"
    ) -> logging.Logger:
    """
    Set up the logging configuration for the application.
    
    Args:
        level (str): The logging level to set. Default is "INFO".
    """

    ibapi_log = logging.getLogger("ibapi")
    ibapi_log.setLevel(getattr(logging, ibapi_level.upper(), logging.WARNING))

    # exclude packagge name from the log messages
    
    if with_time:
        format = '[%(asctime)s] '
    else:
        format = ''

    format += '%(levelname)-7s '

    if with_name:
        format += '| %(name)-25s '

    format += '| %(message)s'

    logging.basicConfig(
        format=format,
        level=getattr(logging, level.upper(), logging.INFO)
    )
    logger = logging.getLogger(name or __name__)
    logger.info("Logging is set up with level: %s", level)

    return logger
