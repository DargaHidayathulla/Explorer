
import sys
sys.path.append( "..")
import os
import smtplib,string,random,re
from fastapi import Depends,HTTPException,status,APIRouter
from pydantic import BaseModel
from typing import Optional
import models
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from database import SessionLocal,engine
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime,timedelta
from jose import jwt,JWTError
import subprocess
SECRET_KEY ="KlgH6AzYDeZeGwD288to 79I3vTHT8wp7" 
ALGORITHM = "HS256" 
bcrypt_context =CryptContext(schemes=["bcrypt"],deprecated="auto")
models.Base.metadata.create_all(bind=engine)
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter(
    prefix="/auth",
    tags=["authorization"],
    responses={401:{"user":"not authorized"}}
)

def get_db():
    try:
        db=SessionLocal()
        yield db
    finally:
        db.close()




# def get_password_hash(password):
#     return bcrypt_context.hash(password)

def verify_password(user_password, db_password):
    if user_password == db_password:
        return True
    else:
        return False

def authenticate_user(email:str,password:str,db):
    user = db.query(models.Users)\
       .filter(models.Users.email == email )\
       .first()
    if not user:
        return False
    if not verify_password(password,user.password):
        return False
    return user


def create_access_token(username:str,user_id:int,
                        expires_delta:Optional[timedelta]=None):
    encode = {"sub":username,"id":user_id}
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=60)
    encode.update({"exp":expire})
    return jwt.encode(encode,SECRET_KEY,algorithm=ALGORITHM)

async def get_current_user(token:str = Depends(oauth2_bearer)):
    try:
        payload = jwt.decode(token,SECRET_KEY, algorithms=[ALGORITHM])
        username:str = payload.get("sub")
        user_id:int =payload.get("id")
        if username is None or user_id is None:
            raise get_user_exception()
        return{"username":username,"id":user_id}
    except JWTError:
        raise get_user_exception()


@router.get("/show")
async def show_settings(user: dict = Depends(get_current_user),
                           db: Session = Depends(get_db)):

    if user is None:
        raise get_user_exception()
    else:
        users=db.query(models.Users).filter(models.Users.user_id==user.get("id")).first()
        return {'user_type':users.User_type}


class Login(BaseModel):
    username:str
    password:str
@router.post("/login")
async def login_for_access_token(data:Login,db:Session = Depends(get_db)):
    logger.info(f"Received login request for username: {data.username}") 
    user = authenticate_user(data.username,data.password,db)
    if not user:
        logger.warning(f"Failed login attempt for username: {data.username}")
        return{"msg": "incorrect  username" }
        # raise token_exception()
    else:
        token_expires = timedelta(minutes=360)
        token = create_access_token(user.email,
                                user.user_id,
                                expires_delta=token_expires)
        logger.info(f"user login for username: {data.username} login") 
        return{"token":token,"User":"User Found","User_type":user.User_type}


# #usercreation code
# class create(BaseModel):
#     Name:str
#     Email:str


# @router.post("/create")
# async def create_user(users: create, db: Session = Depends(get_db),
#                       user: dict = Depends(get_current_user)):
 
#     if user is None:
#         raise get_user_exception()
#     new=db.query(models.Users).filter(models.Users.user_id==user.get('id')).first()
#     type = new.User_type   
#     if type=='admin':
#     # Log the request details
#          logger.info(f"admin created a new user: {users.Email}")
    
#     # Create the new user with 'regular' User_type
#          user_model = models.Users()
#          user_model.Name = users.Name 
#          user_model.email = users.Email
#          pas = new_password(users.Email)
#          user_model.password = pas
#          user_model.User_type = "regular_user"
#          db.add(user_model)
#          db.commit()
    
#          return "User created successfully."
#     else:
#           raise HTTPException(status_code=403, detail="You are not authorized to create new users.")



#forgot password code
class Email1(BaseModel):
    username:str

@router.post('/forgot_password')
async def forgot_password(email:Email1,db:Session=Depends(get_db)):
    mail=email.username
    new=db.query(models.Users).filter(models.Users.email==mail).first()
    if new is None:
        return {"invalid":" Invalid Email "}
        
    elif new is not None:
        pas=new_password(mail)
        new.password=pas
    db.commit()
    return { "success":"NEW PASSWORD CREATED SUCCESSFULLY "}





#change password code

class ChangePassword(BaseModel):
    CurrentPassword: str
    NewPassword: str
    ConfirmPassword: str

def is_strong_password(password: str) -> bool:
    # Define the password requirements here
    # Minimum length of 8 characters and at least one special character
    if len(password) < 8:
        return False

    # Using a regular expression to check for at least one special character
    special_characters = r"[@_!#$%^&*()<>?/\|}{~:]"
    if not re.search(special_characters, password):
        return False

    return True

@router.put('/change_password')
async def Change_Password(password: ChangePassword, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    logger.info(f"Received change password request for user ID: {user.get('id')}")
    pas = db.query(models.Users).filter(models.Users.user_id == user.get("id")).first()
    
    if pas.password == password.CurrentPassword:
        if password.NewPassword == password.ConfirmPassword:
            if is_strong_password(password.NewPassword):
                pas.password = password.NewPassword
                db.commit()
                return {"success": "NEW PASSWORD CREATED SUCCESSFULLY"}
            else:
                return {"msg": "New password must be at least 8 characters long and contain one special character."}
        else:
            return {"msg2": "New password and confirm password are not the same."}
    else:
        return {"msg": "Current password is wrong."}


def get_user_exception():
    credentials_exception =HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="could not validate credentials",
        headers={"WWW-Authenticate":"Bearer"},
    )
    return credentials_exception
def token_exception():
    token_exception_response =HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="incorrect username or password",
    headers={"WWW-Authenticate":"Bearer"}
    )
    return token_exception_response


# def get_current_timestamp():
#     return datetime.now().strftime("%Y-%m-%d %H:%M:%S")



import logging
class PostgresHandler(logging.Handler):
    def __init__(self, connection, table_name="logs"):
        super().__init__()
        self.connection = connection
        self.table_name = table_name

    def emit(self, record):
        try:
            log = models.Log(level=record.levelname, message=record.msg)
            with SessionLocal() as session:
                session.add(log)
                session.commit()
        except Exception as e:
            print(f"Error while logging to PostgreSQL: {e}")

# Create a custom logger and add the custom PostgresHandler
def get_custom_logger():
    logger = logging.getLogger("custom_logger")
    logger.setLevel(logging.INFO)

    handler = PostgresHandler(engine)
    logger.addHandler(handler)

    return logger

# Now, you can use the custom logger to log messages to the database
logger = get_custom_logger()


# import random
# import string
# import smtplib

#password mail code
import random
import string
import smtplib
from email.mime.text import MIMEText

def new_password(email):
    otp = "".join(random.choices(string.ascii_letters + string.digits, k=8))
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login('dargahidayathulla639@gmail.com', 'baysaggpqmqfhsok')

    # HTML formatted message
    msg = f"""\
    <html>
      <body>
        <p><b>Hi,</b></p>
        <p>Your Ezy | Explorer new password is :</p>
        <p style="color: blue;"><b>{otp}</b></p>
        <p><i>Regards,</i></p>
        <p style="color: red;">Ezy | Explorer</p>
      </body>
    </html>
    """

    # Create a MIMEText object with 'html' content type
    mime_msg = MIMEText(msg, 'html')

    mime_msg['From'] = 'dargahidaytahulla639@gmail..com'
    mime_msg['To'] = email
    mime_msg['Subject'] = 'New Password'

    server.sendmail('dargahidayathulla639@gmail.com', email, mime_msg.as_string())
    server.quit()
    logger.info(f"Password created or reset by a user: {email}")
    return otp



#  @app.get("/group_list")
# async def group_list():
#     # Construct the command as a list of strings
#     command = ["./mc", "admin", "group", "ls", "minio", "--json"]

#     # Run the command using subprocess and capture the output
#     try:
#         result = subprocess.run(command, capture_output=True, text=True, check=True)
#         groups_json = result.stdout  # Captured JSON output
#         return groups_json
#     except subprocess.CalledProcessError as e:
#         return f"Error: {e.returncode}\n{e.stderr}"




def create_minio_user(username, password):
    try:
        cruser_command = f"./mc admin user add minio {username} {password}"
        subprocess.run(cruser_command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error creating MinIO user: {e}")
#user creation and db and minio at a time data?
class create(BaseModel):
    Name: str
    Email: str

@router.post("/create")
async def create_user(users: create, db: Session = Depends(get_db),
                      user: dict = Depends(get_current_user)):

    if user is None:
        raise get_user_exception()
    
    new = db.query(models.Users).filter(models.Users.user_id == user.get('id')).first()
    user_type = new.User_type
    
    if user_type == 'admin':
        logger.info(f"Admin created a new user: {users.Email}")
    
        user_model = models.Users()
        user_model.Name = users.Name 
        user_model.email = users.Email
        pas = new_password(users.Email)
        user_model.password = pas
        user_model.User_type = "regular_user"
        db.add(user_model)
        db.commit()
        
        # Create user in MinIO with the same email and password
        create_minio_user(users.Email, pas)
        
        return "User created successfully."
    else:
        raise HTTPException(status_code=403, detail="You are not authorized to create new users.")


#checking users list in minio




# from fastapi import FastAPI, HTTPException
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from minio import Minio

# app = FastAPI()

# # PostgreSQL setup
# DATABASE_URL = "postgresql://username:password@localhost/dbname"
# engine = create_engine(DATABASE_URL)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# # MinIO setup
# minio_client = Minio("minio_server", access_key="minio_access_key", secret_key="minio_secret_key", secure=False)

# # Get user data from PostgreSQL
# def get_user_data(email: str):
#     db = SessionLocal()
#     user_data = db.query(User).filter(User.email == email).first()
#     db.close()
#     return user_data

# # Create MinIO user and assign policies/groups
# def create_minio_user_and_assign(user_data):
#     # Create MinIO user
#     minio_client.admin.user_add(user_data.email, user_data.password)
    
#     # Assign policies or groups based on user type
#     if user_data.usertype == "admin":
#         minio_client.admin.group_add_member("admin_group", user_data.email)
#     elif user_data.usertype == "regular":
#         minio_client.admin.group_add_member("regular_group", user_data.email)
#         minio_client.admin.policy_add_member("read_write_policy", user_data.email)

# # FastAPI route to create users and sync with MinIO
# @app.post("/create_user")
# async def create_user(user: UserCreate):
#     # Assuming UserCreate is a Pydantic model for user creation
#     db = SessionLocal()
#     new_user = User(email=user.email, password=user.password, usertype=user.usertype)
#     db.add(new_user)
#     db.commit()
#     db.close()
    
#     # Sync user data with MinIO
#     create_minio_user_and_assign(new_user)
    
#     return {"message": "User created successfully"}

# # FastAPI route to access MinIO resources
# @app.get("/get_bucket_data/{bucket_name}")
# async def get_minio_data(bucket_name: str, user_email: str):
#     user_data = get_user_data(user_email)
    
#     if user_data is None:
#         raise HTTPException(status_code=403, detail="Access denied.")
    
#     # Check user's usertype and authorize accordingly
#     if user_data.usertype == "admin":
#         # Provide full access to admin
#         objects = minio_client.list_objects(bucket_name, recursive=True)
#         return {"message": "Bucket data retrieved successfully.", "objects": objects}
#     elif user_data.usertype == "regular":
#         # Check if user has access to the bucket
#         if minio_client.admin.policy_contains_member("read_write_policy", user_data.email):
#             objects = minio_client.list_objects(bucket_name, recursive=True)
#             return {"message": "Bucket data retrieved successfully.", "objects": objects}
#         else:
#             raise HTTPException(status_code=403, detail="Access denied.")




