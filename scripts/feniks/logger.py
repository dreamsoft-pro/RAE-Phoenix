import logging
import sys

def setup_logger():
    """
    Configures and returns a logger for the application.
    - Logs INFO and higher to stdout.
    - Uses a clear, consistent format.
    """
    logger = logging.getLogger("feniks_kb")
    logger.setLevel(logging.INFO)

    # Avoid adding duplicate handlers if this function is called multiple times
    if logger.hasHandlers():
        return logger

    # Configure handler
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] - %(message)s", 
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

# Create a single, importable instance of the logger
log = setup_logger()
