import time
import logging
logging.basicConfig(level=logging.INFO, filename="logs/import.log")

def log_runtime(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        runtime = end_time - start_time
        logging.info(f'Running {func.__name__} took {runtime} seconds.')
        return result
    return wrapper