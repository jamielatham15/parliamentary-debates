from config import config
from sqlalchemy import create_engine, Column, Integer, String, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import json, jsonb

engine = create_engine(config.database_uri)

Base = declarative_base()

class Session(Base):
    __tablename__='session'

    sitting_id = Column(Integer, primary_key=True)
    hansard_sitting_id = Column(Integer)
    chamber = Column(String)
    date = Column(Date)
    year = Column(Integer)

class Speech(Base):
    __tablename__='speech'

    speech_id = Column(Integer, primary_key=True)
    hansard_speech_id = Column(Integer)
    title = Column(String)
    speakers = Column(String)
    speech_text = Column(String)


class RawData(Base):
    __tablename__='raw_data'

    raw_data_id = Column(Integer, primary_key=True)
    raw_data = Column(json)




