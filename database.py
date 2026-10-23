from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


SQLALCHEMY_DATABASE_URL = 'postgresql://postgres.eiomibduhjgegkdjhcfc:Admin2026Shuvo@aws-0-ap-northeast-2.pooler.supabase.com:5432/postgres'
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autoflush= False, autocommit= False, bind= engine)

Base = declarative_base()
