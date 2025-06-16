from sqlalchemy import Column, Integer, Text, DateTime, func
from fastapi_app.db.base import Base

class ExamsRules(Base):
    __tablename__ = "quiz_examsrules"

    id = Column(Integer, primary_key=True, index=True)
    rules = Column(Text, nullable=True)
    created = Column(DateTime(timezone=False), server_default=func.now())
    updated = Column(DateTime(timezone=False), onupdate=func.now())
