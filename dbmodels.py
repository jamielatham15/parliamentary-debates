from sqlalchemy import Column, Date, ForeignKey, Integer, String, create_engine
from sqlalchemy.dialects.postgresql import json
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

from config import config

Base = declarative_base()

class ParliamentarySession(Base):
    __tablename__='parliamentary_session'

    id = Column(Integer, primary_key=True)
    hansard_sitting_id = Column(Integer)
    chamber = Column(String)
    date = Column(Date)
    year = Column(Integer)
    speeches = relationship('Speech')

class Speech(Base):
    __tablename__='speech'

    id = Column(Integer, primary_key=True)
    hansard_speech_id = Column(Integer)
    title = Column(String)
    speakers = Column(String)
    full_text = Column(String)
    url = Column(String)
    parliamentary_session_id = Column(Integer, ForeignKey('parliamentary_session.id'))
    parliamentary_session = relationship('ParliamentarySession', back_populates='speeches')


engine = create_engine(config.database_uri)

Session = sessionmaker(bind=engine)

#Base.metadata.create_all(engine)