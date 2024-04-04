from src.database import get_sessions_from_engines
from sqlalchemy import create_engine, Table, MetaData
from src.services.import_ import import_exam_bank
from src.services.sync_ import sync_exam_bank
from src.config.config import settings
from datetime import datetime, timezone
import argparse
import os
import glob
import logging
import time
from tqdm import tqdm


now = datetime.now(timezone.utc)
now_str = now.strftime("%Y-%m-%d %H:%M:%S")
# logging.basicConfig(filename=f'logs/{now_str}.log', level=logging.ERROR)
runtime_logger = logging.getLogger('runtime_logger')
runtime_logger.setLevel(logging.ERROR)
runtime_handler = logging.FileHandler(f'logs/runtime_log/{now_str}.log')
runtime_logger.addHandler(runtime_handler)


def get_latest_runtime(logs_folder_path):
    latest_runtime = max(glob.glob(os.path.join(logs_folder_path, '*.log')), key=os.path.getctime)
    latest_runtime = os.path.basename(latest_runtime).replace('.log', '')
    return latest_runtime

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
    
def check_imported_ids(lst_id_to_import, lst_imported_ids):
    return list(set(lst_id_to_import)-set(lst_imported_ids))

def get_lst_imported_ids(tbl_tracking_logs, session_log):
    return [log[0] for log in session_log.query(tbl_tracking_logs.c.src_exam_id
                                                ).filter(tbl_tracking_logs.c.task_name=='insert').distinct().all()]

def import_exam_by_id(session_import, session_log, exam_id):
    try:
        impored_exam_id = import_exam_bank(session_import, session_log, exam_id=exam_id)
        if impored_exam_id != 0:
            print(f'destination ID: {impored_exam_id:15}, source ID: {exam_id: 10}, task: insert, state: success')
        else:
            print(f'destination ID: {impored_exam_id:15}, source ID: {exam_id: 10}, task: insert, state: fail')
    except Exception as e:
        # logging.error(f'Error import with exam_id: {exam_id}: {e}')
        runtime_logger.error(f'Error import with exam_id: {exam_id}: {e}')
    return None

def import_exam_by_list(session_import, session_log, lst_id_to_import):
    for exam_id in lst_id_to_import:
        import_exam_by_id(session_import, session_log, exam_id)
    return None

def sync_exams(session_import, session_log, lst_id_to_sync, latest_runtime):
    start_time = time.time()
    sync_count = 0
    # for exam_id in tqdm(lst_id_to_sync):
    for exam_id in lst_id_to_sync:
        try:
            synced_exam_id = sync_exam_bank(session_import, session_log, exam_id, latest_runtime)
            if synced_exam_id != 0:
                sync_count += 1
                print(f'destination ID: {synced_exam_id:15}, source ID: {exam_id: 10}, task: sync, state: success')
        except Exception as e:
            runtime_logger.error(f'Error sync with exam_id: {exam_id}: {e}')
    if sync_count != 0:
        run_time = time.time() - start_time
        sync_logger = logging.getLogger('sync_logger')
        sync_logger.setLevel(logging.INFO)
        sync_handler = logging.FileHandler(f'logs/sync_log/{now_str}.log')
        sync_logger.addHandler(sync_handler)
        print(f'Time to sync {sync_count} IDs: {run_time}')
        sync_logger.info(f'Synced {sync_count} IDs in {run_time} seconds')
    else:
        print('No exam to sync!')
    return None
def main():
    parser = argparse.ArgumentParser(description="Data importer with CLI")
    parser.add_argument('--file', type=str, help='Path to file containing IDs to import')
    parser.add_argument('--id', type=int, help="ID of the exam to import")
    parser.add_argument('--sync', action='store_true', help='Use this flag to sync exams')
    args = parser.parse_args()

    database_destination_url = f"{settings.database_url}{settings.db_destination}"
    database_id_mapping_url = f"{settings.database_url}{settings.db_id_mapping}"    

    engine_import = create_and_check_engine(database_url=database_destination_url)
    engine_log = create_and_check_engine(database_url=database_id_mapping_url)

    

    with get_sessions_from_engines(engine_import, engine_log) as (session_import, session_log):
        metadata = MetaData()
        metadata.reflect(engine_log)
        tbl_tracking_logs = Table('tracking_logs', metadata, autoload=True)
        lst_imported_ids = get_lst_imported_ids(tbl_tracking_logs, session_log)
        print(f'{len(lst_imported_ids)} IDs have been imported in db!')
        
        if args.file:
            lst_id_to_import = [int(line.strip()) for line in open(args.file, 'r')]
            lst_id_to_import = check_imported_ids(lst_id_to_import, lst_imported_ids)
            print(f'{len(lst_id_to_import)} IDs are ready to import!')
            import_exam_by_list(session_import, session_log, lst_id_to_import)
        elif args.id:
            if args.id not in lst_imported_ids:
                import_exam_by_id(session_import, session_log, args.id)
            else:
                print(f'ID: {args.id} has been already imported!')
        else:
            print('No import action to perform')


        if args.sync:
            # idx = lst_imported_ids.index(1268)
            # lst_id_to_sync = lst_imported_ids[idx: idx+1]
            lst_id_to_sync = lst_imported_ids
            latest_runtime = get_latest_runtime('logs/sync_log')
            print('Syncing exams...')
            sync_exams(session_import, session_log, lst_id_to_sync, latest_runtime)
        else:
            print('No sync action to perform')



if __name__ == '__main__':
    main()        

