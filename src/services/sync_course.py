from src.services.processor import Processor
from src.services.utils import Utils
from src.services.logger_config import setup_logger
from src.models.exam_bank_models import Course

from typing import List, Dict, Any

logger = setup_logger()

class SyncCourse:
    def __init__(self, session_import, session_log, settings):
        self.session_import = session_import
        # self.session_log = session_log
        # self.settings = settings
        self.processor = Processor(session_import, settings)
        self.utils = Utils(session_import, session_log, settings)

    def sync_course(self, original_course_id: int, is_free: bool=False):
        print(f"Start sync course {original_course_id} ...")

        self.utils.update_course(original_course_id, is_free)

        logger.info(f"Synced course {original_course_id}")
        print(f"Synced course {original_course_id}")
