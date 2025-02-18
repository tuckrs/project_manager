from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from pathlib import Path

# Create data directory in user's home folder
data_dir = Path.home() / '.project_manager'
data_dir.mkdir(exist_ok=True)

# SQLite database file
database_path = data_dir / 'project_manager.db'
SQLALCHEMY_DATABASE_URL = f"sqlite:///{database_path}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}  # Needed for SQLite
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
