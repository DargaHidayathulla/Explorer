# from fastapi import FastAPI, HTTPException
# from enum import Enum
# from minio import Minio
# # from minio.error import S3Error
# from typing import Optional
# import json
# import os
# import subprocess
# # import requests
# import asyncio



# app = FastAPI()

# minio_client = Minio(
#     "192.168.1.151:9000",
#     access_key="minioadmin",
#     secret_key="minioadmin",
#     secure=False,
#     )

# @app.get("/")
# async def root():
#     return{"message": "Fast API root"}

# @app.post("/")
# async def post():
#     return{"message": "Fast API post"}


# @app.get("/dir")
# async def get():
#     path = os.getcwd()
#     cruser = path+"\dir"
#     print(cruser)
#     noofbuckets = subprocess.run(cruser)
#     return{"message": "Fast API put"}

# '''a:create user'''
# @app.get("/user_create/{usr_id}/{usr_pwd}")
# async def user_create(usr_id: str, usr_pwd: str):
#     path = os.getcwd()
#     cruser = path+"./mc admin user add minio "+usr_id +" "+usr_pwd
#     try:
#         noofbuckets = subprocess.run(cruser)
#         return{"message": "User is created successfully"}
#     except subprocess.CalledProcessError as e:
#         return e
    
# '''b:enable user'''
# @app.get("/user_enable/{user_name}")
# async def enable_user(user_name:str):
#     path = os.getcwd()
#     cruser = path+"./mc admin user enable minio "+user_name
#     try:
#         noofbuckets = subprocess.run(cruser)
#         return{"message": "User enabled successfully"}
#     except subprocess.CalledProcessError as e:
#         return e
    
# '''c:Disable user'''
# @app.get("/user_disable/{user_name}")
# async def disable_user(user_name:str):
#     path = os.getcwd()
#     cruser = path+"./mc admin user disable minio "+user_name
#     try:
#         noofbuckets = subprocess.run(cruser)
#         return{"message": "User disabled successfully"}
#     except subprocess.CalledProcessError as e:
#         return e
    
# '''d:Create bucket (policy will be created starting with “po_” followed by bucket name)'''
# @app.get("/bucket_create/{bucket_name}")
# def create_bucket(bucket_name:str):
#     try:
#         path=os.getcwd()
#         # curser=path+'\mc mb MinIO/'+bucket_name
#         # bucket=subprocess.run(curser)
#         # Create bucket.
#         minio_client.make_bucket(bucket_name)
#         '''create_policy'''
#         def create_policy(bucket_name) :
#             fdata1= {
#                 "Version" : "2012-10-17",
#                 "Statement": [
#                     {
#                         "Effect": "Allow",
#                         "Action": ["s3:*"],
#                         "Resource": [f"arn:aws:s3:::{bucket_name}/*" ]
#                     }
#                 ]
#             }
#             with open("abfile.txt","w") as f:
#                 json.dump(fdata1,f,indent=2)
#         create_policy(bucket_name=bucket_name)
#         curser1=path+'./mc admin policy create minio '+"po_"+bucket_name+" abfile.txt"
#         policy=subprocess.run(curser1)
#         return {"message": "Bucket is created successfully"}
#     except Exception as e:
#         print("error")

# '''e:Attach policy to user'''
# @app.get("/policy_attach/{poname}/{usrname}") 
# async def get_user_attach_policy(poname: str, usrname: str):
#     path = os.getcwd()
#     cruser = path+"./mc admin policy attach minio "+poname +" --user "+usrname
#     noofbuckets = subprocess.run(cruser)
#     return{"message": "Policy is attached to the user successfully"}

# '''f:Dettach policy to user'''
# @app.get("/policy_detach/{poname}/{usrname}")
# async def get_user_detach_policy(poname: str, usrname: str):
#     path = os.getcwd()
#     cruser = path+"./mc admin policy detach minio"+poname +" --user "+usrname
#     noofbuckets = subprocess.run(cruser)
#     return{"message": "Policy is detached to the user successfully"}

# '''g:Create group &add user to a group'''
# @app.get("/group_create/{grpname}/{usrname}")
# async def group_create(grpname: str, usrname: str):
#     path = os.getcwd()
#     cruser = path+"./mc admin group add minio "+grpname +" "+usrname
#     noofbuckets = subprocess.run(cruser)
#     return{"message": "group is created successfully"}

# '''h:Attach policies to a group'''
# @app.get("/group_attach_policy/{policy_name}/{group_name}")
# async def attachpolicy_group(policy_name:str,group_name:str):
#     try:
#         path = os.getcwd()
#         cruser = path+",/mc admin policy attach minio "+policy_name+" --group "+group_name
#         policyattach_group = subprocess.run(cruser)
#         return{"message": "policy attached to group successfully"}
#     except Exception as e:
#         print("error")

# # '''i:add user to a group'''
# # @app.get("/add_user")
# '''j:Remove user from group'''
# @app.get("/group_remove_user/{group_name}/{user_name}")
# async def remove_user_group(group_name:str,user_name:str):
#     try:
#         path = os.getcwd()
#         cruser = path+'./mc admin group rm minio '+group_name+" "+user_name
#         remove_user = subprocess.run(cruser)
#         return {"message":"user removed from group successfully"}
#     except Exception as e:
#         print("error")

# '''k:Detach policy from group'''
# @app.get("/group_detach_policy/{policy_name}/{group_name}")
# async def detachpolicy_group(policy_name:str,group_name:str):
#     try:
#         path = os.getcwd()
#         cruser = path+"./mc admin policy detach minio "+policy_name+" --group "+group_name
#         remove_user = subprocess.run(cruser)
#         return {"message":"user removed from group successfully"}
#     except Exception as e:
#         print("error")

# @app.get("/group_detach_policy/{policy_name}/{group_name}")
# async def detach_policy_group(policy_name: str, group_name: str):
#     try:
#         # Construct the command as a list of strings
#         command = ["./mc", "admin", "policy", "detach", "minio", policy_name, "--group", group_name]

#         # Run the command using subprocess
#         subprocess.run(command, check=True)

#         return {"message": "Policy detached from group successfully"}
#     except subprocess.CalledProcessError as e:
#         return {"error": f"Error: {e.returncode}\n{e.stderr}"}





# '''Disable group'''
# @app.get("/group_disable/{group_name}")
# async def disable_group(group_name:str):
#     path = os.getcwd()
#     cruser = path+"./mc admin group disable minio "+group_name
#     disable_group = subprocess.run(cruser)
#     print(disable_group)
#     return{"message": "group is disabled successfully"}

# '''remove group'''
# @app.get("/group_remove/{group_name}")
# async def remove_group(group_name:str):
#     path = os.getcwd()
#     cruser = path+"./mc admin group rm minio "+group_name
#     disable_group = subprocess.run(cruser)
#     print(disable_group)
#     return{"message": "group is removed successfully"}

# # @app.get("/group_remove_member/{group_name}/{member}")
# # async def remove_member_group(group_name:str,member:str):

# #     path = os.getcwd()
# #     cruser = path+"\mc admin group disable MinIO"+group_name
# #     disable_group = subprocess.run(cruser)
# #     print(disable_group)
# #     return{"message": "member is removed from group successfully"}


# '''l:Remove group (first we have to remove all thepolicies in the group)'''
# # @app.get()
# '''m:User list'''
# @app.get("/user_list")
# async def user_list():
#     path = os.getcwd()
#     cruser = path+'./mc admin user ls minio --json'
#     noof_users = subprocess.run(cruser,capture_output=True,text=True)
#     return noof_users

# '''bucket list'''
# @app.get("/buckets_list")
# def get_bucket_list():
#     try:
#         all_buckets_data = {}
#         # List all buckets
#         buckets = minio_client.list_buckets()
#         # Iterate through each bucket and list all objects in each bucket
#         for bucket in buckets:
#             global bucket_name
#             bucket_name = bucket.name
#             print(bucket_name)
#             all_buckets_data[bucket_name] = []
#             objects = minio_client.list_objects(bucket_name)
#             for obj in objects:
#                 all_buckets_data[bucket_name].append(obj.object_name)
#             print(all_buckets_data)
#         return all_buckets_data
#     except Exception as e:
#         raise HTTPException(status_code=404, detail=str(e))
    
# '''n:Policy list'''
# @app.get("/policy_list")
# def get_policy_list():
#     try:
#         path = os.getcwd()
#         cruser = path+'./mc admin policy ls minio --json'
#         noof_policies = subprocess.run(cruser,capture_output=True,text=True)
#         return noof_policies.stdout
#     except Exception as e:
#         print("error")
# get_policy_list()

# '''o:Group list'''
# @app.get("/group_list")
# async def group_list():
#     path = os.getcwd()
#     cruser = path+'./mc admin group ls minio --json'
#     noof_groups = subprocess.run(cruser,capture_output=True,text=True)
#     return noof_groups

# '''q:group info'''
# @app.get("/group_info/{group_name}")
# def group_info(group_name):
#     path=os.getcwd()
#     curser=path+'./mc admin group list minio'
#     grouplist=subprocess.run(curser)
#     curser1=path+'./mc admin group info minio '+group_name
#     group_info=subprocess.run(curser1,shell=True, capture_output=True, text=True)
#     output = group_info.stdout.strip()
#     members_line = output.split("Members:", 1)[-1].strip()
#     global members_list
#     members_list = members_line.split(", ")

#     return group_info
# group_info(group_name="group1")


# '''p.server information'''
# @app.get("/server_info")
# def server_information():
#     path = os.getcwd()
#     cruser = path+'./mc admin info minio --json'
#     server_information = subprocess.run(cruser,capture_output=True,text=True)
#     return server_information



