import logging
import re
from contextlib import contextmanager
from typing import Callable, ContextManager

from sqlalchemy import create_engine, orm
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import Session, scoped_session, sessionmaker

# from src.core.config import settings

logger = logging.getLogger(__name__)

quizz_database_url = 'postgresql://postgres:3FGae34ggFIg@dica-server:54321/vansy_exam_bank'
quizz_database_engine_pool_size = 5
quizz_database_engine_max_overflow = 10
engine = create_engine(
    quizz_database_url, echo=False,
    pool_size=quizz_database_engine_pool_size,
    max_overflow=quizz_database_engine_max_overflow,
)

@contextmanager
def get_session():
    session = scoped_session(sessionmaker(bind=engine,))
    try:
        yield session()
    except Exception as e:
        raise e from None
    finally:
        session.close()


@contextmanager
def get_session_from_engine(from_engine):
    session = scoped_session(sessionmaker(bind=from_engine,))
    try:
        yield session()
    except Exception as e:
        raise e from None
    finally:
        session.close()


def resolve_table_name(name):
    """Resolves table names to their mapped names."""
    names = re.split("(?=[A-Z])", name)  # noqa
    return "_".join([x.lower() for x in names if x])


Base = declarative_base()

