from src.services.import_course import ImportCourse
from src.config.config import get_settings
from src.services.logger_config import setup_logger
from sqlalchemy import create_engine
from src.database import get_sessions_from_engines
import argparse

# logger = setup_logger()

def main():
    parser = argparse.ArgumentParser(description='Import course by id')
    parser.add_argument('--course_id', type=int, help='Course id')
    args = parser.parse_args()

    settings = get_settings()
    import_db_url = f"{settings.database_url}{settings.db_destination}"
    log_db_url = f"{settings.database_url}{settings.db_id_mapping}"
    import_engine = create_engine(import_db_url)
    log_engine = create_engine(log_db_url)
    with get_sessions_from_engines(import_engine, log_engine) as (session_import, session_log):
        parser = ImportCourse(session_import, session_log, settings)
        parser.import_course(course_id=args.course_id, is_free=False)

if __name__ == '__main__':
    main()