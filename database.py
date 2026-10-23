from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


SQLALCHEMY_DATABASE_URL = 'postgresql://postgres:Admin2026Shuvo@db.eiomibduhjgegkdjhcfc.supabase.co:5432/postgres'
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autoflush= False, autocommit= False, bind= engine)

Base = declarative_base()
