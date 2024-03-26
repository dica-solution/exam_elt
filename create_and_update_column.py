from sqlalchemy import create_engine, update, MetaData, Table
from sqlalchemy.orm import sessionmaker
from src.config.config import settings
import time


engine_id_mapping = create_engine(f"{settings.database_url}{settings.db_id_mapping}")
engine_paper_exams = create_engine(f"{settings.database_url}{settings.db_paper_exams}")

tracking_logs = Table('tracking_logs', MetaData(), autoload_with=engine_id_mapping)
paper_exams = Table('paper_exams', MetaData(), autoload_with=engine_paper_exams)

session_id_mapping = sessionmaker(bind=engine_id_mapping)()
session_paper_exams = sessionmaker(bind=engine_paper_exams)()

data = session_paper_exams.query(paper_exams).all()

id_to_value = {row.id: row.updated_at for row in data}
start = time.time()
for row in session_id_mapping.query(tracking_logs).all():
    if row.src_exam_id in id_to_value:
        stmt = (
            update(tracking_logs).
            where(tracking_logs.c.src_exam_id == row.src_exam_id).
            values(updated_at = id_to_value[row.src_exam_id])
        )
        session_id_mapping.execute(stmt)
        session_id_mapping.commit()

session_id_mapping.commit()

session_id_mapping.close()
session_paper_exams.close()
print(f"Total time taken: {time.time() - start}")
