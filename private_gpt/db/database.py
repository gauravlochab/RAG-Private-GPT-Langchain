from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

SQLALCHEMY_DATABASE_URL = os.environ.get('PRIVATEGPT_POSTGRES_CONNECTION_STRING')


engine = create_engine(SQLALCHEMY_DATABASE_URL,pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    try:
        yield SessionLocal()
    finally:
        SessionLocal().close()
