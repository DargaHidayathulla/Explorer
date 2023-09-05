from sqlalchemy import Boolean,Column,Integer,String,DateTime,func,Boolean
from database import Base
from sqlalchemy.dialects.postgresql import BYTEA


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

class Credentials(Base):
    __tablename__ = 'credentials'
    id = Column(Integer, primary_key=True, index=True)
    smtphost = Column(String)
    smtpport = Column(String)
    smtp_user =Column(String)
    smtp_password =Column(String)


# BEFORE INSERT ON users
# FOR EACH ROW
# EXECUTE FUNCTION update_user_id_sequence();
# -- SELECT setval('users_user_id_seq', (SELECT max(user_id) FROM users));
# -- SELECT column_name, column_default
# -- FROM information_schema.columns
# -- WHERE table_name = 'users' AND column_name = 'user_id';