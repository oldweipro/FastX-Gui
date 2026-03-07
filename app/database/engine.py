
from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.common.setting import CONFIG_FOLDER
from app.database.models import Base

_DB_PATH = CONFIG_FOLDER / "fastx.db"
_engine = create_engine(f"sqlite:///{_DB_PATH}", echo=False, future=True)
SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False)


def init_db() -> None:
    """Create all tables if they don't exist."""
    CONFIG_FOLDER.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(_engine)
    logger.info(f"[Database] Initialized at {_DB_PATH}")


def get_session():
    """Return a new session instance."""
    return SessionLocal()
