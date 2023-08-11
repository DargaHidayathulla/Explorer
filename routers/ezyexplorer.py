import sys
sys.path.append( "..")
from fastapi import Depends,HTTPException,status,APIRouter
import subprocess
import json
from enum import Enum
from minio import Minio
# from minio.error import S3Error
from typing import Optional
import os
# import requests
import asyncio
router = APIRouter(
    prefix="/ezy",
    tags=["ezy-explorer"],
    responses={401:{"user":"not authorized"}}
)
minio_client = Minio(
    "192.168.1.151:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False,
    )



# @router.get("/bucket_info")
# async def bucket_info():
#     # Construct the command as a list of strings
#     command = ["./mc", "ls", "minio", "--json"]

#     try:
#         # Run the command using subprocess and capture the output
#         result = subprocess.run(command, capture_output=True, text=True, check=True)
#         bucket_info_json = result.stdout  # Captured JSON output

#         # Parse each line separately and create a list of parsed objects
#         bucket_info = [json.loads(line) for line in bucket_info_json.splitlines()]
#         return bucket_info
#     except subprocess.CalledProcessError as e:
#         return {"error": f"Error: {e.returncode}\n{e.stderr}"}


#we accessed sir code
'''b:enable user'''
@router.get("/user_enable/{username}")
def user_enable(username):
    try:
        cruser=f"./mc admin user enable minio {username}"
        subprocess.run(cruser, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error creating minio user: {e}")
    return{"message": "User enable is successfully"}


'''a:create user'''
@router.get("/user_create/{usr_id}/{usr_pwd}")
def create_minio_user(username, password):
    try:
        cruser_command = f"./mc admin user add minio {username} {password}"
        subprocess.run(cruser_command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error creating MinIO user: {e}")
    return{"message": "User is created successfully"}

#user disable
@router.get("/user_disable/{username}")
def disable_user(username):
    try:
        cruser_command=f"./mc admin user disable minio {username}"
        subprocess.run(cruser_command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error creating MinIO user: {e}")
    return{"message": "user_disable is successfully"}


# '''d:Create bucket (policy will be created starting with “po_” followed by bucket name)'''

@router.get("/bucket_create/{bucket_name}")
def create_bucket(bucket_name: str):
    try:
        # Create bucket.
        minio_client.make_bucket(bucket_name)
        
        # Create policy
        def create_policy(bucket_name):
            fdata1 = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": ["s3:*"],
                        "Resource": [f"arn:aws:s3:::{bucket_name}/*"]
                    }
                ]
            }
            with open("abfile.txt", "w") as f:
                json.dump(fdata1, f, indent=2)
                
        create_policy(bucket_name=bucket_name)
        curser1 = f'./mc admin policy create minio "po_{bucket_name}" abfile.txt'
        subprocess.run(curser1, shell=True, check=True)  # Check the subprocess return value
        
        return {"message": "Bucket is created successfully"}
    except Exception as e:
        print("Error:", str(e))
        return {"error": "An error occurred while creating the bucket"}


#attach policy to users
@router.get("/policy_attach/{poname}/{usrname}")
async def get_user_attach_policy(poname: str, usrname: str):
    poname_list=poname.split(",")
    try:
    # Build the command using an f-string
        for poname in poname_list :
            cmd = f"./mc admin policy attach minio {poname} --user {usrname}"
   
        # Run the subprocess and capture the return code
            return_code = subprocess.run(cmd, shell=True, check=True)
        return {"message": "Policy's is attached to the user successfully"}
    except subprocess.CalledProcessError as e:
        return {"message": f"Error attaching policy's to the user: {str(e)}"}


# #detach policy
@router.get("/policy_detach/{poname}/{usrname}")
async def get_user_attach_policy(poname: str, usrname: str):
    poname_list=poname.split(",")
    try:
        for poname in poname_list:
    # Build the command using an f-string
            cmd = f"./mc admin policy detach minio {poname} --user {usrname}"
        # Run the subprocess and capture the return code
            return_code = subprocess.run(cmd, shell=True, check=True)
        return {"message": "Policy's is deattached to the user successfully"}
    except subprocess.CalledProcessError as e:
        return {"message": f"Error deattaching policy's to the user: {str(e)}"}


#add group and users
@router.get("/group_create/{grpname}/{usrname}")
async def group_create(grpname: str, usrname: str):
    usrname_list=usrname.split(",")
    try:
        for usrname in usrname_list:
            cmd = ["./mc", "admin", "group", "add", "minio", grpname, usrname]
            return_code = subprocess.run(cmd, check=True)
        return {"message": "Group is created successfully"}
    except subprocess.CalledProcessError as e:
        return {"message": f"Error: Group creation failed with subprocess error: {str(e)}"}




'''h:Attach policies to a group'''
@router.get("/group_attach_policy/{policy_name}/{group_name}")
async def attachpolicy_group(policy_name:str,group_name:str):
    policy_list=policy_name.split(",")
    try:
        for policy_name in policy_list:
            cmd = f"./mc admin policy attach minio {policy_name} --group {group_name}"
            policyattach_group = subprocess.run(cmd,shell=True,check=True)
        return{"message": "policy attached to group successfully"}
    except subprocess.CalledProcessError as e :
        return{"message":f"Error attaching is policy to the group:{str(e)}"}

#remove users from group
@router.get("/group_remove_user/{group_name}/{user_names}")
async def remove_user_group(group_name: str, user_names: str):
    try:
        users = user_names.split(",")
        for user in users:
            cmd = f"./mc admin group remove minio {group_name} {user.strip()}"
            remove_user = subprocess.run(cmd, shell=True, check=True)
        return {"message": "Users removed from group successfully"}
    except subprocess.CalledProcessError as e:
        return {"message": f"Error removing user from group: {str(e)}"}

'''k:Detach policy from group'''
@router.get("/group_detach_policy/{policy_name}/{group_name}")
async def detachpolicy_group(policy_name:str,group_name:str):
    try:
        policy_list=policy_name.split(",")
        for policy_name in policy_list:
            cmd = f"./mc admin policy detach minio {policy_name} --group {group_name}"
            remove_policy = subprocess.run(cmd,shell=True,check=True)
        return {"message":"policy removed from group successfully"}
    except subprocess.CalledProcessError as e:
        return{"message":f"error policy not removing from group:{str(e)}"}
    
# '''Disable group'''
@router.get("/group_disable/{group_name}")
async def disable_group(group_name:str):
    cmd = f"./mc admin group disable minio {group_name}"
    disable_group = subprocess.run(cmd,shell=True,check=True)
    return{"message": "group is disabled successfully"}


#remove group it has no users in group they remove
@router.get("/group_remove/{group_name}")
async def remove_group(group_name:str):
    try:
        cmd = f"./mc admin group rm minio {group_name}"
        disable_group = subprocess.run(cmd,shell=True,check=True)
        return{"message": "group is removed successfully"}
    except subprocess.CalledProcessError as e:
        return{"message":f"error for removing from group:{str(e)}"}

# users list
@router.get("/user_list")
async def user_list():
    try:
        cmd=f"./mc admin user ls minio --json"
        result=subprocess.run(cmd,capture_output=True,text=True,shell=True)
        return result
    except Exception as e:
        return {"error":str(e)}
 
#extra purpose
# @router.get("/minio_users")
# async def get_minio_users():
#     try:
#         # Run the mc command to list MinIO users in JSON format
#         cruser_command = "./mc admin user ls minio --json"
#         result = subprocess.run(cruser_command, capture_output=True, text=True, shell=True)
#         return result.stdout
#     except Exception as e:
#         return {"error": str(e)}

#policy list

@router.get("/policy_list")
async def policy_list():
    command = ["./mc", "admin", "policy", "ls", "minio", "--json"]

    # Run the command using subprocess and capture the output
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        policies_json = result.stdout  # Captured JSON output
        
        # Parse the JSON response
        policies = [json.loads(line)["policy"] for line in policies_json.splitlines()]
        return {"policies": policies}
    except subprocess.CalledProcessError as e:
        return {"error": f"Error: {e.returncode}\n{e.stderr}"}

#groups list
@router.get("/group_list")
async def group_list():
    # Construct the command as a list of strings
    command = ["./mc", "admin", "group", "ls", "minio", "--json"]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        groups_json = result.stdout  # Captured JSON output
        return groups_json
    except subprocess.CalledProcessError as e:
        return f"Error: {e.returncode}\n{e.stderr}"


#group info
@router.get("/group_info/{group_name}")
def group_info(group_name: str):
    try:
        group_info_command = f"./mc admin group info minio {group_name}"
        group_info_result = subprocess.run(
            group_info_command, shell=True, capture_output=True, text=True
        )
        output = group_info_result.stdout.strip()
        members_line = output.split("Members:", 1)[-1].strip()
        members_list = members_line.split(", ")
        return {"group_info": output, "members": members_list}
    except Exception as e:
        return {"error": str(e)}

'''p.server information'''
@router.get("/server_info")
def server_information():
    command = ["./mc", "admin", "info", "minio", "--json"]
    # cruser = f"./mc admin info minio--json"
    server_information = subprocess.run(command,capture_output=True,text=True)
    return server_information
