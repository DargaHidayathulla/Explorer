import sys
sys.path.append( "..")
from pydantic import BaseModel
import models
from minio import Minio
from datetime import timezone, timedelta
from minio.error import S3Error
import io
import zipfile

from fastapi import Depends,HTTPException,APIRouter

from sqlalchemy.orm import Session
from database import SessionLocal,engine
from routers.auth import get_current_user
import subprocess
import json
from routers.custom import get_custom_logger
from routers.ezyexplorer import minio_client
logger = get_custom_logger(engine)
router = APIRouter(
    prefix="/bucket",
    tags=["bucket_list"],
)

# default_minio_client = Minio(
#     "localhost:9000",
#     access_key="minioadmin",
#     secret_key="minioadmin",
#     secure=False,
# )
def get_db():
    try:
        db=SessionLocal()
        yield db
    finally:
        db.close()


def convert_to_folder_structure(data, current_path="", bucket_name=""):
    folder_structure = []

    for key, value in data.items():
        folder_path = current_path + "/" + key if current_path else key

        if isinstance(value, dict):
            folder_structure.append({
                "type": "folder",
                "folderName": key,
                "path": folder_path,
                "files": convert_to_folder_structure(value, current_path=folder_path, bucket_name=bucket_name)
            })
        else:
            # Extract the file type from the filename
            file_type = key.split('.')[-1]

            # Get the size of the file
            stat = minio_client.stat_object(bucket_name, value)
            file2=stat.size
            file_size_mib = file2 / 1024
            
            if file2 < (1024 * 1024):
                size_str = f"{file2 / 1024:.2f} KB"
            else:
                size_str = f"{file2 / (1024 * 1024):.2f} MB"
            folder_structure.append({
                "type": "file",
                "filename": key,
                "filetype": '.' + file_type,
                "fileurl": value,
                "size": size_str,
                "size_value":round(file_size_mib,2)
            })

    return folder_structure


def get_bucket_data_recursive(bucket_name, tree_path, objects):
    for obj in objects:
        levels = obj.object_name.split("/")
        file = levels.pop()
        acc = tree_path

        for p in levels:
            acc = acc.setdefault(p, {})

        acc[file] = obj.object_name

    return tree_path

@router.get("/get_bucket_data/{bucket_name}")
async def get_minio_data(bucket_name: str,user: dict = Depends(get_current_user)):
    objects = minio_client.list_objects(bucket_name, recursive=True)

    tree_path = {}

    # Call the recursive function to get the folder structure
    tree_path = get_bucket_data_recursive(bucket_name, tree_path, objects)

    # Convert the MinIO data into the desired folder structure format
    folder_structure = convert_to_folder_structure({bucket_name: tree_path}, bucket_name=bucket_name)
    return folder_structure


# bucket size part
def get_bucket_size_recursive(minio_client, bucket_name, prefix=""):
    total_size = 0
    objects = minio_client.list_objects(bucket_name, prefix=prefix, recursive=True)
    for obj in objects:
        total_size += obj.size
    return total_size

@router.get("/list")
async def list_buckets(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        # Authenticate the user with the provided username and password
        pas = db.query(models.Users).filter(models.Users.user_id == user.get("id")).first()
        # minio_client = minio_client
        user_policies = []

        if pas.User_type != 'admin':
            pas1 = pas.email
            user_policies = get_user_policies5(pas1)

            user_policies = [policy for sublist in user_policies for policy in (sublist if isinstance(sublist, list) else [sublist])]
            
        bucket_info = []
        for bucket in minio_client.list_buckets():
            objects = minio_client.list_objects(bucket.name)
            num_objects = len([obj for obj in objects])
            creation_date = bucket.creation_date.astimezone(timezone(timedelta(hours=5, minutes=30))).strftime('%Y-%m-%d %H:%M:%S %Z')

            bucket_size = get_bucket_size_recursive(minio_client, bucket.name)
            bucket_size2 = bucket_size / 1024  # Convert size to KB

            size_str = f"{bucket_size / 1024:.2f} KB" if bucket_size < (1024 * 1024) else f"{bucket_size / (1024 * 1024):.2f} MB"
            # Check if the user is not an admin and the bucket name exactly matches one of the user's policies
            if pas.User_type != 'admin' and bucket.name in user_policies:
                # Add bucket information to the list
                bucket_info.append({
                    "name": bucket.name,
                    "created": creation_date,
                    "size": size_str,
                    "size_value": round(bucket_size2),
                    "objects": num_objects
                })

            # If the user is an admin, add all buckets to the list
            elif pas.User_type == 'admin':
                bucket_info.append({
                    "name": bucket.name,
                    "created": creation_date,
                    "size": size_str,
                    "size_value": round(bucket_size2),
                    "objects": num_objects
                })
        return {"buckets": bucket_info}
    
    except Exception as e:
        return {"error": str(e)}

def get_user_policies5(username):
    try:
        # Get all user data based on the username
        cmd_get_user_data = f"./mc admin user info minio {username} --json"
        user_info_output = subprocess.check_output(cmd_get_user_data, shell=True).decode()
        user_info = json.loads(user_info_output)
        policies = user_info.get("policyName", []).split(',')
        member_of = [group['policies'] for group in user_info.get("memberOf", [])]
        all_policies = policies + member_of
        return all_policies
    except subprocess.CalledProcessError as e:
        print(f"Error getting user data: {str(e)}")
        return []




#add something file download and folder download

class download(BaseModel):
    bucket_name:str
    path:str

@router.post("/file/download")
async def download_item(file2:download,user: dict = Depends(get_current_user),db: Session = Depends(get_db)):
    new= db.query(models.Users).filter(models.Users.user_id == user.get("id")).first()
    try:
        # Check if the path represents a file
        is_file = is_path_a_file(file2.bucket_name, file2.path)
        if is_file:
            # Generate a pre-signed URL for the file
            url = generate_presigned_url(file2.bucket_name, file2.path)
            logger.info(f"The user {new.email} as downloaded the {file2.path}  file from the bucket {file2.bucket_name}")
            return {"download_url": url}
        else:
            # Generate a pre-signed URL for a zip archive of the folder
            zip_url = generate_presigned_zip_url(file2.bucket_name,file2.path)
            logger.info(f"the user {new.email} as downloaded the {file2.path}  folder from the bucket {file2.bucket_name} ")
            return {"download_url": zip_url}
    except S3Error as e:
        raise HTTPException(status_code=400, detail="Failed to generate download URL")

def is_path_a_file(bucket_name: str, path: str):
    try:
        # Check if the specified path exists in the bucket as an object (file)
        minio_client.stat_object(bucket_name, path)
        return True
    except S3Error as e:
        # The path does not exist or is not an object (file)
        return False

def generate_presigned_url(bucket_name: str, file_path: str):
    try:
        # Generate a pre-signed URL for the file that expires in some time
        url = minio_client.presigned_get_object(
            bucket_name, file_path, expires=timedelta(minutes=30)
        )
        return url
    except Exception as e:
        # Handle errors appropriately
        raise e

def generate_presigned_zip_url(bucket_name: str, folder_path: str):
    try:
        # Create a temporary in-memory zip archive
        zip_data = create_zip_archive(bucket_name, folder_path)
        
        # Upload the zip archive to MinIO
        zip_key = f"{folder_path}.zip"
        minio_client.put_object(
            bucket_name,
            zip_key,
            io.BytesIO(zip_data),
            len(zip_data),
            content_type="application/zip",
        )

        # Generate a pre-signed URL for the uploaded zip archive
        url = minio_client.presigned_get_object(
            bucket_name, zip_key, expires=timedelta(minutes=30)
        )

        return url
    except Exception as e:
        # Handle errors appropriately
        raise e

def create_zip_archive(bucket_name: str, folder_path: str):
    try:
        # List objects in the folder
        objects = minio_client.list_objects(
            bucket_name, folder_path, recursive=True
        )

        # Create a ZIP archive in memory
        zip_data = io.BytesIO()
        with zipfile.ZipFile(zip_data, "w", zipfile.ZIP_DEFLATED) as zipf:
            for obj in objects:
                # Retrieve the object's data from the storage
                obj_data = minio_client.get_object(
                    bucket_name, obj.object_name
                ).read()
                # Add the object's data to the ZIP archive
                # Get the relative path within the folder
                relative_path = obj.object_name[len(folder_path):].strip("/")
                zipf.writestr(relative_path, obj_data)

        return zip_data.getvalue()
    except Exception as e:
        raise e









