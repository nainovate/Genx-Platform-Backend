import os
import logging
from bson import ObjectId
from pymongo import UpdateOne
from pymongo.mongo_client import MongoClient
from fastapi import status
from pymongo.errors import OperationFailure
from werkzeug.security import check_password_hash
# from Database.applicationDataBase import ApplicationDataBase
from db_config import config

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

mongo_ip = config['mongoip']
mongo_port = config['mongoport']


import logging
from pymongo import MongoClient
from pymongo.errors import OperationFailure
from fastapi import status


class OrganizationDataBase:
    def __init__(self, orgId):
        self.status_code = None  # Default status code
        self.client = None
        self.organizationDB = None
        self.orgId = orgId
        # self.applicationDB = ApplicationDataBase()
        try:
            db_uri = f"mongodb://{mongo_ip}:{mongo_port}/"
            self.client = MongoClient(db_uri)
            self.organizationDB = self._get_organization_db(orgId)
            self.status_code = 200
        except OperationFailure as op_err:
            logging.error(f"Error connecting to the database: {op_err}")
            self.status_code = 500
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            self.status_code = 500

    def _get_organization_db(self, orgId):
        try:
            if self.client is None:
                logging.error("MongoClient is not initialized.")
                self.status_code = 500
                return None
            
            # Check if the database already exists
            existing_dbs = self.client.list_database_names()
            if orgId in existing_dbs:
                logging.info(f"Database '{orgId}' already exists.")
                return self.client[orgId]

            # If the database does not exist, create it by accessing it
            logging.info(f"Creating new database '{orgId}'.")
            org_db = self.client[orgId]
            
            return org_db
        except OperationFailure as op_err:
            logging.error(f"Error accessing or creating database: {op_err}")
            self.status_code = 500
            return None
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            self.status_code = 500
            return None
    
    def createSpace(self, spaceName: str, spaceId: str, userId: str):
        try:

            # Validate input types
            if not isinstance(spaceName, str) or not isinstance(spaceId, str) or not isinstance(userId, str):
                logging.error("Invalid input data types. Expected strings for spaceName, spaceId, and userId.")
                return status.HTTP_400_BAD_REQUEST
            
            if self.organizationDB is None:
                logging.error("Organization database is not initialized.")
                return status.HTTP_500_INTERNAL_SERVER_ERROR
            
            # Check if spaceName already exists
            existing_space_name = self.organizationDB["spaces"].find_one({"spaceName": spaceName})
            if existing_space_name:
                logging.error("Space Name Already Exists")
                return status.HTTP_409_CONFLICT
            
            # Check if spaceId already exists
            existing_space_id = self.organizationDB["spaces"].find_one({"spaceId": spaceId})
            if existing_space_id:
                logging.error("Space ID Already Exists")
                return status.HTTP_422_UNPROCESSABLE_ENTITY
            
            data = {
                "spaceName": spaceName,
                "spaceId": spaceId,
                "createdBy": userId
            }

            # Insert the new space data into the database
            self.organizationDB["spaces"].insert_one(data)
            logging.info(f"Space {spaceName} created successfully with space id {spaceId}")
            return status.HTTP_200_OK
        except Exception as e:
            logging.error(f"Error while creating space: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def removeSpace(self, spaceId: str):
        try:
            result = self.organizationDB["spaces"].delete_one(
                {"spaceId": spaceId}
            )
            if result.deleted_count==1:
                return status.HTTP_200_OK
            else:
                return status.HTTP_422_UNPROCESSABLE_ENTITY
        except Exception as e:
            logging.error(f"Error while removing Space: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def checkSpace(self, spaceId: str):
        try:
            # Check if spaceId is a string
            if not isinstance(spaceId, str):
                return status.HTTP_400_BAD_REQUEST

            space = self.organizationDB["spaces"].find_one({"spaceId": spaceId})
            if space:
                return status.HTTP_200_OK
            else:
                return status.HTTP_404_NOT_FOUND
        except Exception as e:
            # Log and handle unexpected errors
            logging.error(f"Error while checking space for spaceId {spaceId}: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def updateSpaceName(self, spaceId: str, spaceName: str):
        try:
           
            existing_space_name = self.organizationDB["spaces"].find_one({"spaceName": spaceName})
            if existing_space_name:
                logging.error("Space Name Already Exists")
                return status.HTTP_409_CONFLICT
            
            result = self.organizationDB["spaces"].update_one(
                {"spaceId": spaceId},
                {"$set": {"spaceName": spaceName}}
            )
            return status.HTTP_200_OK
        except Exception as e:
            logging.error(f"Error while updating space: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR

    def getSpaceInOrg(self,role,userId):
        try:
            if self.organizationDB is None:
                logging.error("Organization database is not initialized.")
                return None, status.HTTP_500_INTERNAL_SERVER_ERROR
            if "admin" in role:
                spaces_list = list(self.organizationDB["spaces"].find({"createdBy":userId}, {"_id": 0,"createdBy":0}))
            elif "analyst" in role:
                spaces_list = list(self.organizationDB["spaces"].find({}, {"_id": 0,"createdBy":0}))
            if len(spaces_list) > 0:
                return spaces_list, status.HTTP_200_OK
            else:
                logging.info("No spaces found for this Org.")
                return [], status.HTTP_404_NOT_FOUND
        except Exception as e:
            logging.error(f"Error while retrieving spaces: {e}")
            return None, status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def getAllSpacesInOrg(self):
        try:
            if self.organizationDB is None:
                logging.error("Organization database is not initialized.")
                return None, status.HTTP_500_INTERNAL_SERVER_ERROR
            
            spaces_list = list(self.organizationDB["spaces"].find({}, {"_id": 0,"createdBy":0}))
            if len(spaces_list) > 0:
                return spaces_list
            else:
                logging.info("No spaces found for this Org.")
                return []
        except Exception as e:
            logging.error(f"Error while retrieving spaces: {e}")
            return []
    
    def createRole(self, roleInfo:dict, roleId:str, spaceIds:dict, userId: str):
        try:
            # Validate input types
            if not isinstance(roleInfo, dict) or not isinstance(spaceIds, list) or not isinstance(userId, str):
                logging.error("Invalid input data types. Expected strings for roleName, spaceId, and userId.")
                return status.HTTP_400_BAD_REQUEST
            
            if self.organizationDB is None:
                logging.error("Organization database is not initialized.")
                return status.HTTP_500_INTERNAL_SERVER_ERROR
            
            # Check if roleName already exists
            existing_role_name = self.organizationDB["roles"].find_one({"roleName": roleInfo["roleName"]})

            if existing_role_name:
                logging.error("role Name Already Exists")
                return status.HTTP_409_CONFLICT
            
            # Check if roleId already exists
            existing_role_id = self.organizationDB["roles"].find_one({"roleId": roleId})

            if existing_role_id:
                logging.error("role ID Already Exists")
                return status.HTTP_422_UNPROCESSABLE_ENTITY
            
            data = {
                "roleName": roleInfo["roleName"],
                "description":roleInfo["description"],
                "roleId": roleId,
                "spaceIds": spaceIds,
                "createdBy": userId
            }

            # Insert the new space data into the database
            self.organizationDB["roles"].insert_one(data)
            logging.info(f"Role {roleInfo['roleName']} created successfully")
            return status.HTTP_200_OK
        except Exception as e:
            logging.error(f"Error while creating Role: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def getSpaceInfo(self,spaceId):
        try:
            if self.organizationDB is None:
                logging.error("Organization database is not initialized.")
                return None, status.HTTP_500_INTERNAL_SERVER_ERROR
            
            space = self.organizationDB["spaces"].find_one({"spaceId":spaceId}, {"_id": 0,"createdBy":0})
            if space:
                return space, status.HTTP_200_OK
            else:
                logging.info("space is not found.")
                return {}, status.HTTP_404_NOT_FOUND
        except Exception as e:
            logging.error(f"Error while retrieving spaces: {e}")
            return None, status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def getRolesInSpace(self, role, spaceId):
        try:
            if self.organizationDB is None:
                logging.error("Organization database is not initialized.")
                return None, status.HTTP_500_INTERNAL_SERVER_ERROR
            if "analyst" in role:
                roles_list = list(self.organizationDB["roles"].find({"spaceIds": {"$elemMatch": {"$eq": spaceId}}}, {"_id": 0,"roleId":1, "roleName":1, "description":1}))
            # elif "admin" in role:
            #     spaces_list = list(self.organizationDB["spaces"].find({}, {"_id": 0,"createdBy":0}))
            if len(roles_list) > 0:
                parsedRoles =[]
                for role in roles_list:
                    tasks_list = list(self.organizationDB["tasks"].find({"roleIds": {"$elemMatch": {"$eq": role["roleId"]}}}, {"_id": 0,"taskId":1, "taskName":1}))
                    role["tasks"] = tasks_list
                    parsedRoles.append(role)
                return parsedRoles, status.HTTP_200_OK
            else:
                logging.info("No roles found for this Org.")
                return [], status.HTTP_404_NOT_FOUND
        except Exception as e:
            logging.error(f"Error while retrieving spaces: {e}")
            return None, status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def checkRole(self, roleId: str):
        try:
            # Check if spaceId is a string
            if not isinstance(roleId, str):
                return status.HTTP_400_BAD_REQUEST

            role = self.organizationDB["roles"].find_one({"roleId": roleId})
            if role:
                return status.HTTP_200_OK
            else:
                return status.HTTP_404_NOT_FOUND
        except Exception as e:
            # Log and handle unexpected errors
            logging.error(f"Error while checking space for roleId {roleId}: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def updateRole(self, data:dict):
        try:
            if "roleName" in data:
                existing_role_name = self.organizationDB["roles"].find_one({"roleName": data["roleName"]})
                if existing_role_name:
                    logging.error("Role Name Already Exists")
                    return status.HTTP_409_CONFLICT
            result = self.organizationDB["roles"].update_one(
                {"roleId": data['roleId']},
                {"$set": {**data}}
            )
            if result.matched_count==1:
                return status.HTTP_200_OK
            else:
                return status.HTTP_422_UNPROCESSABLE_ENTITY
        except Exception as e:
            logging.error(f"Error while updating space: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def removeRole(self, roleId: str):
        try:
            result = self.organizationDB["roles"].delete_one(
                {"roleId": roleId}
            )
            if result.deleted_count==1:
                return status.HTTP_200_OK
            else:
                return status.HTTP_422_UNPROCESSABLE_ENTITY
        except Exception as e:
            logging.error(f"Error while removing Space: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR