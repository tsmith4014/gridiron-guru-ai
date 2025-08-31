import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from app.models.models import Player, RosterCounts

# Database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://draft_user:draft_password@localhost:5432/draft_db")

# Create engine
engine = create_engine(DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Database models
class PlayerDB(Base):
    __tablename__ = "players"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    position = Column(String)
    team = Column(String)
    adp = Column(Integer)
    tier = Column(String)
    age = Column(Integer, nullable=True)
    experience = Column(Integer, nullable=True)
    injury_history = Column(String, nullable=True)
    strength_of_schedule = Column(Float, nullable=True)
    bye_week = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DraftHistoryDB(Base):
    __tablename__ = "draft_history"
    
    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer)
    draft_round = Column(Integer)
    draft_slot = Column(Integer)
    overall_pick = Column(Integer)
    team_id = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

class RosterDB(Base):
    __tablename__ = "rosters"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer)
    player_id = Column(Integer)
    added_at = Column(DateTime, default=datetime.utcnow)

class MLModelDB(Base):
    __tablename__ = "ml_models"
    
    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String)
    model_version = Column(String)
    accuracy_score = Column(Float)
    training_date = Column(DateTime, default=datetime.utcnow)
    model_path = Column(String)

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Database utility functions
def init_db():
    """Initialize database with sample data"""
    Base.metadata.create_all(bind=engine)
    
    # Add sample players if database is empty
    db = SessionLocal()
    try:
        if db.query(PlayerDB).count() == 0:
            sample_players = [
                PlayerDB(name="Ja'Marr Chase", position="WR", team="CIN", adp=1, tier="1"),
                PlayerDB(name="Bijan Robinson", position="RB", team="ATL", adp=2, tier="1"),
                PlayerDB(name="Saquon Barkley", position="RB", team="PHI", adp=3, tier="1"),
                PlayerDB(name="Justin Jefferson", position="WR", team="MIN", adp=4, tier="1"),
                PlayerDB(name="Jahmyr Gibbs", position="RB", team="DET", adp=5, tier="1"),
            ]
            db.add_all(sample_players)
            db.commit()
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()
