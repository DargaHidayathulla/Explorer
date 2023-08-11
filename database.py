from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
SQLAlCHEMY_DATABASE_URL = "postgresql://postgres:darga123@localhost/mydatabaset"
engine = create_engine(
    SQLAlCHEMY_DATABASE_URL
)
SessionLocal = sessionmaker(autocommit=False,autoflush=False,bind=engine)
Base=declarative_base()

