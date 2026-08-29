from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Setting(Base):
    __tablename__ = "settings"
    key   = Column(String, primary_key=True)
    value = Column(String, nullable=False)

class Guest(Base):
    __tablename__ = "guests"

    id             = Column(Integer, primary_key=True, index=True)
    prenom         = Column(String, nullable=False, default="")
    nom            = Column(String, nullable=False, default="")
    telephone      = Column(String, nullable=True, default="")
    code           = Column(String, unique=True, nullable=False, index=True)
    email          = Column(String, nullable=True, default="")
    response       = Column(String, default="pending")   # pending / yes / no
    plus_one       = Column(Integer, default=0)           # accompagnants
    regime         = Column(String, default="standard")   # standard / vegetarien / sans-gluten
    table_number   = Column(Integer, default=0, nullable=True)
    seat_number    = Column(String, default="", nullable=True)
    affinity_group = Column(Integer, default=0, nullable=True)
    affinity_score = Column(Integer, default=0, nullable=True)
    relation_notes = Column(Text, default="")
    message        = Column(Text, default="")
    updated_at     = Column(DateTime, nullable=True)
    created_at     = Column(DateTime, default=datetime.utcnow)
