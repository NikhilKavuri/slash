import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

# If DATABASE_URL is provided (Supabase/Neon), format properly for psycopg2
DB_URL = settings.DATABASE_URL or "sqlite:///./slash_catalog.db"

# SQLAlchemy 2.0 requires postgresql+psycopg2:// for psycopg2
if DB_URL.startswith("postgresql://"):
    DB_URL = DB_URL.replace("postgresql://", "postgresql+psycopg2://", 1)
elif DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql+psycopg2://", 1)

# SQLite specific connect args
connect_args = {"check_same_thread": False} if "sqlite" in DB_URL else {}

engine = create_engine(
    DB_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_recycle=300
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    """Ensure all tables are created in Supabase/PostgreSQL."""
    try:
        from app.models.product import ProductModel, PricePointModel
        Base.metadata.create_all(bind=engine)
        print("Database tables initialized successfully.")
    except Exception as e:
        print(f"Warning: could not initialize database tables: {e}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
