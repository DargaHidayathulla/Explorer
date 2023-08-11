class Create(BaseModel):
    Name: str
    Email: str
    Status: int  # 0 for disabled, 1 for enabled
@router.post("/create")
async def create_user(users: Create, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    if user is None:
        raise get_user_exception()

    new = db.query(models.Users).filter(models.Users.user_id == user.get('id')).first()
    user_type = new.User_type

    if user_type == 'admin':
        logger.info(f"Admin created a new user: {users.Email}")
        
        if users.Status not in [0, 1]:
            raise HTTPException(status_code=400, detail="Invalid status value. Use 0 for disabled and 1 for enabled.")

        user_model = models.Users()
        user_model.Name = users.Name
        user_model.email = users.Email
        pas = new_password(users.Email)
        user_model.password = pas
        user_model.User_type = "regular_user"
        user_model.status = "disable" if users.Status == 0 else "enable"
        db.add(user_model)
        db.commit()

        return "User created successfully."
    else:
        raise HTTPException(status_code=403, detail="You are not authorized to create new users.")


class Users(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    user_type = Column(String)
    status = Column(String, default="enable")  # Status column with default value "enable"
@router.post("/create")
async def create_user(users: Create, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    if user is None:
        raise get_user_exception()

    new = db.query(models.Users).filter(models.Users.user_id == user.get('id')).first()
    user_type = new.User_type

    if user_type == 'admin':
        logger.info(f"Admin created a new user: {users.Email}")
        
        if users.Status not in [0, 1]:
            raise HTTPException(status_code=400, detail="Invalid status value. Use 0 for disabled and 1 for enabled.")

        user_model = models.Users()
        user_model.Name = users.Name
        user_model.email = users.Email
        pas = new_password(users.Email)
        user_model.password = pas
        user_model.User_type = "regular_user"
        user_model.status = "disable" if users.Status == 0 else "enable"  # Set status based on input
        db.add(user_model)
        db.commit()

        return "User created successfully."
    else:
        raise HTTPException(status_code=403, detail="You are not authorized to create new users.")


def change_user_status(user_id: int, new_status: str, db: Session):
    user = db.query(models.Users).filter(models.Users.user_id == user_id).first()
    if user:
        user.status = new_status
        db.commit()
    else:
        raise HTTPException(status_code=404, detail="User not found")
@router.put("/update_status/{user_id}")
async def update_user_status(user_id: int, new_status: str, db: Session = Depends(get_db),
                             user: dict = Depends(get_current_user)):
    if user is None:
        raise get_user_exception()

    admin = db.query(models.Users).filter(models.Users.user_id == user.get('id')).first()
    admin_type = admin.User_type

    if admin_type == 'admin':
        user = db.query(models.Users).filter(models.Users.user_id == user_id).first()
        if user:
            user.status = new_status
            db.commit()
            return "User status updated successfully."
        else:
            raise HTTPException(status_code=404, detail="User not found")
    else:
        raise HTTPException(status_code=403, detail="You are not authorized to update user status.")





from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from minio import Minio

# Assuming you have imported necessary modules and defined your database models

app = FastAPI()

# Configure MinIO client
minio_client = Minio(
    endpoint="minio_endpoint",
    access_key="your_access_key",
    secret_key="your_secret_key",
    secure=False  # Change this to True if your MinIO instance uses HTTPS
)

@app.post("/create")
async def create_user(users: Create, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    if user is None:
        raise get_user_exception()

    new = db.query(models.Users).filter(models.Users.user_id == user.get('id')).first()
    user_type = new.User_type

    if user_type == 'admin':
        # ... Existing admin validation and user creation logic ...

        # Save user data to MinIO
        user_data = f"Name: {users.Name}\nEmail: {users.Email}\n"
        object_name = f"user_{user_model.id}.txt"  # You might use a unique identifier for the object name
        bucket_name = "user-data"

        minio_client.put_object(
            bucket_name,
            object_name,
            user_data.encode('utf-8'),  # Convert to bytes before saving
            len(user_data)
        )

        return "User created successfully."
    else:
        raise HTTPException(status_code=403, detail="You are not authorized to create new users.")


    