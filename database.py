import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Default: SQLite file (runs instantly). For PostgreSQL set:
# DATABASE_URL=postgresql://user:pass@localhost/aacharya
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./aacharya.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine, autoflush=False)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
