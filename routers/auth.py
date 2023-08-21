
import sys
sys.path.append( "..")
import os
import smtplib,string,random,re
from fastapi import Depends,HTTPException,status,APIRouter
from pydantic import BaseModel
from typing import Optional ,List
import models
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from database import SessionLocal,engine
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime,timedelta
from jose import jwt,JWTError
from minio import Minio
from datetime import datetime, timezone, timedelta
import json
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




#login page
class Login(BaseModel):
    username:str
    password:str
# @router.post("/login")
# async def login_for_access_token(data:Login,db:Session = Depends(get_db)):
#     logger.info(f"Received login request for username: {data.username}") 
#     user = authenticate_user(data.username,data.password,db)
#     if not user:
#         logger.warning(f"Failed login attempt for username: {data.username}")
#         return{"msg": "incorrect  username" }
#         # raise token_exception()
#     else:
#         token_expires = timedelta(minutes=360)
#         token = create_access_token(user.email,
#                                 user.user_id,
#                                 expires_delta=token_expires)
#         logger.info(f"user login for username: {data.username} login") 
#         return{"token":token,"User":"User Found","User_type":user.User_type}


@router.post("/login")
async def login_for_access_token(data: Login, db: Session = Depends(get_db)):
    logger.info(f"Received login request for username: {data.username}") 
    user = authenticate_user(data.username, data.password, db)

    if not user:
        logger.warning(f"Failed login attempt for username: {data.username}")
        return {"msg": "Incorrect username or password"}
    elif not user.status:
        # Check if the user is disabled (status is "disable")
        logger.warning(f"Login attempt for disabled username: {data.username}")
        raise HTTPException(status_code=403, detail="User is disabled by admin")
    else:
        token_expires = timedelta(minutes=360)
        token = create_access_token(user.email, user.user_id, expires_delta=token_expires)
        logger.info(f"User login for username: {data.username}") 
        return {"token": token, "User": "User Found", "User_type": user.User_type}


# from fastapi import Header

# default_minio_client = Minio(
#     "192.168.1.151:9000",
#     access_key="minioadmin",
#     secret_key="minioadmin",
#     secure=False,
# )
# # Define the get_bucket_size_recursive function here...
# def get_bucket_size_recursive(minio_client, bucket_name, prefix=""):
#     total_size = 0
#     objects = minio_client.list_objects(bucket_name, prefix=prefix, recursive=True)
#     for obj in objects:
#         total_size += obj.size
#     return total_size

# @router.get("/list4")
# async def list_buckets(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
#     try:
#         # Authenticate the user with the provided username and password
#         pas = db.query(models.Users).filter(models.Users.user_id == user.get("id")).first()
        
#         # Determine which MinIO client to use based on user type
#         # user_type = pas.User_type
#         # if user_type.lower() == 'admin':
#         if pas.User_type == 'admin':
#             minio_client = default_minio_client
#         else:
#             # Create a MinIO client for the regular user
#             minio_client = Minio(
#                 "192.168.1.151:9000",
#                 access_key=pas.email,
#                 secret_key=pas.password,
#                 secure=False
#             )
        
#         bucket_info = []
        
#         # List all buckets for admin users or user-specific buckets for regular users
#         for bucket in minio_client.list_buckets():
#             objects = minio_client.list_objects(bucket.name)
#             num_objects = len([obj for obj in objects])
#             # Format the bucket creation date in the desired timezone format
#             creation_date = bucket.creation_date.astimezone(timezone(timedelta(hours=5, minutes=30))).strftime('%Y-%m-%d %H:%M:%S %Z')

#             bucket_size = get_bucket_size_recursive(minio_client, bucket.name)
#             bucket_size2 = bucket_size / 1024  # Convert size to KB

#             size_str = f"{bucket_size / 1024:.2f} KB" if bucket_size < (1024 * 1024) else f"{bucket_size / (1024 * 1024):.2f} MB"

#             # Get bucket information
#             bucket_info.append({
#                 "name": bucket.name,
#                 "created": creation_date,
#                 "size": size_str,
#                 "size_value": round(bucket_size2),
#                 "objects": num_objects
#             })

#         return {"buckets": bucket_info}
#     except Exception as e:
#         return {"error": str(e)}






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
# Assuming you have a function to retrieve the username from the database

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



def create_minio_user(username, password):
    try:
        cruser_command = f"./mc admin user add minio {username} {password}"
        subprocess.run(cruser_command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error creating MinIO user: {e}")
#user creation and db and minio at a time data?
class create(BaseModel):
    name: str
    username: str

@router.post("/user_create")
async def create_user(users: create, db: Session = Depends(get_db),
                      user: dict = Depends(get_current_user)):
    new = db.query(models.Users).filter(models.Users.user_id == user.get('id')).first()
    user_type = new.User_type
    
    if user_type.lower() == 'admin':
        existing_user = db.query(models.Users).filter(models.Users.email == users.username).first()
        if existing_user:
            return {"detail":"User with this email already exists."}
        logger.info(f"Admin created a new user: {users.username}")
        user_model = models.Users()
        user_model.Name = users.name 
        user_model.email = users.username
        pas = new_password(users.username)
        user_model.password = pas
        user_model.User_type = "regular_user"
        user_model.status = True 
        db.add(user_model)
        db.commit()
        
        # Create user in MinIO with the same email and password
        create_minio_user(users.username, pas)
        
        return {"msg":"User created successfully."}
    else:
        raise HTTPException(status_code=403, detail="You are not authorized to create new users.")


# @router.get("/show")
# async def show_users(user: dict = Depends(get_current_user),
#                            db: Session = Depends(get_db)):

#     if user is None:
#         raise get_user_exception()
#     new=db.query(models.Users).filter(models.Users.user_id==user.get('id')).first()
#     type=new.User_type
#     if type.lower()=='admin':
#         return db.query(models.Users)\
#             .filter(models.Users.User_type == 'regular_user').all()
#     else:
#         return {"detail":"only admin can access the users"}



# ... (previous code)

# # Disable user route
# @router.get("/user_disable/{username}")
# def disable_user(username: str, db: Session = Depends(get_db)):
#     try:
#         # Run MinIO command to disable user
#         cruser_command = f"./mc admin user disable minio {username}"
#         subprocess.run(cruser_command, shell=True, check=True)

#         # Update the user status in the database to "disable"
#         user = db.query(models.Users).filter(models.Users.email == username).first()
#         if user:
#             user.status = False  # Update status to "disable"
#             db.commit()
#         else:
#             raise HTTPException(status_code=404, detail="User not found")

#     except subprocess.CalledProcessError as e:
#         raise RuntimeError(f"Error disabling MinIO user: {e}")

#     return {"message": "User disable is successful"}

# # Enable user route
# @router.get("/user_enable/{username}")
# def user_enable(username: str, db: Session = Depends(get_db)):
#     try:
#         # Run MinIO command to enable user
#         cruser = f"./mc admin user enable minio {username}"
#         subprocess.run(cruser, shell=True, check=True)

#         # Update the user status in the database to "enable"
#         user = db.query(models.Users).filter(models.Users.email == username).first()
#         if user:
#             user.status = True  # Update status to "enable"
#             db.commit()
#         else:
#             raise HTTPException(status_code=404, detail="User not found")

#     except subprocess.CalledProcessError as e:
#         raise RuntimeError(f"Error enabling MinIO user: {e}")

#     return {"message": "User enable is successful"}


# class UserStatus(BaseModel):
#     username: str
#     action: bool  # Change the action type to bool

# @router.post("/user_status/")
# def user_status(user_status: UserStatus, db: Session = Depends(get_db)):
#     try:
#         if isinstance(user_status.action, bool):
#             # Convert the boolean action to the corresponding string value
#             action_str = "enable" if user_status.action else "disable"

#             # Run MinIO command to enable or disable user based on action_str
#             cruser_command = f"./mc admin user {action_str} minio {user_status.username}"
#             subprocess.run(cruser_command, shell=True, check=True)

#             # Update the user status in the database based on the action
#             user = db.query(models.Users).filter(models.Users.email == user_status.username).first()
#             if user:
#                 user.status = user_status.action
#                 db.commit()
#             else:
#                 raise HTTPException(status_code=404, detail="User not found")
            
#             return {"message": f"User {action_str} is successful"}

#         else:
#             raise HTTPException(status_code=400, detail="Invalid action")

#     except subprocess.CalledProcessError as e:
#         raise HTTPException(status_code=500, detail=f"Error performing action: {e}")










