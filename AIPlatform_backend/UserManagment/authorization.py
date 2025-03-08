import os
import logging
from bson import ObjectId
import yaml
from fastapi import HTTPException, Body, status
from werkzeug.security import generate_password_hash
from Database.applicationSetup import *
from Database.applicationDataBase import *
import random
import string
import re
from db_config import config


projectDirectory = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
logDir = os.path.join(projectDirectory, "logs")
logBackendDir = os.path.join(logDir, "backend")
logFilePath = os.path.join(logBackendDir, "logger.log")


# Configure logging settings
logging.basicConfig(
    filename=logFilePath,  # Set the log file name
    level=logging.INFO,  # Set the desired log level (e.g., logging.DEBUG, logging.INFO)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

def load_config():
    backendApiPath = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    configPath = os.path.join(backendApiPath, "config.yaml")
    try:
        with open(configPath, "r") as configFile:
            return yaml.safe_load(configFile)
    except FileNotFoundError:
        logging.error(f"Config file not found at: {configPath}")
    except yaml.YAMLError as e:
        logging.error(f"Error parsing YAML file: {e}")
    except Exception as e:
        logging.error(f"Error loading config: {e}")

def initilizeApplicationDB():
    applicationDB = ApplicationDataBase()
    return applicationDB

    
# Pre-compile regular expressions
digit_regex = re.compile(r"\d")
lowercase_regex = re.compile(r"[a-z]")
uppercase_regex = re.compile(r"[A-Z]")
special_char_regex = re.compile(r"[!@#$%^&*()-_+=]")


def validateEmail(email):
    # Regular expression pattern for email validation
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    # Matching the pattern against the email address
    if re.match(pattern, email):
        return True
    else:
        return False
    
def validatePassword(password):
    return (
        len(password) >= 8
        and digit_regex.search(password)
        and lowercase_regex.search(password)
        and uppercase_regex.search(password)
        and special_char_regex.search(password)
    )


def generateUserId():
    USER_ID_LENGTH = config['userIdLength']
    USER_ID_CHUNK_SIZE = config["userIdChunkSize"]

    characters = string.ascii_uppercase + string.digits
    id = "".join(random.choice(characters) for _ in range(USER_ID_LENGTH))

    # Insert hyphens after every chunk_size characters
    id_with_hyphens = "-".join(
        id[i : i + USER_ID_CHUNK_SIZE] for i in range(0, len(id), USER_ID_CHUNK_SIZE)
    )

    return id_with_hyphens

class Authorization:
    def __init__(self, username: str, userId: str, role: dict, orgIds:list = []):
        self.username = username
        self.userId = userId
        self.role = role
        self.orgIds = orgIds
        self.applicationDB = initilizeApplicationDB()


    def createUser(self, data: dict = Body(...)):
        try:
            print('-----role',self.role)
            print('--------data',data)
            # Check if user already exists by username or email
            if self.applicationDB.checkExistingUser(data["username"], data["email"]):
                return {
                    "status_code" :status.HTTP_409_CONFLICT,
                    "detail" :"Email or username already registered"
                }
            
            # Validate email and password
            if not validateEmail(data["email"]):
                return {
                    "status_code":status.HTTP_422_UNPROCESSABLE_ENTITY,
                    "detail":"Invalid Email"
                }
            if not validatePassword(data["password"]):
                return {
                    "status_code":status.HTTP_422_UNPROCESSABLE_ENTITY,
                    "detail":"Password is weak"
                }

            # Hash the password
            hashed_password = generate_password_hash(data["password"], method="pbkdf2:sha256")

            # Set role and orgId based on the role
            if data["role"] == "admin":
                if "superadmin" not in self.role:
                    return {
                        "status_code":status.HTTP_401_UNAUTHORIZED,
                        "detail":"Unauthorized Access",
                    }
                data["role"] = {data["role"]:[]}
            elif data["role"] in ["analyst", "aiengineer","mlOpsengineer", "dataengineer"]:
                if "orgIds" not in data:
                    return {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "detail": "Invalid input data. Expected 'orgId' in input data."
                    }
                orgIds = data["orgIds"]
                if "admin" not in self.role:
                    return {
                        "status_code":status.HTTP_401_UNAUTHORIZED,
                        "detail":"Unauthorized Access",
                    }
                for orgId in orgIds:
                    if orgId not in self.orgIds:
                        return {
                            "status_code": status.HTTP_401_UNAUTHORIZED,
                            "detail": "Unauthorized Access"
                        }
                data["role"] = {data["role"]:{orgId: [] for orgId in data["orgIds"]}}
            elif data["role"] == "user":
                if "analyst" not in self.role:
                    return {
                        "status_code":status.HTTP_401_UNAUTHORIZED,
                        "detail":"Unauthorized Access",
                    }
                if "orgIds" not in data:
                    return {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "detail": "Invalid input data. Expected 'orgId' in input data."
                    }
                orgIds = data["orgIds"]
                for orgId in orgIds:
                    if orgId not in self.orgIds:
                        return {
                            "status_code": status.HTTP_401_UNAUTHORIZED,
                            "detail": "Unauthorized Access"
                        }
                data["role"] = {data["role"]:{orgId: {} for orgId in data["orgIds"]}}
            else:
                return {
                    "status_code":status.HTTP_400_BAD_REQUEST,
                    "detail":"Invalid role provided."
                }
        
            # Insert user data into the `users` table
            data.pop("password")
            user_id = self.applicationDB.insertData("users", data)
            # Insert user credentials into `userCredentials` table

            user_credentials_data = {
                "userId": user_id,
                "password": hashed_password,
                "lastLogin": None  # Initial login is None as the user hasn't logged in yet
            }
            self.applicationDB.insertData("userCredentials", user_credentials_data)

            return {
                "status_code": status.HTTP_200_OK,
                "detail": "User Registered successfully"
            }

        except Exception as e:
            logger.error(f"Error While Creating User: {e}")
            return {"status_code":500, "detail":"Internal Server Error"}

    
    def getUnassignedAdmins(self, spaceId: str):
        try:
            if not isinstance(spaceId, str):
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid spaceId. Expected a string."
                }
        
            if not "superadmin" in self.role:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "Unauthorized Access",
                }
            
            status_code = self.applicationDB.checkSpace(spaceId = spaceId)

            if status_code == 400:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid spaceId. Expected a string."
                }
            
            if status_code == 404:
                return {
                    "status_code":status.HTTP_401_UNAUTHORIZED,
                    "detail":"Space Not Found",
                }
            
            if not status_code == 200:
                return {
                    "status_code":status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error",
                }
            
            status_code, unassignedAdmins = self.applicationDB.unassignedAdmins(spaceId= spaceId)

            if status_code == 400:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid spaceId. Expected a string."
                }
            
            if status_code == 404:
                return {
                    "status_code":status.HTTP_404_NOT_FOUND,
                    "detail":"No Admins Found",
                }
            
            if not status_code == 200:
                return {
                    "status_code":status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail":"Internal server error",
                }
            
            return {
                    "status_code": status.HTTP_200_OK,
                    "unassignedAdmins": unassignedAdmins
                }
        
        except Exception as e:
            logging.error("Error Fetching Unassigned Admins: {e}")
            return {
                "status_code":status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail":str(e)
            }
        
    def getassignedAdmins(self, spaceId: str):
        try:
            # Validate spaceId
            if not isinstance(spaceId, str):
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid spaceId. Expected a string."
                }
        
            if not "superadmin" in self.role:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "Unauthorized Access",
                }
            
            # Check if space exists
            status_code = self.applicationDB.checkSpace(spaceId = spaceId)

            if status_code == 400:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid spaceId. Expected a string."
                }
            
            if status_code == 404:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "Space Not Found",
                }
            
            if not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error",
                }
            
            status_code, assignedAdmins = self.applicationDB.assignedAdmins(spaceId= spaceId)

            if status_code == 400:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid spaceId. Expected a string."
                }
            
            if status_code == 404:
                return {
                    "status_code":status.HTTP_404_NOT_FOUND,
                    "detail":"No Admins Found",
                }
            
            if not status_code == 200:
                return {
                    "status_code":status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail":"Internal server error",
                }
            
            return {
                "status_code": status.HTTP_200_OK,
                "assignedAdmins": assignedAdmins
                }
        
        except Exception as e:
            logging.error(f"Error While Fetching assigned admins: {e}")
            return {
                "status_code":500, "detail":str(e)
            }
        
    def getUnassignedUsers(self, hierarchyId: str):
        try:
            if not "admin" in self.role:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "Unauthorized Access",
                }
            
            status_code = self.applicationDB.checkHierarchy(hierarchyId= hierarchyId)
            if status_code == 404:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail": "Hierarchy Not Found",
                }
            if not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error",
                }
            
            status_code, unassignedUsers = self.applicationDB.unassignedUsers(hierarchyId = hierarchyId)
            if status_code == 404:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "No Users Found",
                }
            if not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error",
                }
            return {
                "status_code": status.HTTP_200_OK,
                "unassignedUsers": unassignedUsers
            }
        except Exception as e:
            logging.error(f"Error While fetching unassigned users")
            return {
                "status_code": 500, 
                "detail": str(e)
            }
        
    def getassignedUsers(self, hierarchyId: str, useCaseRole: str):
        try:
            if not "admin" in self.role:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "Unauthorized Access",
                }
            
            status_code = self.applicationDB.checkHierarchy(hierarchyId= hierarchyId)
            if status_code == 404:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail": "Hierarchy Not Found",
                }
            if not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error",
                }
            
            status_code, assignedUsers = self.applicationDB.assignedUsers(hierarchyId = hierarchyId, useCaseRole = useCaseRole)
            if status_code == 404:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "No Users Found",
                }
            if not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error",
                }
            return {
                "status_code": status.HTTP_200_OK,
                "assignedUsers": assignedUsers
            }
        except Exception as e:
            logging.error("Error While Fetching assigned users")
            return {
                "status_code": 500, 
                "detail": str(e)
            }
    
    def getAdminsDetails(self):
        try:
            status_code, adminsDetails =  self.applicationDB.getAdminsDetails()
            if not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error",
                }
            return {
                "status_code": status.HTTP_200_OK,
                "adminsDetails": adminsDetails
            }
        except Exception as e:
            logging.error("Error While Fetching admins")
            return {
                "status_code": 500, 
                "detail": str(e)
            }
    

    def updateProfile(self, data: dict):
        try:
            if data.get("email") or data.get("username"):
                return {
                    "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                    "detail": "Email or username cannot be updated",
                }
            status_code =  self.applicationDB.updateProfile(data, self.userId)
            if status_code == 404:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "User Not Found",
                }
            if status_code == 400:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "BAD Request",
                }
            if status_code == 302:
                return {
                    "status_code": status.HTTP_302_FOUND,
                    "detail": "No new data for updation",
                }
            if not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error",
                }
            return {
                "status_code": status.HTTP_200_OK,
                "detail": "Profile Updated Successfully"
            }
        except Exception as e:
            logging.error("Error While updating profile details")
            return {
                "status_code": 500, 
                "detail": str(e)
            }
        
    def getProfile(self):
        try:           
            status_code, userdata =  self.applicationDB.getProfile(self.userId)
            if status_code == 404:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "User Not Found",
                }
            if status_code == 400:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "BAD Request",
                }            
            if not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error",
                }
            return {
                "status_code": status.HTTP_200_OK,
                "data": userdata 
            } 
        except Exception as e:
            logging.error("Error While updating admin details")
            return {
                "status_code": 500, 
                "detail": str(e)
            }
    
    
    def updateUserDetails(self, data: dict):
        try:
            status_code =  self.applicationDB.updateUserDetails(data)
            if status_code == 404:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "User Not Found",
                }
            if status_code == 400:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "BAD Request",
                }
            if status_code == 302:
                return {
                    "status_code": status.HTTP_302_FOUND,
                    "detail": "New Email or New User Name Already Existed",
                }
            if not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error",
                }
            return {
                "status_code": status.HTTP_200_OK,
                "detail": "User Details Updated Successfully"
            }
        except Exception as e:
            logging.error("Error While updating user details")
            return {
                "status_code": 500, 
                "detail": str(e)
            }
        

    def deleteUsers(self, data: dict):
        try:
            user_ids_to_delete = data.get("userIds")
            if not user_ids_to_delete:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "userIds key must be provided in request body."
                }

            # Fetch the details of the user who is making the delete request
            requester_id = self.userId
            # Prevent users from deleting themselves
            if requester_id in user_ids_to_delete:
                return {
                    "status_code": status.HTTP_403_FORBIDDEN,
                    "detail": "Users cannot delete themselves."
                }
            
            requester_role = self.role
            # Fetch details of the user being deleted
            for userId in user_ids_to_delete:
                if not userId:
                    return {
                        "status_code": 400,
                        "detail": "UserIds should not be Empty"
                    }
                status_code, user_to_delete = self.applicationDB.getUserById(userId)

                if status_code != 200:
                    return {
                        "status_code": status_code,
                        "detail": f"User not found for {userId}." if status_code == 404 else "Internal server error"
                    }

                target_role = user_to_delete.get("role", {})

                # Role-based deletion logic
                if "superadmin" in requester_role and "admin" in target_role:
                    pass  # Superadmin can delete admin
                elif "admin" in requester_role and any(role in target_role for role in ["aiengineer", "dataengineer", "analyst", "mlopps"]):
                    pass  # Admin can delete AI Engineer, Data Engineer, Analyst, and MLOps
                elif "analyst" in requester_role and "user" in target_role:
                    pass  # Analyst can delete regular users
                else:
                    return {
                        "status_code": status.HTTP_403_FORBIDDEN,
                        "detail": "You do not have permission to delete this user."
                    }

            # Perform the deletion
                status_code = self.applicationDB.deleteUserById(userId)

            if status_code == 200:
                return {
                    "status_code": status.HTTP_200_OK,
                    "detail": "Users deleted successfully."
                }
            else:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Error while deleting users."
                }

        except Exception as e:
            logging.error(f"Error while deleting user: {e}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": str(e)
            }



    def createClientAPIKey(self, data: dict):
        try:
            if not isinstance(data, dict):
                return {
                    "status_code":status.HTTP_400_BAD_REQUEST,
                    "detail": "Data should be in dict"
                }
            if "orgId" not in data.keys() or "keyName" not in data.keys():
                return {
                    "status_code":status.HTTP_400_BAD_REQUEST,
                    "detail": "No orgId or keyName provided"
                }
            status_code, clientApiKey = self.applicationDB.createClientAPIKey(self.userId, data["orgId"], data["keyName"])
            print(status_code,clientApiKey)
            if status_code == 403:
                return {
                    "status_code":status.HTTP_403_FORBIDDEN,
                    "detail": "Unauthorized access"
                }
            if status_code == 409:
                return {
                    "status_code":status.HTTP_409_CONFLICT,
                    "detail": "Keyname already exists"
                }
            
            if status_code == 200:
                return {
                    "status_code":status.HTTP_200_OK,
                    "data": clientApiKey
                }
        except Exception as e:
            logging.error("Error While updating user details")
            return {
                "status_code": 500, 
                "detail": str(e)
            }
        
    def getClientAPIKeys(self, data: dict):
        try:
            if not isinstance(data, dict):
                return {
                    "status_code":status.HTTP_400_BAD_REQUEST,
                    "detail": "Data should be in dict"
                }
            if "orgId" not in data.keys():
                return {
                    "status_code":status.HTTP_400_BAD_REQUEST,
                    "detail": "No orgId provided"
                }
            status_code, keys = self.applicationDB.getClientAPIKeys(self.userId, data["orgId"])
            if status_code == 403:
                return {
                    "status_code":status.HTTP_403_FORBIDDEN,
                    "detail": "Unauthorized access"
                }
            if status_code == 404:
                return {
                    "status_code":status.HTTP_404_NOT_FOUND,
                    "detail": "No keys found"
                }
            
            if status_code == 200:
                return {
                    "status_code":status.HTTP_200_OK,
                    "data": keys
                }
        except Exception as e:
            logging.error("Error While updating user details")
            return {
                "status_code": 500, 
                "detail": str(e)
            }

    