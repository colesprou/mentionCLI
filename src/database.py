"""
Database models and initialization for the Kalshi research tool.
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Float, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

Base = declarative_base()

class MentionMarket(Base):
    """Model for Kalshi mention markets."""
    __tablename__ = 'mention_markets'
    
    id = Column(Integer, primary_key=True)
    market_id = Column(String(100), unique=True, nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    ticker = Column(String(50))
    status = Column(String(50))  # open, closed, resolved
    close_time = Column(DateTime)
    resolution = Column(String(50))  # yes, no, null
    yes_price = Column(Float)
    no_price = Column(Float)
    volume = Column(Integer)
    open_interest = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ResearchData(Base):
    """Model for research data associated with markets."""
    __tablename__ = 'research_data'
    
    id = Column(Integer, primary_key=True)
    market_id = Column(String(100), nullable=False)
    data_type = Column(String(50), nullable=False)  # news, transcript, analysis, etc.
    source = Column(String(200))
    title = Column(String(500))
    content = Column(Text)
    url = Column(String(500))
    sentiment_score = Column(Float)
    relevance_score = Column(Float)
    meta_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class AIAnalysis(Base):
    """Model for AI-generated analysis."""
    __tablename__ = 'ai_analysis'
    
    id = Column(Integer, primary_key=True)
    market_id = Column(String(100), nullable=False)
    analysis_type = Column(String(50), nullable=False)  # summary, prediction, sentiment
    content = Column(Text, nullable=False)
    confidence_score = Column(Float)
    model_used = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

class PriceHistory(Base):
    """Model for price history tracking."""
    __tablename__ = 'price_history'
    
    id = Column(Integer, primary_key=True)
    market_id = Column(String(100), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    yes_price = Column(Float)
    no_price = Column(Float)
    volume = Column(Integer)
    open_interest = Column(Integer)

# Global database session
Session = None

def init_database(database_url: str = 'sqlite:///kalshi_research.db'):
    """Initialize the database and create tables."""
    global Session
    
    engine = create_engine(database_url, echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

def get_session():
    """Get a database session."""
    if Session is None:
        raise Exception("Database not initialized. Call init_database() first.")
    return Session()

def close_session(session):
    """Close a database session."""
    session.close()
