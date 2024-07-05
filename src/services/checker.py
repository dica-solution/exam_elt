from sqlalchemy.orm import Session
from src.services.logger_config import setup_logger
logger = setup_logger()

logger.info("`checker` module is running...")

def check_id_exist(id: int, session: Session, table_name: str):
    result = session.query(table_name).filter(table_name.id == id).first() is not None
    logger.info(f"Checking ID {id} in {table_name} table: {result}")
    return result