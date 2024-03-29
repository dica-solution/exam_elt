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
def get_sessions_from_engines(*engines):
    sessions = []
    try:
        for engine in engines:
            session = scoped_session(sessionmaker(bind=engine))
            sessions.append(session)
        yield tuple(sessions)
    except Exception as e:
        raise e from None
    finally:
        for session in sessions:
            session.close()


def resolve_table_name(name):
    """Resolves table names to their mapped names."""
    names = re.split("(?=[A-Z])", name)  # noqa
    return "_".join([x.lower() for x in names if x])


Base = declarative_base()

