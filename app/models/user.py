import uuid
from sqlalchemy import Column, String, Index
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=True)
    picture = Column(String, nullable=True)
    __table_args__ = (Index("ix_user_email", "email"),)

    def to_dict(self):
        return {"id": str(self.id), "email": self.email, "name": self.name, "picture": self.picture}