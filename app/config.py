from pydantic_settings import BaseSettings
from typing import List
from dotenv import load_dotenv
load_dotenv()

class Settings(BaseSettings):
    app_name: str = "Auto Studio"
    debug: bool = True
    database_url: str = "sqlite:///./studio.db"
    google_client_id: str = ""
    google_client_secret: str = ""
    session_secret: str = "change-me-to-a-random-secret"
    allowed_hosts: List[str] = ["*"]
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}