from sqlalchemy import Boolean,Column,Integer,String,DateTime,func,Boolean
# from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy.dialects.postgresql import BYTEA
# from sqlalchemy.orm import declarative_base, sessionmaker
# from datetime import datetime

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





    # def set_password(self, password):
    #     # Generate a salt and hash the password
    #     salt = bcrypt.gensalt()
    #     hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    #     self.smtp_password = hashed.decode('utf-8')

    # def check_password(self, password):
    #     # Check if the provided password matches the stored hashed password
    #     return bcrypt.checkpw(password.encode('utf-8'), self.smtp_password.encode('utf-8'))




# from sqlalchemy import Column, Integer, String
# from sqlalchemy.ext.declarative import declarative_base
# from cryptography.fernet import Fernet  # You'll need to install the cryptography library

# Base = declarative_base()

# class Credentials(Base):
#     __tablename__ = 'credentials'
#     id = Column(Integer, primary_key=True, index=True)
#     smtphost = Column(String)
#     smtpport = Column(String)
#     smtp_user = Column(String)
#     smtp_password_encrypted = Column(String)  # Store the encrypted password as a string

#     # Encryption key. You should generate a secure key and store it securely.
#     encryption_key = 'your_secure_encryption_key'

#     def encrypt_password(self, password):
#         # Encrypt the password before storing it
#         f = Fernet(self.encryption_key)
#         self.smtp_password_encrypted = f.encrypt(password.encode()).decode()

#     def decrypt_password(self):
#         # Decrypt and return the stored password
#         f = Fernet(self.encryption_key)
#         return f.decrypt(self.smtp_password_encrypted.encode()).decode()



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