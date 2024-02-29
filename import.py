from src.database import get_sessions_from_engines
from sqlalchemy import create_engine
from src.services.import_ import import_exam_bank
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
    
def import_by_text_file(database_destination_url, database_id_mapping_url, file_path):
    if not os.path.exists('exam_ids/exam_ids_imported.txt'):
        with open('exam_ids/exam_ids_imported.txt', 'w'):
            pass

    exam_ids_imported = [line.strip() for line in open('exam_ids/exam_ids_imported.txt', 'r')]
    if exam_ids_imported:
        exam_ids_to_import = [line.strip() for line in open(file_path, 'r') if line.strip() not in exam_ids_imported]
    exam_ids_to_import = [line.strip() for line in open(file_path, 'r')]

    ids_imported = []
    errors = []

    engine_import = create_and_check_engine(database_url=database_destination_url)
    engine_log = create_and_check_engine(database_url=database_id_mapping_url)

    for i in range(len(exam_ids_to_import)):
        with get_sessions_from_engines(engine_import, engine_log) as (session_import, session_log):
            try:
                src_exam_id = exam_ids_to_import[i]
                exam_id = import_exam_bank(session_import, session_log, exam_id=int(src_exam_id))
                if exam_id != 0:
                    ids_imported.append(src_exam_id)
                if exam_id == 0:
                    errors.append(src_exam_id)
                print(f'{exam_id}   {src_exam_id}  {i}')
            except:
                errors.append(src_exam_id)

    if ids_imported:
        ids_imported = [id_imported for id_imported in ids_imported if id_imported not in exam_ids_imported]
        with open(f'exam_ids/exam_ids_imported.txt', 'a') as file:
            for id_imported in ids_imported:
                file.write(str(id_imported) + '\n')
            file.close()

    if errors:
        current_datetime = datetime.datetime.now()
        formatted_datetime = current_datetime.strftime("%Y-%m-%d_%H-%M-%S")
        with open(f'error_logs/import_error_ids_{formatted_datetime}.txt', 'w') as file:
            for error_id in errors:
                file.write(str(error_id) + '\n')
            file.close()

def import_by_id(database_destination_url, database_id_mapping_url, id):

    if not os.path.exists('exam_ids/exam_ids_imported.txt'):
        with open('exam_ids/exam_ids_imported.txt', 'w'):
            pass

    exam_ids_imported = [line.strip() for line in open('exam_ids/exam_ids_imported.txt', 'r')]

    ids_imported = []
    errors = []

    engine_import = create_and_check_engine(database_url=database_destination_url)
    engine_log = create_and_check_engine(database_url=database_id_mapping_url)

    try:
        with get_sessions_from_engines(engine_import, engine_log) as (session_import, session_log): 
            exam_id = import_exam_bank(session_import, session_log, exam_id=id)
            if exam_id != 0:
                ids_imported.append(id)
            if exam_id == 0:
                errors.append(id)
            print(f'{exam_id}   {id}  {0}')
    except:
        errors.append(id)

    if ids_imported:
        ids_imported = [id_imported for id_imported in ids_imported if str(id_imported) not in exam_ids_imported]
        with open(f'exam_ids/exam_ids_imported.txt', 'a') as file:
            for id_imported in ids_imported:
                file.write(str(id_imported) + '\n')
            file.close()

    if errors:
        current_datetime = datetime.datetime.now()
        formatted_datetime = current_datetime.strftime("%Y-%m-%d_%H-%M-%S")
        with open(f'error_logs/import_error_ids_{formatted_datetime}.txt', 'w') as file:
            for error_id in errors:
                file.write(str(error_id) + '\n')
            file.close()

def main():
    parser = argparse.ArgumentParser(description="Data importer with CLI")
    parser.add_argument('--file', type=str, help='Path to file containing IDs to import')
    parser.add_argument('--id', type=int, help="ID of the exam to import")
    args = parser.parse_args()

    database_destination_url = f"{settings.database_url}{settings.db_destination}"
    database_id_mapping_url = f"{settings.database_url}{settings.db_id_mapping}"    

    if args.file:
        import_by_text_file(database_destination_url, database_id_mapping_url, args.file)
    elif args.id:
        import_by_id(database_destination_url, database_id_mapping_url, args.id)
    else:
        print('Please provide either --file or --id argument.')

    
if __name__=="__main__":
    main()