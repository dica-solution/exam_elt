from src.services.sync_data import ExamUpdater
from src.database import get_session_from_engine
from src.config.config import settings
from sqlalchemy import create_engine
import typer

database_url = f"{settings.database_url}/{settings.db_destination}"
engine = create_engine(
    database_url, echo=False,
    pool_size=50,
    max_overflow=0,
)
try:
    # Attempt to connect to the database
    with engine.connect() as connection:
        print("Connection successful!")
except Exception as e:
    print(f"Connection failed: {e}")

def main(src_exam_id: int):
    with get_session_from_engine(engine) as session:
        exam_updater = ExamUpdater(session)
        exam_data_update = exam_updater.update_exam(src_exam_id)

if __name__=="__main__":
    typer.run(main)