"""SQLAlchemy engine and session-factory construction."""

from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


@lru_cache(maxsize=4)
def create_session_factory(database_url: str) -> sessionmaker[Session]:
    """Return a cached session factory backed by a pooled SQLAlchemy engine."""

    engine: Engine = create_engine(database_url, pool_pre_ping=True)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
