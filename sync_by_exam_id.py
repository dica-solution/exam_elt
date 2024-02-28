from src.services.sync_data import ExamUpdater
from src.database import get_sessions_from_engines
from src.config.config import settings
from sqlalchemy import create_engine
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
    engine_import = create_and_check_engine(database_url=database_destination_url)
    engine_log = create_and_check_engine(database_url=database_id_mapping_url)
    
    with get_sessions_from_engines(engine_import, engine_log) as (session_import, session_log): 
        exam_updater = ExamUpdater(session_import, session_log)
        exam_updater.update_exam(src_exam_id)
        print(f"Update exam: {src_exam_id} successful!")

if __name__=="__main__":
    typer.run(main)