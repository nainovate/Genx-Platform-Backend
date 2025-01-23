import os
import logging
import yaml
from fastapi import HTTPException, Body, status
from werkzeug.security import generate_password_hash
from Database.users import *
from Database.applicationSetup import *
from Database.applicationDataBase import *
from UserManagment.authentication import getApplicationConfig
import random
import string
import re


projectDirectory = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
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

def initilizeUserDB():
    try:
        userDB = UsersSetup()
        return userDB
    except Exception as e:
        logging.error(f"Error while getting userDB: {e}")
        return None

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
    applicationConfig = getApplicationConfig()
    USER_ID_LENGTH = applicationConfig["userIdLength"]
    USER_ID_CHUNK_SIZE = applicationConfig["userIdChunkSize"]

    characters = string.ascii_uppercase + string.digits
    id = "".join(random.choice(characters) for _ in range(USER_ID_LENGTH))

    # Insert hyphens after every chunk_size characters
    id_with_hyphens = "-".join(
        id[i : i + USER_ID_CHUNK_SIZE] for i in range(0, len(id), USER_ID_CHUNK_SIZE)
    )

    return id_with_hyphens

class Authorization:
    def __init__(self, username: str, userId: str, role: dict):
        self.username = username
        self.userId = userId
        self.role = role
        self.userDB = initilizeUserDB()
        self.applicationDB = initilizeApplicationDB()

    def createUser(self, data: dict = Body(...)):
        try:
            if self.userDB.checkExistingUser(data["username"], data["email"]):
                return HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email or username already registered"
                )
            if not validateEmail(data["email"]):
                return HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Invalid Email"
                )
            if not validatePassword(data["password"]):
                return HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Password is weak"
                )
            
            hashed_password = generate_password_hash(data["password"], method="pbkdf2:sha256")
            user_id = generateUserId()


            if data["role"] == "admin":
                if not "superadmin" in self.role:
                    return HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Unauthorized Access",
                    )
                role = {"admin":[]}
            
            if data["role"] == "user":
                if not "admin" in self.role:
                    return HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Unauthorized Access",
                    )
                role = {"user":{}}

            user_data = {
                "userId": user_id,
                "username": data["username"],
                "email": data["email"],
                "firstName": data["firstName"],
                "lastName": data["lastName"],
                "contactNumber": data["contactNumber"],
                "password": hashed_password,
                "role": role
                }
            
            user_authentication_data = {
                "userId": user_id,
                "contactNumberVerification": False,
                "oneTimePassword": None,
                "otpAttemptsCount": 0,
                "otpAttemptLocked": False,
                "otpCoolDown": None,
                "otpSendCount": 0,
                "otpSendLastTimestamp": None,
                "otpSendLock": False,
                "otpSendLockedUntil": None
                }

            self.userDB.insertData("users", user_data)
            self.userDB.insertData("userAuthentication", user_authentication_data)

            return {"status_code": status.HTTP_200_OK,
                    "detail": "User Registered successfully"
                }

        except Exception as e:
            logger.error(f"Error While Creating User:{e}")
            return HTTPException(status_code=500, detail=str(e))
    
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
            
            status_code, unassignedAdmins = self.userDB.unassignedAdmins(spaceId= spaceId)

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
            
            status_code, assignedAdmins = self.userDB.assignedAdmins(spaceId= spaceId)

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
            
            status_code, unassignedUsers = self.userDB.unassignedUsers(hierarchyId = hierarchyId)
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
            
            status_code, assignedUsers = self.userDB.assignedUsers(hierarchyId = hierarchyId, useCaseRole = useCaseRole)
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
    
    def getAdminDetails(self):
        try:
            if not "superadmin" in self.role:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "Unauthorized Access",
                }
            status_code, adminDetails = self.userDB.getAdminDetails()
            if not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error",
                }
            return {
                "status_code": status.HTTP_200_OK,
                "adminDetails": adminDetails
            }
        except Exception as e:
            logging.error("Error While Fetching assigned users")
            return {
                "status_code": 500, 
                "detail": str(e)
            }
    
    def updateAdminDetails(self, data: dict):
        try:
            if not "superadmin" in self.role:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "Unauthorized Access",
                }
            userId = data["userId"]
            newEmail = data["newEmail"]
            newUserName = data["newUserName"]
            status_code = self.userDB.updateAdminDetails(userId= userId, newEmail= newEmail, newUserName= newUserName)
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
                "detail": "Admin Details Updated Successfully"
            }
        except Exception as e:
            logging.error("Error While updating admin details")
            return {
                "status_code": 500, 
                "detail": str(e)
            }
    
    def getUserDetails(self):
        try:
            if not "admin" in self.role:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "Unauthorized Access",
                }
            
            status_code, userDetails = self.userDB.getUserDetails()
            if not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error",
                }
            return {
                "status_code": status.HTTP_200_OK,
                "userDetails": userDetails
            }
        except Exception as e:
            logging.error("Error While Fetching user details")
            return {
                "status_code": 500, 
                "detail": str(e)
            }
    
    def updateUserDetails(self, data: dict):
        try:
            if not "admin" in self.role:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "Unauthorized Access",
                }
            userId = data["userId"]
            newEmail = data["newEmail"]
            newUserName = data["newUserName"]
            status_code = self.userDB.updateUserDetails(userId= userId, newEmail= newEmail, newUserName= newUserName)
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