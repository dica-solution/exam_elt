from src.database import get_sessions_from_engines
from sqlalchemy import create_engine
# from src.services.import_ import import_exam_bank
from src.services.import_quiz import get_all_filtered_ids, import_exam_bank
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
    
def import_quiz(database_destination_url, database_id_mapping_url):

    filtered_id_list = get_all_filtered_ids(settings.api_get_filtered_quiz_ids)

    if not os.path.exists('ids/quiz_ids_imported.txt'):
        with open('ids/quiz_ids_imported.txt', 'w'):
            pass

    quiz_ids_imported = [line.strip() for line in open('ids/quiz_ids_imported.txt', 'r')]
    print(f'{len(quiz_ids_imported)} IDs have been imported in db!')
    if quiz_ids_imported:
        quiz_ids_to_import = [id for id in filtered_id_list if id not in quiz_ids_imported]
    else:
        quiz_ids_to_import = filtered_id_list
    # quiz_ids_to_import = quiz_ids_to_import[:1]
    print(f'{len(quiz_ids_to_import)} IDs are ready to import!')

    ids_imported = []
    errors = []

    engine_import = create_and_check_engine(database_url=database_destination_url)
    engine_log = create_and_check_engine(database_url=database_id_mapping_url)

    for i in range(len(quiz_ids_to_import)):
        with get_sessions_from_engines(engine_import, engine_log) as (session_import, session_log):
            try:
                src_quiz_id = int(quiz_ids_to_import[i])
                quiz_id = import_exam_bank(session_import, session_log, quiz_id=src_quiz_id)
                if quiz_id != 0:
                    ids_imported.append(src_quiz_id)
                    print(f'destination ID: {quiz_id}   , source ID{src_quiz_id: 10}, state: success')
                if quiz_id == 0:
                    errors.append(src_quiz_id)
                    print(f'destination ID: {quiz_id}   , source ID{src_quiz_id: 10}, state: fail')
            except:
                errors.append(src_quiz_id)
                print(f'destination ID: {0:15}, source ID{src_quiz_id: 15}, state: fail')

    if ids_imported:
        ids_imported = [id_imported for id_imported in ids_imported if id_imported not in quiz_ids_imported]
        with open(f'ids/quiz_ids_imported.txt', 'a') as file:
            for id_imported in ids_imported:
                file.write(str(id_imported) + '\n')
            file.close()

    if errors:
        current_datetime = datetime.datetime.now()
        formatted_datetime = current_datetime.strftime("%Y-%m-%d_%H-%M-%S")
        with open(f'error_logs/quiz_import_error_ids_{formatted_datetime}.txt', 'w') as file:
            for error_id in errors:
                file.write(str(error_id) + '\n')
            file.close()


def main():
    database_destination_url = f"{settings.database_url}{settings.db_destination}"
    database_id_mapping_url = f"{settings.database_url}{settings.db_id_mapping}"    

    import_quiz(database_destination_url, database_id_mapping_url)


    
if __name__=="__main__":
    main()