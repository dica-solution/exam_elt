import time
import logging
logging.basicConfig(level=logging.INFO, filename="logs/import.log")

def log_runtime(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        runtime = end_time - start_time
        logging.info(f'Running {runtime:.15f} seconds: {func.__name__}')
        return result
    return wrapper

def start_info():
    start_time = time.time()
    logging.info(f'Starting program at {time.ctime(start_time)}')

def end_info():
    end_time = time.time()
    logging.info(f'Ending program at {time.ctime(end_time)}\n\n')