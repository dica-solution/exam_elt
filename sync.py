from src.database import get_sessions_from_engines
from sqlalchemy import create_engine
from src.services.sync_ import sync_exam_bank
from src.config.config import settings
# import typer
import datetime
import argparse
import os

    
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
    
def sync_by_text_file(database_destination_url, database_id_mapping_url, file_path):
    if not os.path.exists('exam_ids/exam_ids_synced.txt'):
        with open('exam_ids/exam_ids_synced.txt', 'w'):
            pass

    exam_ids_synced = [line.strip() for line in open('exam_ids/exam_ids_synced.txt', 'r')]
    # if exam_ids_synced:
    #     exam_ids_to_sync = [line.strip() for line in open(file_path, 'r') if line.strip() not in exam_ids_synced]
    exam_ids_to_sync = [line.strip() for line in open(file_path, 'r')]

    ids_synced = []
    errors = []

    engine_sync = create_and_check_engine(database_url=database_destination_url)
    engine_log = create_and_check_engine(database_url=database_id_mapping_url)

    for i in range(len(exam_ids_to_sync)):
        with get_sessions_from_engines(engine_sync, engine_log) as (session_sync, session_log):
            try:
                src_exam_id = exam_ids_to_sync[i]
                exam_id = sync_exam_bank(session_sync, session_log, exam_id=int(src_exam_id))
                if exam_id != 0:
                    ids_synced.append(src_exam_id)
                if exam_id == 0:
                    errors.append(src_exam_id)
                print(f'{exam_id}   {src_exam_id}  {i}')
            except:
                errors.append(src_exam_id)

    if ids_synced:
        ids_synced = [id_synced for id_synced in ids_synced if id_synced not in exam_ids_synced]
        with open(f'exam_ids/exam_ids_synced.txt', 'a') as file:
            for id_synced in ids_synced:
                file.write(str(id_synced) + '\n')
            file.close()

    if errors:
        current_datetime = datetime.datetime.now()
        formatted_datetime = current_datetime.strftime("%Y-%m-%d_%H-%M-%S")
        with open(f'error_logs/sync_error_ids_{formatted_datetime}.txt', 'w') as file:
            for error_id in errors:
                file.write(str(error_id) + '\n')
            file.close()

def sync_by_id(database_destination_url, database_id_mapping_url, id):

    if not os.path.exists('exam_ids/exam_ids_synced.txt'):
        with open('exam_ids/exam_ids_synced.txt', 'w'):
            pass

    exam_ids_synced = [line.strip() for line in open('exam_ids/exam_ids_synced.txt', 'r')]

    ids_synced = []
    errors = []

    engine_sync = create_and_check_engine(database_url=database_destination_url)
    engine_log = create_and_check_engine(database_url=database_id_mapping_url)

    try:
        with get_sessions_from_engines(engine_sync, engine_log) as (session_sync, session_log): 
            exam_id = sync_exam_bank(session_sync, session_log, exam_id=id)
            if exam_id != 0:
                ids_synced.append(id)
            if exam_id == 0:
                errors.append(id)
            print(f'{exam_id}   {id}  {0}')
    except:
        errors.append(id)

    if ids_synced:
        ids_synced = [id_synced for id_synced in ids_synced if str(id_synced) not in exam_ids_synced]
        with open(f'exam_ids/exam_ids_synced.txt', 'a') as file:
            for id_synced in ids_synced:
                file.write(str(id_synced) + '\n')
            file.close()

    if errors:
        current_datetime = datetime.datetime.now()
        formatted_datetime = current_datetime.strftime("%Y-%m-%d_%H-%M-%S")
        with open(f'error_logs/sync_error_ids_{formatted_datetime}.txt', 'w') as file:
            for error_id in errors:
                file.write(str(error_id) + '\n')
            file.close()

def main():
    parser = argparse.ArgumentParser(description="Data syncer with CLI")
    parser.add_argument('--file', type=str, help='Path to file containing IDs to sync')
    parser.add_argument('--id', type=int, help="ID of the exam to sync")
    args = parser.parse_args()

    database_destination_url = f"{settings.database_url}{settings.db_destination}"
    database_id_mapping_url = f"{settings.database_url}{settings.db_id_mapping}"    

    if args.file:
        sync_by_text_file(database_destination_url, database_id_mapping_url, args.file)
    elif args.id:
        sync_by_id(database_destination_url, database_id_mapping_url, args.id)
    else:
        print('Please provide either --file or --id argument.')

    
if __name__=="__main__":
    main()