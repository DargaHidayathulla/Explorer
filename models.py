from sqlalchemy import Boolean,Column,Integer,String,ForeignKey, LargeBinary,DateTime,func,Boolean

from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

class Users(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    Name = Column(String)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    User_type = Column(String)
    status = Column(Boolean, default=True)

class Log(Base):
    __tablename__ = 'logs'
    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(50))
    message = Column(String)
    created_at = Column(DateTime, default=func.now())

# CREATE OR REPLACE FUNCTION update_user_id_sequence()
# RETURNS TRIGGER AS $$
# BEGIN
#   IF NEW.user_id > (SELECT last_value FROM users_user_id_seq) THEN
#     SELECT setval('users_user_id_seq', NEW.user_id);
#   END IF;
#   RETURN NEW;
# END;
# $$ LANGUAGE plpgsql;

# CREATE TRIGGER user_id_trigger
# BEFORE INSERT ON users
# FOR EACH ROW
# EXECUTE FUNCTION update_user_id_sequence();
# -- SELECT setval('users_user_id_seq', (SELECT max(user_id) FROM users));
# -- SELECT column_name, column_default
# -- FROM information_schema.columns
# -- WHERE table_name = 'users' AND column_name = 'user_id';