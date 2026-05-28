import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import Settings

settings = Settings()
data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(data_dir, exist_ok=True)

db_url = settings.database_url
if db_url.startswith("sqlite:///./"):
    rel_path = db_url[len("sqlite:///./"):]
    db_url = f"sqlite:///{os.path.join(data_dir, rel_path)}"

connect_args = {"check_same_thread": False} if "sqlite" in db_url else {}
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