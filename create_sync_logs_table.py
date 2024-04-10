from src.models.exam_bank_models import SyncLogs
from src.database import Base
from src.config.config import settings
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone, timedelta
import argparse

parser = argparse.ArgumentParser(description="Create SyncLogs table")
parser.add_argument("--d", type=int, default=7, help="Number of days ago to set the `last_sync` value")
args = parser.parse_args()


database_id_mapping_url = f"{settings.database_url}{settings.db_id_mapping}"
engine = create_engine(
    database_id_mapping_url, echo=False,
    pool_size=50,
    max_overflow=0,
)
Session = sessionmaker(bind=engine)
session = Session()

try:
    with engine.connect() as connection:
        print("Connection successful!")
        inspector = inspect(engine)
        if 'sync_logs' not in inspector.get_table_names():
            SyncLogs.__table__.create(engine)
            print(f"Table {SyncLogs.__tablename__} has been created!")
            days_ago = datetime.now(timezone.utc) - timedelta(days=args.d)
            new_sync_log = SyncLogs(runtime=days_ago)
            session.add(new_sync_log)
            session.commit()
            print(f"Inserted initial value into {SyncLogs.__tablename__} table: {days_ago}")
        else:
            print(f"{SyncLogs.__tablename__} table already exists!")
except Exception as e:
    print(f"Connection failed: {e}")
