from src.models.exam_bank_models import TrackingLogs
from src.database import Base
from src.config.config import settings
from sqlalchemy import create_engine
database_id_mapping_url = f"{settings.database_url}{settings.db_id_mapping}"
engine = create_engine(
    database_id_mapping_url, echo=False,
    pool_size=50,
    max_overflow=0,
)
try:
    # Attempt to connect to the database
    with engine.connect() as connection:
        print("Connection successful!")
        TrackingLogs.__table__.create(engine)
        print("Create `TrackingLogs` table successful!")
except Exception as e:
    print(f"Connection failed: {e}")