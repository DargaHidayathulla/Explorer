


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




#user authentication based on login credentials
from fastapi import Depends, HTTPException

# Assume you have a function to get the user's role from the token or session
def get_user_type(current_user: dict = Depends(get_current_user)):
    return current_user.get("user_type")

@router.get("/list")
async def list_buckets(user_type: str = Depends(get_user_type)):
    try:
        bucket_info = []
        assigned_buckets = []

        # Assuming you have a function to get the assigned buckets for the user
        if user_type == "admin":
            assigned_buckets = [bucket.name for bucket in minio_client.list_buckets()]
        elif user_type == "regular":
            assigned_buckets = get_assigned_buckets_for_user(current_user.get("username"))

        for bucket_name in assigned_buckets:
            bucket = minio_client.get_bucket_stat(bucket_name)
            objects = minio_client.list_objects(bucket_name)
            num_objects = len([obj for obj in objects])

            creation_date = bucket.creation_date.astimezone(timezone(timedelta(hours=5, minutes=30))).strftime('%Y-%m-%d %H:%M:%S %Z')
            bucket_size = get_bucket_size_recursive(minio_client, bucket_name)
            bucket_size2 = bucket_size / 1024
            size_str = f"{bucket_size / 1024:.2f} KB" if bucket_size < (1024 * 1024) else f"{bucket_size / (1024 * 1024):.2f} MB"

            bucket_info.append({
                "name": bucket_name,
                "created": creation_date,
                "size": size_str,
                "size_value": round(bucket_size2),
                "objects": num_objects
            })

        return {"buckets": bucket_info}

    except Exception as e:
        return {"error": str(e)}


#another
@router.get("/list")
async def list_buckets(current_user: dict = Depends(get_current_user)):
    try:
        bucket_info = []

        if current_user.get("user_type") == "admin":
            # Admin user can see all buckets
            assigned_buckets = [bucket.name for bucket in minio_client.list_buckets()]
        else:
            # Regular user can only see their assigned buckets
            assigned_buckets = get_assigned_buckets_for_user(current_user.get("username"))

        for bucket_name in assigned_buckets:
            bucket = minio_client.get_bucket_stat(bucket_name)
            objects = minio_client.list_objects(bucket_name)
            num_objects = len([obj for obj in objects])

            creation_date = bucket.creation_date.astimezone(timezone(timedelta(hours=5, minutes=30))).strftime('%Y-%m-%d %H:%M:%S %Z')
            bucket_size = get_bucket_size_recursive(minio_client, bucket_name)
            bucket_size2 = bucket_size / 1024
            size_str = f"{bucket_size / 1024:.2f} KB" if bucket_size < (1024 * 1024) else f"{bucket_size / (1024 * 1024):.2f} MB"

            bucket_info.append({
                "name": bucket_name,
                "created": creation_date,
                "size": size_str,
                "size_value": round(bucket_size2),
                "objects": num_objects
            })

        return {"buckets": bucket_info}

    except Exception as e:
        return {"error": str(e)}

#creating the bucket and policy
import json
import subprocess
from fastapi import FastAPI

app = FastAPI()

@app.post("/bucket_create")
def create_bucket_and_policy(bucket: create_bucket):
    try:
        # Create bucket.
        minio_client.make_bucket(bucket.bucket_name)

        # Create and attach policy
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": ["s3:*"],
                    "Resource": [f"arn:aws:s3:::{bucket.bucket_name}/*"]
                }
            ]
        }

        # Convert policy to a JSON string
        policy_json = json.dumps(policy)

        # Attach policy to the bucket
        subprocess.run(f'./mc admin policy add minio {bucket.bucket_name} - <<EOF\n{policy_json}\nEOF', shell=True, check=True)

        return {"message": "Bucket and policy created successfully"}
    except Exception as e:
        print("Error:", str(e))
        return {"error": "An error occurred while creating the bucket and policy"}

@app.get("/policy_attach/{poname}/{usrname}")
async def attach_policy_to_user(poname: str, usrname: str):
    poname_list = poname.split(",")
    try:
        for poname in poname_list:
            cmd = f'./mc admin policy set minio {usrname} {poname}'
            return_code = subprocess.run(cmd, shell=True, check=True)

        return {"message": "Policy attached to user successfully"}
    except subprocess.CalledProcessError as e:
        return {"message": f"Error attaching policy to user: {str(e)}"}
class BucketModel(BaseModel):
    buckets: str
    username: str

buckets_db = {}  # A dictionary to store user buckets

@router.post("/user/add_bucket22")
async def add_bucket(bucket: BucketModel):
    try:
        new_buckets = bucket.buckets.split(",")

        if bucket.username not in buckets_db:
            buckets_db[bucket.username] = []

        # Remove previously attached buckets for the user
        existing_buckets = buckets_db[bucket.username]
        for existing_bucket in existing_buckets:
            cmd_detach = f"./mc admin policy detach minio {existing_bucket} --user {bucket.username}"
            try:
                return_code = subprocess.run(cmd_detach, shell=True, check=True)
            except subprocess.CalledProcessError as e:
                pass

        # Attach new buckets
        attached_buckets = []
        failed_buckets = []
        for new_bucket in new_buckets:
            cmd_attach = f"./mc admin policy attach minio {new_bucket} --user {bucket.username}"
            try:
                return_code = subprocess.run(cmd_attach, shell=True, check=True)
                attached_buckets.append(new_bucket)
            except subprocess.CalledProcessError as e:
                failed_buckets.append(new_bucket)

        buckets_db[bucket.username] = new_buckets

        response_message = "Buckets have been attached to the user successfully"
        if attached_buckets:
            response_message += f": {', '.join(attached_buckets)} attached"
        if failed_buckets:
            response_message += f", but failed to attach: {', '.join(failed_buckets)}"

        return {"message": response_message, "buckets": new_buckets}
    except Exception as e:
        return {"message": f"Error: {str(e)}"}
import shelve
import subprocess
from fastapi import FastAPI, HTTPException

app = FastAPI()

buckets_db = shelve.open("buckets_db")  # Open or create the storage file

class BucketModel1(BaseModel):
    buckets: str
    username: str

@app.post("/user/add_bucket")
async def add_bucket(bucket: BucketModel1):
    try:
        new_buckets = bucket.buckets.split(",")

        if bucket.username not in buckets_db:
            buckets_db[bucket.username] = []

        # Remove previously attached buckets for the user
        existing_buckets = buckets_db[bucket.username]
        for existing_bucket in existing_buckets:
            # Detach logic here...

        # Attach new buckets if provided
        for new in new_buckets:
            # Attach logic here...

        buckets_db[bucket.username] = new_buckets
        return {"message": "Buckets are attached to the user successfully"}

    except Exception as e:
        return {"message": f"Error: {str(e)}"}

@app.get("/user/buckets1/{username}")
async def get_user_buckets(username: str):
    user_buckets = buckets_db.get(username, [])
    return {"username": username, "buckets": user_buckets}
# #groups list
# @router.get("/group_list3")
# async def group_list():
#     # Construct the command as a list of strings
#     command = ["./mc", "admin", "group", "ls", "minio", "--json"]
#     try:
#         result = subprocess.run(command, capture_output=True, text=True, check=True)
#         groups_json = result.stdout  # Captured JSON output
#         groups =[json.loads(line)["groups"] for line in groups_json.splitlines()]

#         return{"groups":groups}
#     except subprocess.CalledProcessError as e:
#         return f"Error: {e.returncode}\n{e.stderr}"