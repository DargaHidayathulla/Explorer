import sys
sys.path.append( "..")
import os
import pandas as pd
from fastapi import Depends,HTTPException,status,APIRouter,Request,Response
from pydantic import BaseModel
from typing import Optional
import models
from minio import Minio
from datetime import datetime, timezone, timedelta
from minio.error import S3Error
import io
import zipfile
from fastapi.responses import JSONResponse, StreamingResponse
from jose import jwt,JWTError
from fastapi import Depends,HTTPException,status,APIRouter
from pydantic import BaseModel
from typing import Optional ,List
import models
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from database import SessionLocal,engine
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime,timedelta

# from fastapi.responses import StreamingResponse
# import httpx
import asyncio
import urllib.parse
from fastapi.responses import JSONResponse,StreamingResponse
router = APIRouter(
    prefix="/bucket",
    tags=["bucket_list"],
)

minio_client = Minio(
    "192.168.1.151:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False,
)


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
            
            # file_size_mib = stat.size / (1024 * 1024)
            # # file2=int(stat.size/1024)
            # # file_size_kb = int(stat.size / 1024)
            # # size_str = f"{file_size_kb} KB" 
            # if file_size_mib < 1:
            #     # Convert to kilobytes (KB)
            #     file_size_kb = int(stat.size / 1024)
            #     size_str = f"{file_size_kb} KB"
            # else:
            #     # Convert to megabytes (MB)
            #     file_size_mb = round(file_size_mib, 2)
            #     size_str = f"{file_size_mb} MB"
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
async def get_minio_data(bucket_name: str):
    objects = minio_client.list_objects(bucket_name, recursive=True)

    tree_path = {}

    # Call the recursive function to get the folder structure
    tree_path = get_bucket_data_recursive(bucket_name, tree_path, objects)

    # Convert the MinIO data into the desired folder structure format
    folder_structure = convert_to_folder_structure({bucket_name: tree_path}, bucket_name=bucket_name)

    return folder_structure


@router.get("/list")
async def list_buckets():
    try:
        bucket_info = []
        for bucket in minio_client.list_buckets():
            objects = minio_client.list_objects(bucket.name)
            num_objects = len([obj for obj in objects])
         # Format the bucket creation date in the desired timezone format
            creation_date = bucket.creation_date.astimezone(timezone(timedelta(hours=5, minutes=30))).strftime('%Y-%m-%d %H:%M:%S %Z')
            bucket_size = get_bucket_size_recursive(minio_client, bucket.name)
            # Adjust size representation to include "KB" for sizes below 1 MiB
            # bucket_mib =bucket_size / (1024*1024)
            # bucket_kib =int(bucket_size /1024)
            # size_str= f"{bucket_kib}KB"
            bucket_size2=bucket_size /1024
            if bucket_size < (1024 * 1024):
                size_str = f"{bucket_size / 1024:.2f} KB"
            else:
                size_str = f"{bucket_size / (1024 * 1024):.2f} MB"

            # Get bucket information
            bucket_info.append({
                "name": bucket.name,
                "created": creation_date,
                "size": size_str,
                "size_value":round(bucket_size2),
                "objects": num_objects
            })
        
        return {"buckets": bucket_info}
        
    except Exception as e:
        return {"error": str(e)}

def get_bucket_size_recursive(minio_client, bucket_name, prefix=""):
    total_size = 0
    objects = minio_client.list_objects(bucket_name, prefix=prefix, recursive=True)
    for obj in objects:
        total_size += obj.size
    return total_size


# #authorization part
# SECRET_KEY ="KlgH6AzYDeZeGwD288to 79I3vTHT8wp7" 
# ALGORITHM = "HS256" 
# bcrypt_context =CryptContext(schemes=["bcrypt"],deprecated="auto")
# models.Base.metadata.create_all(bind=engine)
# oauth2_bearer = OAuth2PasswordBearer(tokenUrl="token")
# async def get_current_user(token:str = Depends(oauth2_bearer)):
#     try:
#         payload = jwt.decode(token,SECRET_KEY, algorithms=[ALGORITHM])
#         username:str = payload.get("sub")
#         user_id:int =payload.get("id")
#         if username is None or user_id is None:
#             raise get_user_exception()
#         return{"username":username,"id":user_id}
#     except JWTError:
#         raise get_user_exception()
# def get_user_exception():
#     credentials_exception =HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="could not validate credentials",
#         headers={"WWW-Authenticate":"Bearer"},
#     )
#     return credentials_exception
# def token_exception():
#     token_exception_response =HTTPException(
#     status_code=status.HTTP_401_UNAUTHORIZED,
#     detail="incorrect username or password",
#     headers={"WWW-Authenticate":"Bearer"}
#     )
#     return token_exception_response
# def get_db():
#     try:
#         db=SessionLocal()
#         yield db
#     finally:
#         db.close()
# @router.get("/list")
# async def list_buckets(db:Session=Depends(get_db),
#                        user:dict=Depends(get_current_user)):
#     try:
#         new=db.query(models.Users).filter(models.Users.user_id == user.get('id')).first()
#         if new.User_type == "admin":
#             # Admin user, list all buckets
#             bucket_names = [bucket.name for bucket in minio_client.list_buckets()]
#         elif new.User_type == "regular_user":
#             # Regular user, list user-specific buckets
#             user_bucket_name = new.bucket_name
            #   user_files ={}
            #   return{"user_files":user_files}


#         bucket_info = []
#         for bucket in minio_client.list_buckets():
#             objects = minio_client.list_objects(bucket.name)
#             num_objects = len([obj for obj in objects])
#          # Format the bucket creation date in the desired timezone format
#             creation_date = bucket.creation_date.astimezone(timezone(timedelta(hours=5, minutes=30))).strftime('%Y-%m-%d %H:%M:%S %Z')
#             bucket_size = get_bucket_size_recursive(minio_client, bucket.name)
#             # Adjust size representation to include "KB" for sizes below 1 MiB
#             # bucket_mib =bucket_size / (1024*1024)
#             # bucket_kib =int(bucket_size /1024)
#             # size_str= f"{bucket_kib}KB"
#             bucket_size2=bucket_size /1024
#             if bucket_size < (1024 * 1024):
#                 size_str = f"{bucket_size / 1024:.2f} KB"
#             else:
#                 size_str = f"{bucket_size / (1024 * 1024):.2f} MB"

#             # Get bucket information
#             bucket_info.append({
#                 "name": bucket.name,
#                 "created": creation_date,
#                 "size": size_str,
#                 "size_value":round(bucket_size2),
#                 "objects": num_objects
#             })

#         return {"buckets": bucket_info}

#     except Exception as e:
#         return {"error": str(e)}
# def get_bucket_size_recursive(minio_client, bucket_name, prefix=""):
#     total_size = 0
#     objects = minio_client.list_objects(bucket_name, prefix=prefix, recursive=True)
#     for obj in objects:
#         total_size += obj.size
#     return total_size



# from fastapi import Depends, FastAPI, HTTPException
# from minio import Minio
# from sqlalchemy.orm import Session

# # ... Import necessary modules and create FastAPI app ...

# # Initialize MinIO client
# minio_client = Minio(
#     endpoint='your_minio_endpoint',
#     access_key='your_access_key',
#     secret_key='your_secret_key',
#     secure=True
# )

# def get_assigned_buckets(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
#     if current_user.user_type == "admin":
#         assigned_buckets = [bucket.name for bucket in minio_client.list_buckets()]
#     else:
#         assigned_buckets = db.query(AssignedBucket.bucket_name).filter(AssignedBucket.user_id == current_user.id).all()
#         assigned_buckets = [bucket[0] for bucket in assigned_buckets]
    
#     return assigned_buckets

# @app.get("/user/buckets")
# def read_user_buckets(assigned_buckets: list = Depends(get_assigned_buckets)):
#     return {"assigned_buckets": assigned_buckets}




#adding files download

# class download2(BaseModel):
#     bucket_name: str
#     file_path: str

# class download(BaseModel):
#     bucket_name:str
#     file_path:str

# @router.post("/file/download")
# async def download_file(file: download):
#     try:
#         # Generate a pre-signed URL for the file
#         url = generate_presigned_url(file.bucket_name, file.file_path)
        
#         # Return the URL to the client
#         return JSONResponse(content={"download_url": url})
#     except Exception as e:
#         return {"error": "Failed to generate download URL"}

# def generate_presigned_url(bucket_name, file_path):
#     try:
#         # Generate a pre-signed URL for the file that expires in some time
#         url = minio_client.presigned_get_object(bucket_name, file_path, expires=timedelta(minutes=30))
#         return url
#     except Exception as e:
#         # Handle errors appropriately
#         raise e




#add something file download and folder download

class download(BaseModel):
    bucket_name:str
    path:str

@router.post("/file/download")
async def download_item(file2:download):
    try:
        # Check if the path represents a file
        is_file = is_path_a_file(file2.bucket_name, file2.path)
        if is_file:
            # Generate a pre-signed URL for the file
            url = generate_presigned_url(file2.bucket_name, file2.path)
            return {"download_url": url}
        else:
            # Generate a pre-signed URL for a zip archive of the folder
            zip_url = generate_presigned_zip_url(file2.bucket_name,file2.path)
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
        # Handle errors appropriately
        raise e



#it is another method for reducing all buckets buts size not giving

# def get_bucket_info(bucket):
#     objects = minio_client.list_objects(bucket.name)
#     num_objects = len([obj for obj in objects])
    
#     creation_date = bucket.creation_date.astimezone(timezone(timedelta(hours=5, minutes=30))).strftime('%Y-%m-%d %H:%M:%S %Z')
    
#     bucket_size = 0
#     for obj in objects:
#         bucket_size += obj.size
    
#     if bucket_size < (1024 * 1024):
#         size_str = f"{bucket_size / 1024:.2f} KB"
#     else:
#         size_str = f"{bucket_size / (1024 * 1024):.2f} MB"
    
#     return {
#         "name": bucket.name,
#         "created": creation_date,
#         "size": size_str,
#         "objects": num_objects,
#     }

# @router.get("/list")
# def list_buckets():
#     try:
#         bucket_info = []

#         # Fetch all buckets once
#         buckets = minio_client.list_buckets()

#         # Fetch bucket information synchronously
#         for bucket in buckets:
#             bucket_info.append(get_bucket_info(bucket))
        
#         return {"buckets": bucket_info}
        
#     except Exception as e:
#         return {"error": str(e)}




# @router.get("/get_bucket_data/{bucket_name}")
# async def get_minio_data(bucket_name: str):
#     objects = minio_client.list_objects(bucket_name, recursive=True)

#     tree_path = {}

#     # Call the recursive function to get the folder structure
#     tree_path = get_bucket_data_recursive(bucket_name, tree_path, objects)

#     # Convert the MinIO data into the desired folder structure format
#     folder_structure = convert_to_folder_structure({bucket_name: tree_path}, bucket_name=bucket_name)

#     return folder_structure


# it is simple file type method
# def convert_to_folder_structure(data, current_path=""):
#     folder_structure = []

#     for key, value in data.items():
#         folder_path = current_path + "/" + key if current_path else key

#         if isinstance(value, dict):
#             folder_structure.append({
#                 "type": "folder",
#                 "folderName":key,
#                 "path": folder_path,
#                 "files": convert_to_folder_structure(value, current_path=folder_path)
#             })
#         else:
#             # Extract the file type from the filename
#             file_type = key.split('.')[-1]

#             folder_structure.append({
#                 "type": "file",
#                 "filename": key,
#                 "filetype": '.' + file_type,
#                 "fileurl": value
#             })

#     return folder_structure

# def get_bucket_data_recursive(bucket_name, tree_path, objects):
#     for obj in objects:
#         levels = obj.object_name.split("/")
#         file = levels.pop()
#         acc = tree_path

#         for p in levels:
#             acc = acc.setdefault(p, {})

#         acc[file] = obj.object_name

#     return tree_path



# @router.get("/get_bucket_data/{bucket_name}")
# async def get_minio_data(bucket_name: str):
#     objects = minio_client.list_objects(bucket_name, recursive=True)

#     tree_path = {}

#     # Call the recursive function to get the folder structure
#     tree_path = get_bucket_data_recursive(bucket_name, tree_path, objects)

#     # Convert the MinIO data into the desired folder structure format
#     folder_structure = convert_to_folder_structure({bucket_name: tree_path})

#     return folder_structure 

#list methods
# @router.get("/list")
# async def list_buckets():
#     try:
#         bucket_info = []
#         for bucket in minio_client.list_buckets():
#             objects = minio_client.list_objects(bucket.name)
#             num_objects = len([obj for obj in objects])
#             bucket_info.append({"name": bucket.name, "length": num_objects})
#         return {"buckets": bucket_info}
#     except Exception as e:
#         return {"error": str(e)}


# @router.get("/get_objects/{bucket_name}")
# async def get_objects_from_minio(bucket_name: str):
#     try:
#         # Fetch all objects in the specified bucket
#         objects = minio_client.list_objects(bucket_name, recursive=True)

#         # Create a list to hold object names (including folder structure)
#         object_names = []

#         for obj in objects:
#             # The object name contains the full path, so we add it to the list
#             object_names.append(obj.object_name)

#         return object_names
#     except Exception as e:
#         raise HTTPException(status_code=404, detail=str(e))