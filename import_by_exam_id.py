from src.database import get_sessions_from_engines
from sqlalchemy import create_engine
from src.services.import_data import import_exam_bank
from src.models.exam_bank_models import Base
from src.config.config import settings
import typer

database_destination_url = f"{settings.database_url}{settings.db_destination}"
database_id_mapping_url = f"{settings.database_url}{settings.db_id_mapping}"

    
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
    

def main(src_exam_id: int):
# def main(last_idx: int):
    engine_import = create_and_check_engine(database_url=database_destination_url)
    engine_log = create_and_check_engine(database_url=database_id_mapping_url)
    # with open('id_import_2.txt', 'r') as file:
    #     id_list = []
    #     for line in file:
    #         id = line.strip()
    #         id_list.append(int(id))
    # if last_idx != 0: last_idx += 1
    # idx = 0 + last_idx
    # error = []
    # for id in id_list[last_idx:]:
    #     try:
    #         with get_session_from_engine(engine) as session:
    #             exam_id = import_exam_bank(session, page=id)
    #             print(f'{exam_id}   {idx}')
    #             idx += 1
    #     except:
    #         error.append(id)
    # print(error)
    with get_sessions_from_engines(engine_import, engine_log) as (session_import, session_log): 
        exam_id = import_exam_bank(session_import, session_log, exam_id=src_exam_id)
        print(exam_id)
if __name__=="__main__":
    typer.run(main)