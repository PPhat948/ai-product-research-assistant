from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import os

Base = declarative_base()

class QueryLog(Base):
    __tablename__ = 'query_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    user_query = Column(String, nullable=False)
    agent_response = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    feedbacks = relationship("Feedback", back_populates="query")

class Feedback(Base):
    __tablename__ = 'feedbacks'
    
    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(Integer, ForeignKey('query_logs.id'))
    rating = Column(Integer, nullable=False) # valid values: 1-5
    comment = Column(String, nullable=True)
    
    query = relationship("QueryLog", back_populates="feedbacks")

DB_URL = "sqlite:///./products.db"

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

