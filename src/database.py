import logging
import re
from contextlib import contextmanager
from typing import Callable, ContextManager

from sqlalchemy import create_engine, orm
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import Session, scoped_session, sessionmaker


@contextmanager
def get_session_from_engine(from_engine):
    session = scoped_session(sessionmaker(bind=from_engine,))
    try:
        yield session()
    except Exception as e:
        raise e from None
    finally:
        session.close()

@contextmanager
def get_sessions_from_engines(engine1, engine2):
    session1 = scoped_session(sessionmaker(bind=engine1))
    session2 = scoped_session(sessionmaker(bind=engine2))
    
    try:
        yield session1, session2
    except Exception as e:
        raise e from None
    finally:
        session1.close()
        session2.close()


def resolve_table_name(name):
    """Resolves table names to their mapped names."""
    names = re.split("(?=[A-Z])", name)  # noqa
    return "_".join([x.lower() for x in names if x])


Base = declarative_base()

