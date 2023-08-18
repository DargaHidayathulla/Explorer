import sys
sys.path.append( "..")
from fastapi import Depends,HTTPException,status,APIRouter,Query
import subprocess
from pydantic import BaseModel
import json
import models
from enum import Enum
from minio import Minio
# from minio.error import S3Error
from typing import Optional
import os

import models
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from database import SessionLocal,engine
# import requests
import asyncio
router = APIRouter(
    prefix="/api",
    tags=["ezy-explorer"],
    responses={401:{"user":"not authorized"}}
)
minio_client = Minio(
    "192.168.1.151:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False,
    )

def get_db():
    try:
        db=SessionLocal()
        yield db
    finally:
        db.close()

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
# '''b:enable user'''
# @router.get("/user_enable/{username}")
# def user_enable(username):
#     try:
#         cruser=f"./mc admin user enable minio {username}"
#         subprocess.run(cruser, shell=True, check=True)
#     except subprocess.CalledProcessError as e:
#         raise RuntimeError(f"Error creating minio user: {e}")
#     return{"message": "User enable is successfully"}


# '''a:create user'''
# @router.get("/user_create/{usr_id}/{usr_pwd}")
# def create_minio_user(username, password):
#     try:
#         cruser_command = f"./mc admin user add minio {username} {password}"
#         subprocess.run(cruser_command, shell=True, check=True)
#     except subprocess.CalledProcessError as e:
#         raise RuntimeError(f"Error creating MinIO user: {e}")
#     return{"message": "User is created successfully"}

#user disable
# @router.get("/user_disable/{username}")
# def disable_user(username):
#     try:
#         cruser_command=f"./mc admin user disable minio {username}"
#         subprocess.run(cruser_command, shell=True, check=True)
#     except subprocess.CalledProcessError as e:
#         raise RuntimeError(f"Error creating MinIO user: {e}")
#     return{"message": "user_disable is successfully"}


# '''d:Create bucket (policy will be created starting with “po_” followed by bucket name)'''
class create_bucket(BaseModel):
    bucket_name:str

@router.post("/bucket_create")
def create_bucket(bucket:create_bucket):
    try:
        # Create bucket.
        minio_client.make_bucket(bucket.bucket_name)
        
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
                
        create_policy(bucket_name=bucket.bucket_name)
        curser1 = f'./mc admin policy create minio "{bucket.bucket_name}" abfile.txt'
        subprocess.run(curser1, shell=True, check=True)  # Check the subprocess return value
        
        return {"message": "Bucket is created successfully"}
    except Exception as e:
        print("Error:", str(e))
        return {"error": "An error occurred while creating the bucket"}


# #attach policy to users
# @router.get("/policy_attach/{poname}/{usrname}")
# async def get_user_attach_policy(poname: str, usrname: str):
#     poname_list=poname.split(",")
#     try:
#     # Build the command using an f-string
#         for poname in poname_list :
#             cmd = f"./mc admin policy attach minio {poname} --user {usrname}"
   
#         # Run the subprocess and capture the return code
#             return_code = subprocess.run(cmd, shell=True, check=True)
#         return {"message": "Policy's is attached to the user successfully"}
#     except subprocess.CalledProcessError as e:
#         return {"message": f"Error attaching policy's to the user: {str(e)}"}


class Bucketmodel1(BaseModel):
    buckets:str
    username:str


def get_user_policies(username):
    try:
        # Get the current policies attached to the user
        cmd_get_policies = f"./mc admin user info minio {username} --json"
        user_info_output = subprocess.check_output(cmd_get_policies, shell=True).decode()
        user_info = json.loads(user_info_output)
        
        current_policies = user_info.get("policyName", [])
        return current_policies
    except subprocess.CalledProcessError as e:
        print(f"Error getting user policies: {str(e)}")
        return []

def detach_policies(username, policies_to_detach):
    try:
        if policies_to_detach:
            policy=policies_to_detach.split(",")
            for policy_name in policy:
              cmd_detach = f"./mc admin policy detach minio {policy_name} --user {username}"
              subprocess.run(cmd_detach, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error detaching policies: {str(e)}")

@router.post("/user/add_bucket")
async def update_user_policies(bucket:Bucketmodel1):
    try:
        new_policies = bucket.buckets.split(",")

        # Get the current policies attached to the user
        current_policies = get_user_policies(bucket.username)

        # Detach the existing policies
        detach_policies(bucket.username, current_policies)
        
        # Attach the new policies
        if len(new_policies) > 0 and new_policies[0] != "":
            for policy_name in new_policies:
               cmd_attach = f"./mc admin policy attach minio {policy_name} --user {bucket.username}"
               subprocess.run(cmd_attach, shell=True, check=True)
            return {"message": "Policies updated successfully."}
        else:
            return{"message":"all existing buckets are detached"}

    except subprocess.CalledProcessError as e:
        return {"message": f"Error updating policies: {str(e)}"}




 
# #console admin have they users table they usertype also change
# @router.get("/policy_attach/{poname}/{usrname}")
# async def attach_policy_to_user(poname: str, usrname: str, db: Session = Depends(get_db)):
#     try:
#         # Attach policies to the user using the mc tool
#         cmd = f"./mc admin policy attach minio {poname} --user {usrname}"
#         return_code = subprocess.run(cmd, shell=True, check=True)

#         # Check if the attached policy is "consoleAdmin"
#         is_console_admin_policy = "consoleAdmin" in poname

#         # Update the usertype in the PostgreSQL database
#         if is_console_admin_policy:
#             user = db.query(models.Users).filter(models.Users.email == usrname).first()
#             if user:
#                 user.User_type = "admin"
#                 db.commit()

#         return {"message": "Policy attached to the user successfully"}
#     except subprocess.CalledProcessError as e:
#         return {"message": f"Error attaching policy to the user: {str(e)}"}

#detach policy
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

# # users list
# @router.get("/user_list1")
# async def user_list():
#     try:
#         cmd=f"./mc admin user ls minio --json"
#         result=subprocess.run(cmd,capture_output=True,text=True,shell=True)
#         return result
#     except Exception as e:
#         return {"error":str(e)}

#bases on front requirement

@router.get("/user_list")
async def user_list():
    try:
        cmd = "./mc admin user ls minio --json"
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)

        if result.returncode == 0:
            user_data = result.stdout.strip()
            user_list = []

            for user_info in user_data.split('\n'):
                user_json = json.loads(user_info)
                name = user_json.get("accessKey")
                policy_name = user_json.get("policyName")
                user_status = user_json.get("userStatus")
                member =user_json.get("memberOf")
                user_list.append({"name": name,"bucketname":policy_name,"userstatus":user_status,"member":member})
            user_list.sort(key=lambda x: x["name"])
            return user_list
        else:
            return {"error": "Failed to retrieve user list"}

    except Exception as e:
        return {"error": str(e)}






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




# #groups list  
# @router.get("/group_list")
# async def group_list():
#     # Construct the command as a list of strings
#     command = ["./mc", "admin", "group", "ls", "minio", "--json"]
#     try:
#         result = subprocess.run(command, capture_output=True, text=True, check=True)
#         groups_json = result.stdout  # Captured JSON output
#         groups = []

#         # Parse JSON output and extract group names
#         for line in groups_json.splitlines():
#             group_info = json.loads(line)
#             if "groups" in group_info:
#                 groups.extend(group_info["groups"])
#         return {"groups": groups}
#     except subprocess.CalledProcessError as e:
#         return {"error": f"Error: {e.returncode}\n{e.stderr}"}




# @router.get("/group_details/{group_name}")
# async def group_details(group_name: str):
#     try:
#         # Get detailed information about the group using mc command
#         command = ["./mc", "admin", "group", "info", "minio", group_name, "--json"]
#         result = subprocess.run(command, capture_output=True, text=True, check=True)
#         group_info = json.loads(result.stdout)
#         print(group_info)
#         # Spliting grouppoliy string to list based on policies
#         group_info["groupPolicy"] = group_info["groupPolicy"].split(",")
#         print(group_info)

#         return {"group_info": group_info}
#     except subprocess.CalledProcessError as e:
#         return {"error": f"Error: {e.returncode}\n{e.stderr}"}



@router.get("/group_list")
async def group_list():
    # Construct the command as a list of strings
    command = ["./mc", "admin", "group", "ls", "minio", "--json"]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        groups_json = result.stdout  # Captured JSON output
        groups = []

        # Parse JSON output and extract group names
        for line in groups_json.splitlines():
            group_info = json.loads(line)
            if "groups" in group_info:
                groups.extend(group_info["groups"])

        # Now retrieve policies and users for each group
        groups_with_policies_users = []
        for group in groups:
            group_info_command = ["./mc", "admin", "group", "info", "minio", group, "--json"]
            try:
                group_result = subprocess.run(group_info_command, capture_output=True, text=True, check=True)
                group_info_json = group_result.stdout
                group_info = json.loads(group_info_json)
                policies = group_info.get("groupPolicy", [])
                users = group_info.get("members", [])
                groups_with_policies_users.append({
                    "groupName": group,
                    "groupPolicy": policies.split(","),
                    "members": users
                })
            except subprocess.CalledProcessError as e:
                return {"error": f"Error: {e.returncode}\n{e.stderr}"} 
        return {"groups": groups_with_policies_users}
    except subprocess.CalledProcessError as e:
        return {"error": f"Error: {e.returncode}\n{e.stderr}"}
    



# @router.get("/group_create/{grpname}")
# async def group_create(grpname: str):
#     try:
#         # Create a "group" user (without associating any policies)
#         group_user = f"group_{grpname}"
#         minio_client.make_group(group_user)
        
#         return {"message": f"Group '{grpname}' is created successfully"}
#     except Exception as e:
#         return {"message": f"Error: Group creation failed with error: {str(e)}"}




'''p.server information'''
@router.get("/server_info")
def server_information():
    command = ["./mc", "admin", "info", "minio", "--json"]
    # cruser = f"./mc admin info minio--json"
    server_information = subprocess.run(command,capture_output=True,text=True)
    return server_information

#userstatus

class UserStatus(BaseModel):
    username: str
    action: bool  # Change the action type to bool

@router.post("/user_status/")
def user_status(user_status: UserStatus, db: Session = Depends(get_db)):
    try:
        if isinstance(user_status.action, bool):
            # Convert the boolean action to the corresponding string value
            action_str = "enable" if user_status.action else "disable"

            # Run MinIO command to enable or disable user based on action_str
            cruser_command = f"./mc admin user {action_str} minio {user_status.username}"
            subprocess.run(cruser_command, shell=True, check=True)
            # Update the user status in the database based on the action
            user = db.query(models.Users).filter(models.Users.email == user_status.username).first()
            if user:
                user.status = user_status.action
                db.commit()
            else:
                raise HTTPException(status_code=404, detail="User not found")
            
            return {"message": f"User {action_str} is successful"}

        else:
            raise HTTPException(status_code=400, detail="Invalid action")

    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Error performing action: {e}")

#single api for attach and detach polices from group


# @router.post("/manage_group_policy")
# async def manage_group_policy(policy_name: str, group_name: str, attach: bool):
#     try:
#         cmd_action = "attach" if attach else "detach"
        
#         policy_list = policy_name.split(",")
#         for policy in policy_list:
#             cmd = f"./mc admin policy {cmd_action} minio {policy} --group {group_name}"
#             subprocess.run(cmd, shell=True, check=True)
        
#         action_message = "attached to" if attach else "detached from"
#         return {"message": f"Policy {action_message} group successfully"}
#     except subprocess.CalledProcessError as e:
#         action_message = "attaching to" if attach else "detaching from"
#         return {"message": f"Error {action_message} group: {str(e)}"}












