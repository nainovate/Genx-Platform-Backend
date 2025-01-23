import os
import logging
from pymongo import UpdateOne
from pymongo.mongo_client import MongoClient
from fastapi import  HTTPException, status
from werkzeug.security import check_password_hash

# Set up logging
projectDirectory = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
logDir = os.path.join(projectDirectory, "logs")
logBackendDir = os.path.join(logDir, "backend")
logFilePath = os.path.join(logBackendDir, "logger.log")

# Configure logging settings
logging.basicConfig(
    filename=logFilePath,  # Set the log file name
    level=logging.INFO,  # Set the desired log level (e.g., logging.DEBUG, logging.INFO)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

mongo_ip = os.getenv("mongo_ip")
mongo_port = os.getenv("mongo_port")

class UsersSetup:
    def __init__(self):
        self.status_code = 200  # Default status code

        try:
            db_uri = "mongodb://"+mongo_ip+":"+mongo_port+"/"
            self.client = MongoClient(db_uri)
            self.usersDB = self._get_users_db()
            if self.usersDB is None:
                self.status_code = 500
        except Exception as e:
            logging.error(f"Error connecting to the database: {e}")
            self.status_code = 500

    def _get_users_db(self):
        try:
            if self.client is None:
                logging.error("MongoClient is not initialized.")
                self.status_code = 500
                return None
            
            if "usersDB" not in self.client.list_database_names():
                return self.client["usersDB"]
            else:
                return self.client.get_database("usersDB")
        except Exception as e:
            logging.error(f"Error accessing users database: {e}")
            self.status_code = 500
            return None
    
    def createCollections(self):
        collections = ["users", "userAuthentication", "userAttributes", "refreshTokens"]
        try:
            if self.usersDB is None:
                logging.error("usersDB is not initialized.")
                return False, 500  # MongoDB not initialized, return 500
            
            for collection_name in collections:
                if collection_name not in self.usersDB.list_collection_names():
                    self.usersDB.create_collection(collection_name)
                    logging.info(f"Collection '{collection_name}' created successfully.")
            return True, 200  # Collections created successfully, return 200
        except Exception as e:
            logging.error(f"Error creating collections: {e}")
            return False, 500  # Error occurred during collection creation, return 500


    def checkExistingUser(self, username: str, email: str):
        try:
            if not isinstance(username, str) or not isinstance(email, str):
                raise TypeError("Username and email should be strings.")
            
            if self.usersDB is None:
                raise RuntimeError("usersDB is not initialized.")
            
            userCollection = self.usersDB["users"]
            userData = userCollection.find_one({"$or": [{"username": username}, {"email": email}]})
            return userData
        except (TypeError, RuntimeError) as e:
            logging.error(str(e))
            raise
        except Exception as e:
            logging.error(f"Error checking existing user: {e}")
            raise
    
    def checkUser(self, userId: str):
        try:
            if not isinstance(userId, str):
                raise TypeError("UserId should be string")
            
            if self.usersDB is None:
                raise RuntimeError("usersDB is not initialized.")
            
            userCollection = self.usersDB["users"]
            userData = userCollection.find_one({"userId": userId})
            if userData:
                return status.HTTP_302_FOUND
            return status.HTTP_404_NOT_FOUND
        except (TypeError, RuntimeError) as e:
            logging.error(str(e))
            return status.HTTP_400_BAD_REQUEST
        except Exception as e:
            logging.error(f"Error checking existing user: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def checkUserName(self, username: str):
        try:
            if not isinstance(username, str):
                raise TypeError("username should be string")
            
            if self.usersDB is None:
                raise RuntimeError("usersDB is not initialized.")
            
            userCollection = self.usersDB["users"]
            userData = userCollection.find_one({"username": username})
            if userData:
                return status.HTTP_302_FOUND
            return status.HTTP_404_NOT_FOUND
        except (TypeError, RuntimeError) as e:
            logging.error(str(e))
            return status.HTTP_400_BAD_REQUEST
        except Exception as e:
            logging.error(f"Error checking existing user: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def checkEmail(self, email: str):
        try:
            if not isinstance(email, str):
                raise TypeError("email should be string")
            
            if self.usersDB is None:
                raise RuntimeError("usersDB is not initialized.")
            
            userCollection = self.usersDB["users"]
            userData = userCollection.find_one({"email": email})
            if userData:
                return status.HTTP_302_FOUND
            return status.HTTP_404_NOT_FOUND
        except (TypeError, RuntimeError) as e:
            logging.error(str(e))
            return status.HTTP_400_BAD_REQUEST
        except Exception as e:
            logging.error(f"Error checking existing user: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def insertData(self, collectionName: str, data: dict):
        try:
            if not isinstance(collectionName, str):
                raise TypeError("Collection name should be a string.")
            if not isinstance(data, dict):
                raise TypeError("Data should be a dictionary.")
            
            collection = self.usersDB[collectionName]
            collection.insert_one(data)
            logging.info("Data Inserted Successfully")
        except TypeError as te:
            logging.error(str(te))
            raise
        except Exception as e:
            logging.error(f"Error inserting data into '{collectionName}' collection: {e}")
            raise
    
    def getUserCredentials(self, userId: str):
        try:
            user = self.usersDB["users"].find_one(
                {"userId": userId},
                {"_id": 0, "email": 0, "firstName": 0, "lastName": 0, "contactNumber":0}
            )
            if user:
                return status.HTTP_302_FOUND, {key: value for key, value in user.items() if key != "password"}
            else: 
                return status.HTTP_404_NOT_FOUND, None
        except Exception as e:
            # Error Occured
            logging.error(f"Error while checking activeStatus: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR, None
        
    def checkUserCredentials(self, username: str, password: str):
        try:
            user = self.usersDB["users"].find_one(
                {"username": username},
                {"_id": 0, "username": 0, "firstName": 0, "lastName": 0, "contactNumber":0}
            )


            if user:
                if check_password_hash(user["password"], password):
                    return status.HTTP_200_OK, {key: value for key, value in user.items() if key != "password"}
                else:
                    # Incorrect password
                    logging.info("Invalid Credentials")
                    return status.HTTP_401_UNAUTHORIZED, None
            else:
                # User not found
                logging.info("Invalid Credentials")
                return status.HTTP_404_NOT_FOUND, None
        except Exception as e:
            # Error Occured
            logging.error(f"Error while checking user credentials: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR, None
        
    def checkDeviceLogin(self, deviceHash: str, activeStatus: str):
        try:
            activeStatus = self.usersDB["userAttributes"].find_one({"deviceHash": deviceHash, "activeStatus": activeStatus}, {"_id": 0})
            if activeStatus is not None:
                # Active status found
                return status.HTTP_302_FOUND, activeStatus["userId"]
            else:
                # User not found or active status not available
                return status.HTTP_404_NOT_FOUND, None
        except Exception as e:
            # Log and handle unexpected errors
            logging.error(f"Error while checking active status: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR, None

    def checkActiveStatus(self, userId: str):
        try:
            activeStatus = self.usersDB["userAttributes"].find_one({"userId": userId}, {"_id": 0, "userId": 0})
            if activeStatus is not None:
                # Active status found
                return status.HTTP_200_OK, activeStatus.get("activeStatus")
            else:
                # User not found or active status not available
                return status.HTTP_404_NOT_FOUND, None
        except Exception as e:
            # Log and handle unexpected errors
            logging.error(f"Error while checking active status for user {userId}: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR, None
        
    def addUserAttributes(self, userId: str, activeStatus: str, deviceHash: str) -> int:
        try:
            data = {
                "userId": userId,
                "deviceHash": deviceHash,
                "activeStatus": activeStatus
            }

            # Perform the update operation
            result = self.usersDB["userAttributes"].insert_one(data)

            # Check if the update was successful
            if result.inserted_id is not None:
                return status.HTTP_200_OK
            else:
                return status.HTTP_304_NOT_MODIFIED
        except Exception as e:
            # Log and handle the error
            logging.error(f"Error adding user attributes: {e}")
            # Return an internal server error status code
            return status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def addRefreshToken(self, userId: str, deviceHash: str, refreshToken: str) -> int:
        try:
            data = {
                "userId": userId,
                "deviceHash": deviceHash,
                "refreshToken": refreshToken
            }
            # Perform the update operation
            result = self.usersDB["refreshTokens"].insert_one(data)

            # Check if the update was successful
            if result.inserted_id is not None:
                return status.HTTP_200_OK
            else:
                return status.HTTP_304_NOT_MODIFIED
        except Exception as e:
            # Log and handle the error
            logging.error(f"Error updating user attributes: {e}")
            # Return an internal server error status code
            return status.HTTP_500_INTERNAL_SERVER_ERROR

    def deleteUserAttributes(self, userId: str, deviceHash: str) -> int:
        try:
            # Perform the update operation
            result = self.usersDB["userAttributes"].delete_one({"userId": userId, "deviceHash": deviceHash})

            # Check if the update was successful
            if result.deleted_count == 1:
                return status.HTTP_200_OK
            else:
                return status.HTTP_304_NOT_MODIFIED
        except Exception as e:
            # Log and handle the error
            logging.error(f"Error updating user attributes: {e}")
            # Return an internal server error status code
            return status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def deleteRefreshTokens(self, userId: str, deviceHash: str) -> int:
        try:
            # Perform the update operation
            result = self.usersDB["refreshTokens"].delete_one({"userId": userId, "deviceHash": deviceHash})

            # Check if the update was successful
            if result.deleted_count == 1:
                return status.HTTP_200_OK
            else:
                return status.HTTP_304_NOT_MODIFIED
        except Exception as e:
            # Log and handle the error
            logging.error(f"Error updating user attributes: {e}")
            # Return an internal server error status code
            return status.HTTP_500_INTERNAL_SERVER_ERROR


    def getRefreshToken(self, userId: str, deviceHash: str):
        try:
            # Perform the update operation
            result = self.usersDB["refreshTokens"].find_one({"userId": userId, "deviceHash": deviceHash})

            # Check if the update was successful
            if not list(result):
                return status.HTTP_404_NOT_FOUND, None
            
            return status.HTTP_200_OK, result["refreshToken"]
        except Exception as e:
            # Log and handle the error
            logging.error(f"Error updating refresh token: {e}")
            # Return an internal server error status code
            return status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal server error"
        
    def updatePassword(self, userId: str, password: str):
        try:
            filter = {"userId": userId}

            update_operation = {
                "$set": {
                    "password": password
                }
            }
            # Perform the update operation
            result = self.usersDB["users"].update_one(filter, update_operation)

            # Check if the update was successful
            if not result.modified_count >= 1:
                return status.HTTP_304_NOT_MODIFIED
            
            return status.HTTP_200_OK
        except Exception as e:
            # Log and handle the error
            logging.error(f"Error updating refresh token: {e}")
            # Return an internal server error status code
            return status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal server error"
        
    def checkUserAttributes(self, userId: str, deviceHash: str):
        try:
            userAttributes = self.usersDB["userAttributes"].find_one({"userId": userId, "deviceHash": deviceHash}, {"_id": 0, "userId": 0})
            if userAttributes is not None:
                return status.HTTP_200_OK, userAttributes.get("deviceHash")
            else:
                # User not found or user attributes not available
                return status.HTTP_404_NOT_FOUND, None
        except Exception as e:
            # Log and handle unexpected errors
            logging.error(f"Error while checking user attributes for user {userId}: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR, None
    
    def getUserId(self, username: str, role: dict):
        try:
            users = self.usersDB["users"].find_one({"username": username, "role": role}, {"_id": 0})
            if users is not None:
                return status.HTTP_200_OK, users.get("userId")
            else:
                # User not found or user Id not available
                return status.HTTP_404_NOT_FOUND, None
        except Exception as e:
            # Log and handle unexpected errors
            logging.error(f"Error while checking users for user name {username}: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR, None
    
    def getUserInfo(self, emailId: str):
        try:
            users = self.usersDB["users"].find_one({"email": emailId}, {"_id": 0})
            if users is not None:
                return status.HTTP_200_OK, users["userId"]
            else:
                # User not found or user Id not available
                return status.HTTP_404_NOT_FOUND, None
        except Exception as e:
            # Log and handle unexpected errors
            logging.error(f"Error while checking users for emailId {emailId}: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR, None
    
    def getAuthenticationDetails(self, userId: str):
        try:
            authenticationDetails = self.usersDB["userAuthentication"].find_one({"userId": userId}, {"_id": 0})
            if authenticationDetails is not None:
                return status.HTTP_200_OK, authenticationDetails
            else:
                # User not found or user Id not available
                return status.HTTP_404_NOT_FOUND, None
        except Exception as e:
            # Log and handle unexpected errors
            logging.error(f"Error while gettting authentication details for userId {userId}: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR, None
    
    def updateAuthenticationDetails(self, userId: str, data: dict):
        try:
            # Construct the filter using userId
            filter = {"userId": userId}

            # Construct the update operation
            update_operation = UpdateOne(filter, {"$set": data})

            # Perform the update operation using bulk_write with the update_operation
            result = self.usersDB["userAuthentication"].bulk_write([update_operation])

            # Check if the document was modified
            if result.modified_count > 0:
                return status.HTTP_200_OK
            else:
                # Document not found or not modified
                return status.HTTP_304_NOT_MODIFIED
        except Exception as e:
            # Log and handle unexpected errors
            logging.error(f"Error updating authentication details for userId {userId}: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR


    def checkRole(self, userId: str, role: str):
        try:
            user = self.usersDB["users"].find_one({"userId": userId})
            if user and role in user.get("role", {}):
                return status.HTTP_200_OK
            else:
                # User not found or user Id not available
                return status.HTTP_404_NOT_FOUND
        except Exception as e:
            # Log and handle unexpected errors
            logging.error(f"Error while checking users for user id {userId}: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def assignSpace(self, userId: str, spaceId: str):
        try:
            # Validate input data
            if not isinstance(userId, str) or not isinstance(spaceId, str):
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. userId and spaceId must be strings."
                }
            
            # Check if user exists and is an admin
            user = self.usersDB["users"].find_one({"userId": userId})

            if not user:
                return status.HTTP_404_NOT_FOUND
            
            user_role = user.get("role", {})
            if "admin" not in user_role:
                return status.HTTP_403_FORBIDDEN
            
            if spaceId in user_role.get("admin", []):
                return status.HTTP_409_CONFLICT

            self.usersDB["users"].update_one({"userId": userId}, {"$push": {"role.admin": spaceId}})
            return status.HTTP_200_OK
            
        except Exception as e:
            # Log and handle unexpected errors
            logging.error(f"Error while assigning space for user id {userId}: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR

    def unassignedAdmins(self, spaceId: str):
        try:
            # Check if spaceId is a string
            if not isinstance(spaceId, str):
                return status.HTTP_400_BAD_REQUEST, None

            unassignedAdmins = list(self.usersDB["users"].find(
                {"role.admin": {"$nin": [spaceId]},
                "role.superadmin": {"$exists": False},
                "role.user": {"$exists": False}
                },
                {"_id": 0, "email": 0, "firstName": 0, "lastName": 0, "contactNumber": 0, "password": 0, "role": 0}
            ))

            if not unassignedAdmins:
                return status.HTTP_404_NOT_FOUND, None

            return status.HTTP_200_OK, unassignedAdmins
        except Exception as e:
            # Log and handle unexpected errors
            logging.error(f"Error while fetching unassigned admins for spaceId {spaceId}: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR, None
        
    def unassignSpace(self, userId: str, spaceId: str):
        try:
            # Validate input data
            if not isinstance(userId, str) or not isinstance(spaceId, str):
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. userId and spaceId must be strings."
                }
            
            # Check if user exists and is an admin
            user = self.usersDB["users"].find_one({"userId": userId})

            if not user:
                return status.HTTP_404_NOT_FOUND
            
            user_role = user.get("role", {})
            if "admin" not in user_role:
                return status.HTTP_403_FORBIDDEN
            
            if spaceId not in user_role.get("admin", []):
                return status.HTTP_409_CONFLICT

            self.usersDB["users"].update_one({"userId": userId}, {"$pull": {"role.admin": spaceId}})
            return status.HTTP_200_OK

        except Exception as e:
            # Log and handle unexpected errors
            logging.error(f"Error while unassigning space for user id {userId}: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def assignedAdmins(self, spaceId: str):
        try:
            # Validate input data
            if not isinstance(spaceId, str):
                return status.HTTP_400_BAD_REQUEST, None
        
            # Fetch assigned admins for the space
            assignedAdmins = list(self.usersDB["users"].find(
                {"role.admin": {"$in": [spaceId]},
                "role.superadmin": {"$exists": False},
                "role.user": {"$exists": False}
                },
                {"_id": 0, "email": 0, "firstName": 0, "lastName": 0, "contactNumber": 0, "password": 0, "role": 0}
            ))

            if len(assignedAdmins) == 0:
                return status.HTTP_404_NOT_FOUND, None
            
            return status.HTTP_200_OK, assignedAdmins
        
        except Exception as e:
            # Log and handle unexpected errors
            logging.error(f"Error while fetching assigned admins for spaceId {spaceId}: {e}")

    def unassignedUsers(self, hierarchyId: str):
        try:
            unassigned_users = list(self.usersDB["users"].find({
                "role.user": {"$exists": True},
                "role.superadmin": {"$exists": False},
                "role.admin": {"$exists": False},
                },{"_id":0,"email":0,"firstName":0,"lastName":0,"contactNumber":0,"password":0}))
            
            # Filter out users who are already assigned to the given hierarchy ID
            unassignedUsers = [user for user in unassigned_users if hierarchyId not in user["role"]["user"]]
            for user in unassignedUsers:
                if "role" in user:
                    del user["role"]
            if not unassignedUsers:
                return status.HTTP_404_NOT_FOUND, None
            return status.HTTP_200_OK, list(unassignedUsers)
        except Exception as e:
            # Log and handle unexpected errors
            logging.error(f"Error while fetching unassigned users for hierarchyId {hierarchyId}: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def assignedUsers(self, hierarchyId: str, useCaseRole: str):
        try:
            assigned_users = self.usersDB["users"].find({
                "role.user": {"$exists": True},
                "role.superadmin": {"$exists": False},
                "role.admin": {"$exists": False},
                "role.user." + hierarchyId: useCaseRole
                },{"_id":0,"email":0,"firstName":0,"lastName":0,"contactNumber":0,"password":0})
            assignedUsers = list(assigned_users)
            if not assignedUsers:
                return status.HTTP_404_NOT_FOUND, None
            for user in assignedUsers:
                if "role" in user:
                    del user["role"]
            
            return status.HTTP_200_OK, list(assignedUsers)
        except Exception as e:
            # Log and handle unexpected errors
            logging.error(f"Error while fetching assigned users for hierarchyId {hierarchyId}: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
        
    
    def checkHierarchyRole(self, userId: str, hierarchyId: str, useCaseRole: str):
        try:
            user = self.usersDB["users"].find_one({"userId": userId,f"role.user.{hierarchyId}": useCaseRole})
            if user:
                return status.HTTP_200_OK
            else:
                # User not found or user Id not available
                return status.HTTP_404_NOT_FOUND
        except Exception as e:
            # Log and handle unexpected errors
            logging.error(f"Error while checking users for user id {userId}: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def assignUseCaseRole(self, userId: str, hierarchyId: str, useCaseRole: str):
        try:
            user = self.usersDB["users"].find_one({"userId": userId})
            if user and "user" in user.get("role", {}):
                hierarchyIds = user.get("role", {}).get("user", [])
                if hierarchyId in hierarchyIds:
                    return status.HTTP_409_CONFLICT
                self.usersDB["users"].update_one({"userId": userId}, {"$set": {f"role.user.{hierarchyId}": useCaseRole}})
                return status.HTTP_200_OK
            else:
                return status.HTTP_404_NOT_FOUND
        except Exception as e:
            # Log and handle unexpected errors
            logging.error(f"Error while assigning Role for user id {userId}: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def unassignUseCaseRole(self, userId: str, hierarchyId: str):
        try:
            user = self.usersDB["users"].find_one({"userId": userId})
            if user and "user" in user.get("role", {}):
                hierarchyIds = user.get("role", {}).get("user", [])
                if not hierarchyId in hierarchyIds:
                    return status.HTTP_409_CONFLICT
                self.usersDB["users"].update_one({"userId": userId}, {"$unset": {f"role.user.{hierarchyId}": ""}})
                return status.HTTP_200_OK
            else:
                return status.HTTP_404_NOT_FOUND
        except Exception as e:
            # Log and handle unexpected errors
            logging.error(f"Error while unassigning Role for user id {userId}: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def getAssignedSpaces(self, userId: str):
        try:
            # Validate input data
            if not isinstance(userId, str):
                return None, status.HTTP_400_BAD_REQUEST
            
            if self.usersDB is None:
                logging.error("Users database is not initialized.")
                return None, status.HTTP_500_INTERNAL_SERVER_ERROR
            
            # Query the document with the specified userId
            result = self.usersDB["users"].find_one({"userId":userId})
            if not result:
                logging.error(f"User not found for userId: {userId}.")
                return None, status.HTTP_404_NOT_FOUND
            
            # Check if the user is an admin
            if "admin" not in result["role"]:
                logging.error(f"User {userId} is not an admin.")
                return None, status.HTTP_403_FORBIDDEN
            
            # Get the values in the role["admin"] array
            spaceIds = result["role"].get("admin", [])
            if not spaceIds:
                logging.error(f"No spaces found for userId: {userId}.")
                return None, status.HTTP_404_NOT_FOUND
            
            return spaceIds, status.HTTP_200_OK

        except Exception as e:
            logging.error(f"Error while retrieving spaces assigned for userId-{userId}: {e}")
            return None, status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def removeHierarchyRole(self, hierarchyIds: list):
        try:
            # Validate input data
            if not isinstance(hierarchyIds, list):
                return None, status.HTTP_400_BAD_REQUEST
            
            for hierarchyId in hierarchyIds:
                result = self.usersDB["users"].update_many(
                    {"role.user": {"$exists": True}, f"role.user.{hierarchyId}": {"$exists": True}},
                    {"$unset": {f"role.user.{hierarchyId}": ""}, "$pull": {"hierarchyId": hierarchyId}}
                )
                if not result.modified_count > 0:
                    return status.HTTP_304_NOT_MODIFIED
                 
            return status.HTTP_200_OK
        
        except Exception as e:
            print(str(e))
            logging.error(f"Error while removing hierarchy role for users: {e}")
            return None, status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def removeSpaceRole(self, spaceId: str):
        try:
            spaceId= spaceId
            result = self.usersDB["users"].update_many(
                {"role.admin": {"$exists": True, "$in": [spaceId]}},
                {"$pull": {"role.admin": spaceId}}
            )
            if not result.modified_count >= 1:
                return status.HTTP_304_NOT_MODIFIED
            return status.HTTP_200_OK
        except Exception as e:
            logging.error(f"Error while removing hierarchy role for users: {e}")
            return None, status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def getAdminDetails(self):
        try:
            # Find documents where the role is "admin" and project only the specified fields
            adminDocuments = self.usersDB["users"].find(
                {"role.admin": {"$exists": True},
                 "role.superadmin": {"$exists": False},
                 "role.user": {"$exists": False},
                 },{"_id": 0, "userId": 1, "username": 1, "email": 1})
            # Convert the cursor to a list of dictionaries
            adminData = list(adminDocuments)
            for admin in adminData:
                active_status = self.usersDB["userAttributes"].find_one({"userId":admin["userId"], "activeStatus": "active"},{"_id":0, "activeStatus":1})
                if not active_status:
                    admin["activeStaus"] = "inactive"
                else:
                    admin["activeStatus"] = "active"
            return status.HTTP_200_OK, adminData
        except Exception as e:
            logging.error(f"Error while removing space: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def updateAdminDetails(self, userId: str, newUserName: str, newEmail: str):
        try:
            status_code = self.checkUser(userId= userId)
            if status_code == 404:
                return status.HTTP_404_NOT_FOUND
            if status_code == 400:
                return status.HTTP_400_BAD_REQUEST
            if not status_code == 302:
                return status.HTTP_500_INTERNAL_SERVER_ERROR
            
            if not newUserName == "":
                status_code = self.checkUserName(username= newUserName)
                if status_code == 400:
                    return status.HTTP_400_BAD_REQUEST
                if status_code == 500:
                    return status.HTTP_500_INTERNAL_SERVER_ERROR
                if status_code == 302:
                    return status.HTTP_302_FOUND
                self.usersDB["users"].update_one(
                    {"userId": userId},
                    {"$set": {"username": newUserName}}
                )
                
            if not newEmail == "":
                status_code = self.checkEmail(email= newEmail)
                if status_code == 400:
                    return status.HTTP_400_BAD_REQUEST
                if status_code == 500:
                    return status.HTTP_500_INTERNAL_SERVER_ERROR
                if status_code == 302:
                    return status.HTTP_302_FOUND
                self.usersDB["users"].update_one(
                    {"userId": userId},
                    {"$set": {"email": newEmail}}
                )
            return status.HTTP_200_OK
        except Exception as e:
            logging.error(f"Error while updating admin: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def getUserDetails(self):
        try:
            # Find documents where the role is "users" and project only the specified fields
            userDocuments = self.usersDB["users"].find(
                {"role.admin": {"$exists": False},
                 "role.superadmin": {"$exists": False},
                 "role.user": {"$exists": True},
                },{"_id": 0, "userId": 1, "username": 1, "email": 1, "role": 1})
            
            # Convert the cursor to a list of dictionaries
            userData = list(userDocuments)
            for user in userData:
                active_status = self.usersDB["userAttributes"].find_one({"userId":user["userId"], "activeStatus": "active"},{"_id":0, "activeStatus":1})
                if not active_status:
                    user["activeStatus"] = "inactive"
                else:
                    user["activeStatus"] = "active"
            return status.HTTP_200_OK, userData
        except Exception as e:
            logging.error(f"Error while removing space: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def updateUserDetails(self, userId: str, newUserName: str, newEmail: str):
        try:
            status_code = self.checkUser(userId= userId)
            if status_code == 404:
                return status.HTTP_404_NOT_FOUND
            if status_code == 400:
                return status.HTTP_400_BAD_REQUEST
            if not status_code == 302:
                return status.HTTP_500_INTERNAL_SERVER_ERROR
            
            if not newUserName == "":
                status_code = self.checkUserName(username= newUserName)
                if status_code == 400:
                    return status.HTTP_400_BAD_REQUEST
                if status_code == 500:
                    return status.HTTP_500_INTERNAL_SERVER_ERROR
                if status_code == 302:
                    return status.HTTP_302_FOUND
                self.usersDB["users"].update_one(
                    {"userId": userId},
                    {"$set": {"username": newUserName}}
                )
                
            if not newEmail == "":
                status_code = self.checkEmail(email= newEmail)
                if status_code == 400:
                    return status.HTTP_400_BAD_REQUEST
                if status_code == 500:
                    return status.HTTP_500_INTERNAL_SERVER_ERROR
                if status_code == 302:
                    return status.HTTP_302_FOUND
                self.usersDB["users"].update_one(
                    {"userId": userId},
                    {"$set": {"email": newEmail}}
                )
            return status.HTTP_200_OK
        except Exception as e:
            logging.error(f"Error while updating user: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR