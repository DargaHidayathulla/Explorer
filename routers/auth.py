
# baysaggpqmqfhsok
import sys
sys.path.append( "..")
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


import subprocess
from routers.custom import get_custom_logger

logger = get_custom_logger(engine)

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
        expire = datetime.utcnow() + timedelta(minutes=30)
    encode.update({"exp":expire})
    return jwt.encode(encode,SECRET_KEY,algorithm=ALGORITHM)

async def get_current_user(token:str = Depends(oauth2_bearer)):
    try:
        payload = jwt.decode(token,SECRET_KEY, algorithms=[ALGORITHM])
        username:str = payload.get("sub")
        user_id:int =payload.get("id")
        if username is None or user_id is None:
            raise get_user_exception()
        # expiration_time = payload.get("exp")
        return{"username":username,"id":user_id}
    except JWTError:
        raise get_user_exception()


@router.post("/refresh_token")
async def refresh_token(token:str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        user_id = payload.get("id")
        
        # Assuming the old token is valid, generate a new token
        new_token = create_access_token(username, user_id)
        
        return {"new_token": new_token}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")






#login page
class Login(BaseModel):
    username:str
    password:str

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
        return {"disable":"User is disabled by admin"}
    else:
        # token_expires = timedelta(minutes=30)
        token = create_access_token(user.email, user.user_id)
        logger.info(f"User login for username: {data.username}") 
        return {"token": token, "User": "User Found", "User_type": user.User_type}



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
        pas=new_password(mail,db)
        new.password=pas
    db.commit()
    logger.info(f" this {email.username} forgot the password ")
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
    # logger.info(f"Received change password request for user ID: {user.get('id')}")
    pas = db.query(models.Users).filter(models.Users.user_id == user.get("id")).first()
    logger.info(f"Received change password request for user name is : {pas.Name}")
    if pas.password == password.CurrentPassword:
        if password.NewPassword == password.ConfirmPassword:
            if is_strong_password(password.NewPassword):
                pas.password = password.NewPassword
                db.commit()
                return {"success": "NEW PASSWORD CREATED SUCCESSFULLY"}
            else:
                return {"msg1": "New password must be at least 8 characters long and contain one special character."}
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


#password mail code

from email.mime.text import MIMEText

# Assuming you have already imported necessary modules and defined the logger

def new_password(email, db):
    try:
        smtp_credentials = db.query(models.Credentials).first()
        if not smtp_credentials:
            return {"msg1": "SMTP credentials not found in the database"}

        smtp_host = smtp_credentials.smtphost
        smtp_port = smtp_credentials.smtpport
        smtp_user = smtp_credentials.smtp_user
        smtp_password = smtp_credentials.smtp_password
        otp = "".join(random.choices(string.ascii_letters + string.digits, k=8))
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)

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

        mime_msg = MIMEText(msg, 'html')

        mime_msg['From'] = smtp_user
        mime_msg['To'] = email
        mime_msg['Subject'] = 'New Password'

        server.sendmail(smtp_user, email, mime_msg.as_string())
        server.quit()
        logger.info(f"Password created or reset by a user: {email}")
        return otp

    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        raise HTTPException(status_code=500, detail="Error sending email")

#testing part
class smtptesting(BaseModel):
    email:str


@router.post("/test_smtp")
async def test_smtp(email1:smtptesting,db: Session = Depends(get_db),
                    user: dict = Depends(get_current_user)):
    try:
        email1=email1.email
        # Retrieve SMTP credentials from the database
        smtp_credentials = db.query(models.Credentials).first()
        if not smtp_credentials:
            raise HTTPException(status_code=500, detail="SMTP credentials not found in the database")

        smtp_host = smtp_credentials.smtphost
        smtp_port = smtp_credentials.smtpport
        smtp_user = smtp_credentials.smtp_user
        smtp_password = smtp_credentials.smtp_password
        # Connect to the SMTP server and send the email
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)

        msg = f"""\
        <html>
          <body>
            <p><b>Hi,</b></p>
            <p style="color:blue;">Your Ezy | Explorer SMTP Email Test Compelted Successfully</p>
            <p><i>Regards,</i></p>
            <p style="color: red;">Ezy | Explorer</p>
          </body>
        </html>
        """

        mime_msg = MIMEText(msg, 'html')

        mime_msg['From'] = smtp_user
        mime_msg['To'] = email1
        mime_msg['Subject'] = 'SMTP Checking'

        server.sendmail(smtp_user, email1, mime_msg.as_string())
        server.quit()

        # logger.info(f"Password reset email sent to: {email1}")

        # Return a success message
        return {"message": "SMTP user credentials are valid"}

    except Exception as e:
        logger.error(f"smtp user invalid")
        return {"error":"Smtp user invalid"}




#smtp credentials table 
@router.get("/get_smtp")
async def show_smtp(db:Session=Depends(get_db)):
    new=db.query(models.Credentials).all()
    return new
#SMTP Creation part
class credentails(BaseModel):
    smtpHost :str
    smtpPort:str
    user:str
    password:str
@router.put("/smtp_create")
async def smtp_create(new:credentails,db: Session = Depends(get_db),
                      user: dict = Depends(get_current_user)):
    smtp_model=db.query(models.Credentials).first()
    if smtp_model:
      smtp_model.smtphost = new.smtpHost
      smtp_model.smtpport = new.smtpPort
      smtp_model.smtp_user = new.user
      smtp_model.smtp_password =new.password
      db.add(smtp_model)
      db.commit()
      return {"msg": "SMTP setup updated successfully."}
    else:
        smtp_model1=models.Credentials()
        smtp_model1.smtphost =new.smtpHost
        smtp_model1.smtpport = new.smtpPort
        smtp_model1.smtp_user = new.user
        smtp_model1.smtp_password = new.password
        db.add(smtp_model1)
        db.commit()
        return{"msg1":"SMTP created sucessfully"}


#minio creation part

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
        pas = new_password(users.username,db)
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


@router.get("/show")
async def show_users(user: dict = Depends(get_current_user),
                           db: Session = Depends(get_db)):

    if user is None:
        raise get_user_exception()
    new=db.query(models.Users).filter(models.Users.user_id==user.get('id')).first()
    return {"email":new.email}


