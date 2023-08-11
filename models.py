from sqlalchemy import Boolean,Column,Integer,String,ForeignKey, LargeBinary,DateTime,func

from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

class Users(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, index=True,autoincrement=True)
    Name = Column(String)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    User_type = Column(String)

class Log(Base):
    __tablename__ = 'logs'
    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(50))
    message = Column(String)
    created_at = Column(DateTime, default=func.now())

# from sqlalchemy import Column, Integer, String, Sequence
# class User(Base):
#     __tablename__ = 'users'
#     user_id = Column(Integer, Sequence('user_id_seq'), primary_key=True, autoincrement=True)
#     Name = Column(String)
#     email = Column(String, unique=True)
#     password = Column(String)
#     User_type = Column(String)