import sys
sys.path.append( "..")
from fastapi import Depends,HTTPException,APIRouter
import subprocess
from pydantic import BaseModel
import json,io
import models
from minio import Minio

from sqlalchemy.orm import Session
from database import SessionLocal,engine
from routers.auth import get_current_user

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




# '''d:Create bucket  the bucket should be policy'''
class create_bucket(BaseModel):
    bucket_name: str

@router.post("/bucket_create")
def create_bucket(bucket: create_bucket, user: dict = Depends(get_current_user)):
    try:
        bucket_name = bucket.bucket_name

        # Check if the bucket already exists
        if not minio_client.bucket_exists(bucket_name):
            # Create bucket.
            minio_client.make_bucket(bucket_name)
            # folder_name = "SHIJI"
            # minio_client.put_object(bucket_name, f"{folder_name}/", io.BytesIO(b''), 0) 
        
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
            
            curser1 = f'./mc admin policy create minio "{bucket_name}" abfile.txt'
            subprocess.run(curser1, shell=True, check=True)  # Check the subprocess return value
            return {"message": "Bucket is created successfully"}
        else:
            return {"message1": "Bucket already exists"}
    except Exception as e:
        print("Error:", str(e))
        return {"error": "An error occurred while creating the bucket"}




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
async def update_user_policies(bucket:Bucketmodel1,user: dict = Depends(get_current_user)):
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




 


@router.get("/user_list")
async def user_list(user: dict = Depends(get_current_user)):
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









@router.get("/group_list")
async def group_list(user: dict = Depends(get_current_user)):
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
                #if policyies empty or values t
                if isinstance(policies, str):
                    policies = policies.split(",")
                if isinstance(users, str):
                    users = users.split(",")

                groups_with_policies_users.append({
                    "groupName": group,
                    "groupPolicy": policies,
                    "members": users
                })
                groups_with_policies_users.sort(key=lambda x: x["groupName"])
            except subprocess.CalledProcessError as e:
                return {"error": f"Error: {e.returncode}\n{e.stderr}"} 

        return {"groups": groups_with_policies_users}
    except subprocess.CalledProcessError as e:
        return {"error": f"Error: {e.returncode}\n{e.stderr}"}




class group_create(BaseModel):
    group: str

@router.post("/group_create")
async def group_create(group_info: group_create,user: dict = Depends(get_current_user)):
    default_username = "srinivas@gmail.com"  # Change this to your desired default username
    group_name = group_info.group
    
    # Check if the group already exists
    check_cmd = ["./mc", "admin", "group", "list", "minio"]
    check_process = subprocess.Popen(check_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    check_output, check_error = check_process.communicate()
    
    if group_name in check_output.decode():
        # Group already exists, return a message
        return {"exists": f"Group '{group_name}' already exists."}
    
    try:
        # Create the group with the default username
        cmd = ["./mc", "admin", "group", "add", "minio", group_name, default_username]
        return_code = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Remove the default user from the group
        remove_cmd = ["./mc", "admin", "group", "rm", "minio", group_name, default_username]
        remove_return_code = subprocess.run(remove_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Assuming you are using FastAPI, return a JSON response
        return {"created": f"Group '{group_name}' is created successfully with default username: {default_username} and default user removed from the group."}
    
    except subprocess.CalledProcessError as e:
        # Return an error response with details
        raise HTTPException(status_code=500, detail=f"Subprocess error - {str(e)}")
#buckets adding groups
class Groupmodel1(BaseModel):
    groupName:str
    buckets:str


def get_user_policies1(groupName):
    try:
        # Get the current policies of the group 
        cmd_group_policies = f"./mc admin group info minio {groupName} --json"
        group_info_output = subprocess.check_output(cmd_group_policies, shell=True).decode()
        group_info = json.loads(group_info_output)
        
        group_policies = group_info.get("groupPolicy", [])
        return group_policies
    except subprocess.CalledProcessError as e:
        print(f"Error getting group policies: {str(e)}")
        return []

def detach_policies1(groupName, policies_to_detach):
    try:
        if policies_to_detach:
            grp_policy=policies_to_detach.split(",")
            for policy_name in grp_policy:
              cmd_detach = f"./mc admin policy detach minio {policy_name} --group {groupName}"
              subprocess.run(cmd_detach, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error detaching policies: {str(e)}")

@router.post("/group/add_bucket")
async def update_group_policies(bucket:Groupmodel1,user: dict = Depends(get_current_user)):
    try:
        new_policies = bucket.buckets.split(",")

        # Get the current policies attached to the user
        group_policies = get_user_policies1(bucket.groupName)

        # Detach the existing policies
        detach_policies1(bucket.groupName, group_policies)
        
        # Attach the new policies
        if len(new_policies) > 0 and new_policies[0] != "":
            for policy_name in new_policies:
               cmd_attach = f"./mc admin policy attach minio {policy_name} --group {bucket.groupName}"
               subprocess.run(cmd_attach, shell=True, check=True)
            return {"group_update": "Policies updated successfully."}
        else:
            return{"policies":"all existing buckets are detached"}

    except subprocess.CalledProcessError as e:
        return {"error": f"Error updating policies: {str(e)}"}
    

class Groupuser(BaseModel):
    groupName:str
    users:str


def get_user(groupName):
    try:
        # Get the current policies of the group 
        cmd_group_policies = f"./mc admin group info minio {groupName} --json"
        group_info_output = subprocess.check_output(cmd_group_policies, shell=True).decode()
        group_info = json.loads(group_info_output)
        
        group_users = group_info.get("members", [])
        return group_users
    except subprocess.CalledProcessError as e:
        print(f"Error getting group users: {str(e)}")
        return []

def detach_users(groupName, policies_to_detach):
    try:
        if policies_to_detach:
            for policy_name in policies_to_detach:
                # Split each policy_name if it contains commas
                policy_parts = policy_name.split(",")
                for part in policy_parts:
                    remove_cmd = ["./mc", "admin", "group", "rm", "minio", groupName, part] 
                    remove_return_code = subprocess.run(remove_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"Error detaching users: {str(e)}")



@router.post("/group/add_users")
async def update_group_users(user:Groupuser,user2: dict = Depends(get_current_user)):
    try:
        new_policies = user.users.split(",")

        # Get the current users attached to the group
        group_users = get_user(user.groupName)

        # Detach the existing users
        detach_users(user.groupName,group_users)
        
        # Attach the new policies
        if len(new_policies) > 0 and new_policies[0] != "":
            for policy_name in new_policies:
                cmd = ["./mc", "admin", "group", "add", "minio", user.groupName,policy_name ]
                return_code = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return {"group_users": "users updated successfully."}
        else:
            return{"group_member":"all existing users are detached"}

    except subprocess.CalledProcessError as e:
        return {"error": f"Error updating policies: {str(e)}"}




#user_status
class UserAction(BaseModel):
    username: str
    action: bool

@router.post("/user_status")
def perform_user_action(user: UserAction,user3: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        if user.action:
            cruser_command = f"./mc admin user enable minio {user.username}"
        else:
            cruser_command = f"./mc admin user disable minio {user.username}"
        
        subprocess.run(cruser_command, shell=True, check=True)
        
        user1 = db.query(models.Users).filter(models.Users.email == user.username).first()
        if user1:
            user1.status = user.action
            db.commit()
            action_message = "enable" if user.action else "disable"
            return {"message": f"User {action_message} is successful"}
        else:
            raise HTTPException(status_code=404, detail="User not found")
    
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Error performing user action: {e}")















