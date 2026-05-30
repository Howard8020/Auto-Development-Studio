import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import Settings

settings = Settings()

# Use /tmp/ for the database — guaranteed writable on Render and all platforms.
# On Render's free tier the app filesystem isn't writable at runtime, so we
# can't use a data/ directory next to the source code.
DATA_DIR = "/tmp/auto-studio-data"
os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "studio.db")
db_url = f"sqlite:///{DB_PATH}"

connect_args = {"check_same_thread": False}
engine = create_engine(db_url, echo=settings.debug, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()