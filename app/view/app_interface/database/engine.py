
from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.common.paths import AppPaths
from app.view.app_interface.database.models import Base

_engine = create_engine(f"sqlite:///{AppPaths.DATABASE_FILE}", echo=False, future=True)
SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False)


def init_db() -> None:
    """Create all tables if they don't exist."""
    AppPaths.ensure_directories()
    Base.metadata.create_all(_engine)
    logger.info(f"[Database] Initialized at {AppPaths.DATABASE_FILE}")


def get_session():
    """Return a new session instance."""
    return SessionLocal()
