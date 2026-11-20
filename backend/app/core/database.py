import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

# If DATABASE_URL is provided (Neon/Supabase), use it; otherwise fallback to local sqlite for instant zero-config persistence
DB_URL = settings.DATABASE_URL or "sqlite:///./slash_catalog.db"

# SQLite specific connect args
connect_args = {"check_same_thread": False} if "sqlite" in DB_URL else {}

engine = create_engine(DB_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
