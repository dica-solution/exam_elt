from src.models.exam_bank_models import TrackingLogs
from src.services.import_ import import_exam_bank
from src.services.logger_config import setup_logger

logger = setup_logger()

class ImportExam:
    def __init__(self, session_import, session_log, settings):
        self.session_import = session_import
        self.session_log = session_log
        self.settings = settings

    def _get_imported_src_exam_id_list(self):
        distinct_impoted_exam_id = (
            self.session_log.query(TrackingLogs.src_exam_id)
            .distinct()
            .all()
        )
        return [log[0] for log in distinct_impoted_exam_id]
    
    def _get_imported_exam_id(self, exam_id):
        latest_log = (
            self.session_log.query(TrackingLogs)
            .filter(TrackingLogs.src_exam_id == exam_id)
            .order_by(TrackingLogs.timestamp.desc())
            .first()
        )
        return latest_log.des_exam_id if latest_log else None



    def import_exam(self, exam_id):
        imported_src_exam_id_list = self._get_imported_src_exam_id_list()
        if exam_id in imported_src_exam_id_list:
            logger.info(f'exam_id: {exam_id} has been already imported!')
            imported_dest_exam_id = self._get_imported_exam_id(exam_id)
            if imported_dest_exam_id:
                return imported_dest_exam_id
        else:
            imported_des_exam_id, error_info = import_exam_bank(self.session_import, self.session_log, exam_id)
            logger.info(f"Imported exam {exam_id}")
            if imported_des_exam_id != 0:
                return imported_des_exam_id
        return None