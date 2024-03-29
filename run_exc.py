import logging
from logging.handlers import RotatingFileHandler
from sqlalchemy import create_engine, Table, distinct, MetaData
from sqlalchemy.orm import sessionmaker
from src.config.config import settings
from src.database import get_sessions_from_engines
from src.models.exam_bank_models import TrackingLogs
from src.services.import_ import import_exam_bank
from src.services.sync_ import sync_exam_bank
from datetime import datetime


def create_and_check_engine(database_url, echo=False, pool_size=50, max_overflow=0):
    try:
        engine = create_engine(
            database_url, echo=echo,
            pool_size=pool_size,
            max_overflow=max_overflow,
        )
        with engine.connect() as connection:
            print("Connection successful!")   
            return engine
    except Exception as e:
        print(f"Connection failed: {e}")
        return None 

def check_changes(updated_time):
    last_run_time = open('logs/log_runs.log', 'r').readlines()[-1].strip()
    last_run_time = datetime.strptime(last_run_time, '%Y-%m-%d %H:%M:%S.%f')
    if last_run_time < updated_time:
        return True
    else:
        return False
    
# def delete_exam(deleted_exam_id, session_import, session_log, tbl_exam, tbl_tracking_logs):
    try:
        des_exam_id = session_log.query(distinct(tbl_tracking_logs.c.des_exam_id)).filter(tbl_tracking_logs.c.src_exam_id == deleted_exam_id).all()
        session_import.query(tbl_exam).filter(tbl_exam.c.id == des_exam_id).delete()
        log = TrackingLogs(    
                    src_exam_id = deleted_exam_id,
                    src_quiz_object_type = None,
                    src_quiz_question_id = None,
                    src_quiz_question_group_id = None,
                    des_exam_id = des_exam_id,
                    des_quiz_question_id = None,
                    des_quiz_question_group_id = None,
                    task_name = 'delete', # "insert", "update" or "delete"
                    order = 0,
                )
        session_log.add(log)
        session_log.commit()
    except Exception as e:
        print(f"Error: {e}")

def count_number_quizzes(exam_id, session_source, tbl_paper_exams_components, tbl_components_exam_grouped_essays_components, 
                         tbl_components_exam_group_entry_texts, tbl_components_exam_group_quiz_true_falses):
    quizzes = session_source.query(tbl_paper_exams_components).filter(tbl_paper_exams_components.c.entity_id == exam_id).all()
    count = 0
    for quiz in quizzes:
        if quiz.component_type in ['exam.single-quiz', 'exam.single-essay', 'exam.single-text-entry']:
            count += 1
        if quiz.component_type == 'exam.grouped-quiz':
            count += session_source.query(tbl_components_exam_grouped_essays_components).filter(tbl_components_exam_grouped_essays_components.c.entity_id == quiz.component_id).count()
        if quiz.component_type == 'exam.grouped-essay':
            count += session_source.query(tbl_components_exam_grouped_essays_components).filter(tbl_components_exam_grouped_essays_components.c.entity_id == quiz.component_id).count()
        if quiz.component_type == 'exam.grouped-text-entry':
            count += session_source.query(tbl_components_exam_group_entry_texts).filter(tbl_components_exam_group_entry_texts.c.entity_id == quiz.component_id).count()
        if quiz.component_type == 'exam.group-quiz-true-false':
            count += session_source.query(tbl_components_exam_group_quiz_true_falses).filter(tbl_components_exam_group_quiz_true_falses.c.entity_id == quiz.component_id).count()
    return count

def import_exam(exam_id, session_import, session_log):
    task = 'import'
    try:
        des_exam_id = import_exam_bank(session_import, session_log, exam_id=exam_id)
        print(f'task: {task:10}, destination ID: {des_exam_id:15}, source ID{exam_id: 10}, state: success')
    except Exception as e:
        # print(f"Error: {e}")
        print(f'task: {task:10}, destination ID: {0:15}, source ID{exam_id: 10}, state: fail')

def sync_exam(sync_exam_id, session_import, session_log, session_source, tbl_tracking_logs, tbl_exam, tbl_paper_exams_components, 
              tbl_components_exam_grouped_essays_components, tbl_components_exam_group_entry_texts, tbl_components_exam_group_quiz_true_falses):
    task = 'sync'
    try:
        # Get number of imported quizzes
        des_exam_id = session_log.query(tbl_tracking_logs).filter(tbl_tracking_logs.c.src_exam_id == sync_exam_id).first().des_exam_id
        num_quizzes_imported = session_import.query(tbl_exam).filter(tbl_exam.c.id == des_exam_id).first().num_quizzes

        # Get number of quizzes in source
        num_quizzes_source = count_number_quizzes(sync_exam_id, session_source, tbl_paper_exams_components, tbl_components_exam_grouped_essays_components, 
                                                  tbl_components_exam_group_entry_texts, tbl_components_exam_group_quiz_true_falses)
        
        
        if num_quizzes_imported == num_quizzes_source:
            try:
                des_exam_id = sync_exam_bank(session_import, session_log, sync_exam_id)
                print(f'task: {task:10}, destination ID: {des_exam_id:15}, source ID{sync_exam_id: 10}, state: success')
            except Exception as e:
                print(f'task: {task:10}, destination ID: {0:15}, source ID{sync_exam_id: 10}, state: fail')
        else:

            pass
        print("Hello")
    except Exception as e:
        print(f"Error: {e}")
    return

def main():
    database_source_url = f"{settings.database_url}{settings.db_paper_exams}"
    database_destination_url = f"{settings.database_url}{settings.db_destination}"
    database_id_mapping_url = f"{settings.database_url}{settings.db_id_mapping}"  
    engine_source = create_and_check_engine(database_url=database_source_url)
    engine_import = create_and_check_engine(database_url=database_destination_url)
    engine_log = create_and_check_engine(database_url=database_id_mapping_url)
    metadata_source = MetaData()
    metadata_source.reflect(bind=engine_source)
    metadata_import = MetaData()
    metadata_import.reflect(bind=engine_import)
    metadata_log = MetaData()
    metadata_log.reflect(bind=engine_log)

    # Tables
    tbl_tracking_logs = Table('tracking_logs', metadata_log, autoload_with=engine_log)
    tbl_paper_exams = Table('paper_exams', metadata_source, autoload_with=engine_source)
    tbl_paper_exams_components = Table("paper_exams_components", metadata_source, autoload_with=engine_source)
    tbl_exam = Table('exam', metadata_import, autoload_with=engine_import)
    tbl_paper_exams_grade_links = Table("paper_exams_grade_links", metadata_source, autoload_with=engine_source)
    tbl_paper_exams_subject_links = Table("paper_exams_subject_links", metadata_source, autoload_with=engine_source)
    tbl_paper_exams_school_links = Table("paper_exams_school_links", metadata_source, autoload_with=engine_source)
    tbl_components_exam_single_quizs = Table("components_exam_single_quizs", metadata_source, autoload_with=engine_source)
    tbl_components_exam_single_essays = Table("components_exam_single_essays", metadata_source, autoload_with=engine_source)
    tbl_components_exam_grouped_quizs_components = Table("components_exam_grouped_quizs_components", metadata_source, autoload_with=engine_source)
    tbl_components_exam_grouped_quizs = Table("components_exam_grouped_quizs", metadata_source, autoload_with=engine_source)
    tbl_components_exam_grouped_essays_components = Table("components_exam_grouped_essays_components", metadata_source, autoload_with=engine_source)
    tbl_components_exam_grouped_essays = Table("components_exam_grouped_essays", metadata_source, autoload_with=engine_source)
    tbl_components_exam_group_quiz_true_falses_components = Table("components_exam_group_quiz_true_falses_components", metadata_source, autoload_with=engine_source)
    tbl_components_exam_group_quiz_true_falses = Table("components_exam_group_quiz_true_falses", metadata_source, autoload_with=engine_source)
    tbl_components_exam_single_quiz_true_falses = Table("components_exam_single_quiz_true_falses", metadata_source, autoload_with=engine_source)
    tbl_components_exam_group_entry_texts_components = Table("components_exam_group_entry_texts_components", metadata_source, autoload_with=engine_source)
    tbl_components_exam_group_entry_texts = Table("components_exam_group_entry_texts", metadata_source, autoload_with=engine_source)
    tbl_components_exam_single_text_entries = Table("components_exam_single_text_entries", metadata_source, autoload_with=engine_source)
    tbl_files_related_morphs = Table("files_related_morphs", metadata_source, autoload_with=engine_source)
    tbl_files = Table("files", metadata_source, autoload_with=engine_source)
    tbl_grades = Table("grades", metadata_source, autoload_with=engine_source)
    tbl_subjects = Table("subjects", metadata_source, autoload_with=engine_source)
    tbl_schools = Table("schools", metadata_source, autoload_with=engine_source)

    try:
        with get_sessions_from_engines(engine_source, engine_import, engine_log) as (session_source, session_import, session_log):
            # Get current IDs already imported in db
            exam_ids_imported = session_log.query(distinct(tbl_tracking_logs.c.src_exam_id)).all()
            exam_ids_imported = [x[0] for x in exam_ids_imported]
            
            # Get IDs from source
            exam_ids_from_source = session_source.query(tbl_paper_exams.c.id).all()
            exam_ids_from_source = [x[0] for x in exam_ids_from_source]

            # Check for deleted IDs -> delete that IDs in destination db
            if len(exam_ids_from_source) < len(exam_ids_imported):
                exam_ids_deleted = list(set(exam_ids_imported) - set(exam_ids_from_source))
                # for exam_id in exam_ids_deleted:
                #     delete_exam(exam_id)
            
            else:
                for exam_id in exam_ids_from_source:
                    # Import exam if not in destination db
                    if exam_id not in exam_ids_imported:
                        # import_exam(exam_id, session_import, session_log)
                        pass
                    # Check updated time and sync if necessary    
                    updated_time = session_source.query(tbl_paper_exams).filter(tbl_paper_exams.c.id == exam_id).first().updated_at             
                    if check_changes(updated_time):
                        sync_exam(exam_id, session_import, session_log, session_source, tbl_tracking_logs)
                    else:
                        continue
                


    except Exception as e:
        print(f"Error: {e}")
    # Log run
    logger = logging.getLogger('my_logger')
    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler('logs/log_runs.log', maxBytes=2000, backupCount=5)
    logger.addHandler(handler)
    logger.info(datetime.now())

if __name__ == "__main__":
    main()
