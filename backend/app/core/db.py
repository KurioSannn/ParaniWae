from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


@lru_cache
def get_engine() -> Engine:
    s = get_settings()
    eng = create_engine(s.database_url, pool_pre_ping=True, pool_size=s.db_pool_size, max_overflow=s.db_max_overflow,
                        pool_timeout=s.db_pool_timeout_s)
    if s.debug_query_stats:
        from app.core import query_stats
        query_stats.install(eng)
    return eng


def get_db() -> Iterator[Session]:
    with sessionmaker(bind=get_engine(), expire_on_commit=False)() as session:
        yield session
