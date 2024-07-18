import os
import logging
from datetime import datetime, timedelta, timezone
from src.config.config import get_settings

settings = get_settings()

def setup_logger():
    now = datetime.now(timezone(timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S")
    log_path = settings.import_course_log_dir
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    log_file = os.path.join(log_path, f"{now}.log")
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    
    return logging.getLogger(__name__)
