"""Engine/session factory. SQLite for the v1.0 release; set DENOVOVHH_DB_URL to a
postgresql+psycopg URL to run the identical schema on PostgreSQL."""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

DB_URL = os.environ.get("DENOVOVHH_DB_URL",
                        "sqlite:///" + os.path.join(os.path.dirname(__file__), "..", "data", "denovovhh.sqlite"))

engine = create_engine(DB_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, future=True)


def init_db():
    Base.metadata.create_all(engine)


def get_session():
    return SessionLocal()
