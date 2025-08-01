from datetime import datetime, timezone
import os
import logging
import random
import string
import time
from bson import ObjectId
from pymongo import UpdateOne
from pymongo import MongoClient, DESCENDING
from fastapi import status
from pymongo.errors import OperationFailure
from werkzeug.security import check_password_hash
from db_config import config
from Database.organizationDataBase import OrganizationDataBase

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


class ApplicationDataBase:
    def __init__(self):
        self.status_code = None  # default status code
        mongo_ip = config['mongoip']
        mongo_port = config['mongoport']
        try:
            db_uri = "mongodb://"+mongo_ip+":"+mongo_port+"/"
            self.client = MongoClient(db_uri)
            self.  applicationDB = self._get_application_db()
            self.status_code = 200
        except OperationFailure as op_err:
            logging.error(f"Error connecting to the database: {op_err}")
            self.status_code = 500
            return False, self.status_code
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            self.status_code = 500
            return False, self.status_code

    def _get_application_db(self):
        try:
            if self.client is None:
                logging.error("MongoClient is not initialized.")
                self.status_code = 500
                return None
            return self.client["applicationDB"]
        except OperationFailure as op_err:
            logging.error(f"Error accessing database: {op_err}")
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
                logging.error("Invalid input data types. Expected strings for spaceName, spaceId, userId, and a list for usecases.")
                return status.HTTP_400_BAD_REQUEST
            
            if self.applicationDB is None:
                logging.error("Application database is not initialized.")
                return status.HTTP_500_INTERNAL_SERVER_ERROR
            
            # Check if spaceName already exists
            existing_space_name = self.applicationDB["spaces"].find_one({"spaceName": spaceName})
            if existing_space_name:
                logging.error("Space Name Already Existed")
                return status.HTTP_409_CONFLICT
            
            # Check if spaceId already exists
            existing_space_id = self.applicationDB["spaces"].find_one({"spaceId": spaceId})
            if existing_space_id:
                logging.error("Space ID Already Existed. Creating new space ID.")
                return status.HTTP_422_UNPROCESSABLE_ENTITY
            
            data = {
                "spaceName": spaceName,
                "spaceId": spaceId,
                "createdBy": userId
            }

            # Insert the new space data into the database
            if self.applicationDB["spaces"].insert_one(data):
                logging.info(f"Space {spaceName} created successfully with space id {spaceId}")
                return status.HTTP_200_OK
        except Exception as e:
            logging.error(f"Error while creating space: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def createOrganization(self, data: dict, userId: str):
        try:
            if not isinstance(data, dict) or not isinstance(data["orgName"], str) or not isinstance(data["email"], str) or not isinstance(data["contactNumber"], str) or not isinstance(data["address"], str):
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data."
                }
            
            if self.applicationDB is None:
                logging.error("Application database is not initialized.")
                return status.HTTP_500_INTERNAL_SERVER_ERROR
            
            # Check if orgName already exists
            existing_org_name = self.applicationDB["organizations"].find_one({"orgName": data['orgName']})
            if existing_org_name:
                logging.error("Org Name Already Existed")
                return status.HTTP_409_CONFLICT
            
            # Check if org already exists
            existing_org_id = self.applicationDB["organizations"].find_one({"orgId": data['orgId']})
            if existing_org_id:
                logging.error("Org ID Already Existed. Creating new org ID.")
                return status.HTTP_422_UNPROCESSABLE_ENTITY
            
            data["createdBy"]= ObjectId(userId)

            # Insert the new org data into the database
            if self.applicationDB["organizations"].insert_one(data):
                logging.info(f"Organization {data['orgName']} created successfully with org id {data['orgId']}")
                return status.HTTP_200_OK
        except Exception as e:
            logging.error(f"Error while creating space: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def checkSpace(self, spaceId: str):
        try:
            # Check if spaceId is a string
            if not isinstance(spaceId, str):
                return status.HTTP_400_BAD_REQUEST

            space = self.applicationDB["spaces"].find_one({"spaceId": spaceId})
            if space:
                return status.HTTP_200_OK
            else:
                return status.HTTP_404_NOT_FOUND
        except Exception as e:
            # Log and handle unexpected errors
            logging.error(f"Error while checking space for space id {spaceId}: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def checkOrg(self, orgId: str):
        try:
            # Check if spaceId is a string
            if not isinstance(orgId, str):
                return status.HTTP_400_BAD_REQUEST

            org = self.applicationDB["organizations"].find_one({"orgId": orgId})
            if org:
                return status.HTTP_200_OK
            else:
                return status.HTTP_404_NOT_FOUND
        except Exception as e:
            # Log and handle unexpected errors
            logging.error(f"Error while checking org for org id {orgId}: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def getSpaces(self):
        try:
            if self.applicationDB is None:
                logging.error("Application database is not initialized.")
                return None, status.HTTP_500_INTERNAL_SERVER_ERROR
            
            spaces_list = list(self.applicationDB["spaces"].find({}, {"_id": 0, "usecases": 0, "createdBy": 0}))
            
            if len(spaces_list) > 0:
                spaces = {}
                for space in spaces_list:
                    spaces[space["spaceId"]] = space["spaceName"]
                return spaces, status.HTTP_200_OK
            else:
                logging.info("No spaces found in application database.")
                return {}, status.HTTP_404_NOT_FOUND
        except Exception as e:
            logging.error(f"Error while retrieving spaces: {e}")
            return None, status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def getUsersInOrg(self, orgId):
        try:
            if self.applicationDB is None:
                logging.error("Application database is not initialized.")
                return None, status.HTTP_500_INTERNAL_SERVER_ERROR
            
            users_list = list(self.applicationDB["users"].find(
                {"role.admin": {"$exists": False},
                 "role.superadmin": {"$exists": False},
                 "role.user": {"$exists": False},
                },{ "contactNumber": 0}))
            filtered_users = [user for user in users_list if orgId in user['orgIds']]

            if filtered_users is None:
                return {
                    status.HTTP_404_NOT_FOUND, []
                }
            else:
                for user in filtered_users:
                    user['userId'] = str(user['_id'])
                    del user['_id']
                return status.HTTP_200_OK, list(filtered_users)
            
        except Exception as e:
            logging.error(f"Error while retrieving Users for orgId: {e}")
            return None, status.HTTP_500_INTERNAL_SERVER_ERROR
        

    def getAllUsers(self):
        try:
            if self.applicationDB is None:
                logging.error("Application database is not initialized.")
                return None, status.HTTP_500_INTERNAL_SERVER_ERROR
            
            users_list = list(self.applicationDB["users"].find(
                {"role.admin": {"$exists": False},
                 "role.superadmin": {"$exists": False},
                 "role.user": {"$exists": False},
                },{"contactNumber": 0}))

            if users_list is None:
                return {
                    status.HTTP_404_NOT_FOUND, []
                }
            else:
                for user in users_list:
                    user['userId'] = str(user['_id'])
                    del user['_id']
                return status.HTTP_200_OK, users_list
            
        except Exception as e:
            logging.error(f"Error while retrieving All Users: {e}")
            return None, status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def getAssignedAnalysts(self,spaceId):
        try:
            if self.applicationDB is None:
                logging.error("Application database is not initialized.")
                return None, status.HTTP_500_INTERNAL_SERVER_ERROR
            
            users_list = list(self.applicationDB["users"].find(
                {"role.analyst": {"$exists": True},
                },{"contactNumber": 0}))

            if users_list is None:
                return {
                    status.HTTP_404_NOT_FOUND, []
                }
            else:
                for user in users_list:
                    user['userId'] = str(user['_id'])
                    del user['_id']
                return status.HTTP_200_OK, users_list
            
        except Exception as e:
            logging.error(f"Error while retrieving All Users: {e}")
            return None, status.HTTP_500_INTERNAL_SERVER_ERROR

    def getAllAnalysts(self):
        try:
            if self.applicationDB is None:
                logging.error("Application database is not initialized.")
                return None, status.HTTP_500_INTERNAL_SERVER_ERROR
            
            users_list = list(self.applicationDB["users"].find(
                {"role.analyst": {"$exists": True},
                },{"contactNumber": 0}))

            if users_list is None:
                return {
                    status.HTTP_404_NOT_FOUND, []
                }
            else:
                for user in users_list:
                    user['userId'] = str(user['_id'])
                    del user['_id']
                return status.HTTP_200_OK, users_list
            
        except Exception as e:
            logging.error(f"Error while retrieving All Users: {e}")
            return None, status.HTTP_500_INTERNAL_SERVER_ERROR

    def getAnalystsInOrg(self, orgId):
        try:
            if self.applicationDB is None:
                logging.error("Application database is not initialized.")
                return status.HTTP_500_INTERNAL_SERVER_ERROR, None

            # Retrieve the list of analysts in the specified organization
            org_analysts_list = list(self.applicationDB["users"].find(
                {
                    "role.analyst": {"$exists": True},
                },
                { "contactNumber": 0}
            ))
            if not org_analysts_list:
                return status.HTTP_404_NOT_FOUND, []

            # Filter analysts who are part of the specified space
            space_analysts = [
                analyst for analyst in org_analysts_list
                if orgId in analyst["orgIds"]
            ]

            if space_analysts:
                for user in space_analysts:
                    user['userId'] = str(user['_id'])
                    del user['_id']
                return status.HTTP_200_OK, space_analysts
            else:
                logging.info(f"No analysts found for org {orgId} in organization.")
                return status.HTTP_404_NOT_FOUND, []

        except Exception as e:
            logging.error(f"Error while retrieving analysts for org {orgId}: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR, str(e)


    def getOrganizations(self):
        try:
            if self.applicationDB is None:
                logging.error("Application database is not initialized.")
                return None, status.HTTP_500_INTERNAL_SERVER_ERROR
            
            org_list = list(self.applicationDB["organizations"].find({}, {"_id": 0, "createdBy": 0}))
            
            if len(org_list) > 0:
                orgs = []
                for org in org_list:
                    organizationDB = OrganizationDataBase(org["orgId"])
                    spaces = organizationDB.getAllSpacesInOrg()
                    org["spaces"] = spaces
                    orgs.append(org)
                return orgs, status.HTTP_200_OK
            else:
                logging.info("No org found in application database.")
                return {}, status.HTTP_404_NOT_FOUND
        except Exception as e:
            logging.error(f"Error while retrieving spaces: {e}")
            return None, status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def getOrgInfo(self, orgId):
        try:
            if self.applicationDB is None:
                
                logging.error("Application database is not initialized.")
                return None, status.HTTP_500_INTERNAL_SERVER_ERROR
            
            orgInfo = self.applicationDB["organizations"].find_one({"orgId":orgId}, {"_id": 0, "orgId": 1,"orgName":1})
            if orgInfo:
                # orgs = {}
                # for org in org_list:
                #     orgs[org["orgId"]] = org["orgName"]
                return orgInfo, status.HTTP_200_OK
            else:
                logging.info("No org found in application database.")
                return {}, status.HTTP_404_NOT_FOUND
        except Exception as e:
            logging.error(f"Error while retrieving spaces: {e}")
            return None, status.HTTP_500_INTERNAL_SERVER_ERROR

    def getSpaceUseCases(self, spaceId: str):
        try:
             # Validate input data
            if not isinstance(spaceId, str):
                return None, status.HTTP_400_BAD_REQUEST
            
            if self.applicationDB is None:
                logging.error("Application database is not initialized.")
                return None, status.HTTP_500_INTERNAL_SERVER_ERROR
            
            spaceUseCases = list(self.applicationDB["spaces"].find({"spaceId": spaceId},{"_id":0,"createdBy":0,"spaceId":0,"spaceName":0}))[0]['usecases']

            if spaceUseCases:
                return spaceUseCases, status.HTTP_200_OK
            else:
                logging.error(f"No space use cases found for spaceId: {spaceId}.")
                return None, status.HTTP_404_NOT_FOUND
            
        except Exception as e:
            logging.error(f"Error while retrieving space use cases for space {spaceId}: {e}")
            return None, status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def createHierarchy(self, hierarchyName: str, hierarchyId: str, useCaseId: str, spaceId: str, userId: str, useCaseRoles: dict):
        try:
            if self.applicationDB is None:
                logging.error("Application database is not initialized.")
                return status.HTTP_500_INTERNAL_SERVER_ERROR
            hierarchyNames = self.applicationDB["hierarchys"].find_one({"hierarchyName": hierarchyName})
            if hierarchyNames:
                logging.error("Hierarchy Name Already Existed")
                return status.HTTP_409_CONFLICT
            
            hierarchyIds = self.applicationDB["hierarchys"].find_one({"hierarchyId": hierarchyId})
            if hierarchyIds:
                logging.error("Hierarchy ID Already Existed Creating new space ID")
                return status.HTTP_422_UNPROCESSABLE_ENTITY
            data = {
                "hierarchyName": hierarchyName,
                "hierarchyId": hierarchyId,
                "spaceId": spaceId,
                "useCaseId": useCaseId,
                "useCaseRoles": useCaseRoles,
                "createdBy": userId
            }
            if self.applicationDB["hierarchys"].insert_one(data):
                logging.info(f"Hierarchy {hierarchyName} created sucessfully with hierarchy id {hierarchyId}")
                return status.HTTP_200_OK
        except Exception as e:
            logging.error(f"Error while crerating hierarchy: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def checkHierarchy(self, hierarchyId: str):
        try:
            hierarchy = self.applicationDB["hierarchys"].find_one({"hierarchyId": hierarchyId})
            if hierarchy:
                return status.HTTP_200_OK
            else:
                return status.HTTP_404_NOT_FOUND
        except Exception as e:
            # Log and handle unexpected errors
            logging.error(f"Error while checking hierarchy for hierarchy id {hierarchyId}: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def checkUseCaseId(self, hierarchyId: str, useCaseId: str):
        try:
            useCaseId = self.applicationDB["hierarchys"].find_one({"hierarchyId": hierarchyId, "useCaseId":useCaseId})
            if useCaseId:
                return status.HTTP_200_OK
            else:
                return status.HTTP_404_NOT_FOUND
        except Exception as e:
            # Log and handle unexpected errors
            logging.error(f"Error while checking usecase Id for hierarchy id {hierarchyId}: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def checkHierarchyRoles(self, hierarchyId: str, useCaseRole: str):
        try:
            hierarchy = self.applicationDB["hierarchys"].find_one({"hierarchyId": hierarchyId})
            if useCaseRole in hierarchy["useCaseRoles"]:
                return status.HTTP_200_OK
            else:
                return status.HTTP_404_NOT_FOUND
        except Exception as e:
            # Log and handle unexpected errors
            logging.error(f"Error while checking useCaseRoles for hierarchy id {hierarchyId}: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def getSpaceId(self, hierarchyId: str):
        try:
            # Validate input data
            if not isinstance(hierarchyId, str):
                return None, status.HTTP_400_BAD_REQUEST

            if self.applicationDB is None:
                logging.error("Application database is not initialized.")
                return None, status.HTTP_500_INTERNAL_SERVER_ERROR
            
            spaceId = self.applicationDB["hierarchys"].find_one({"hierarchyId": hierarchyId},{"_id":0,"hierarchyName":0,"hierarchyId":0,"useCaseId":0,"useCaseRoles":0,"createdBy":0})

            if spaceId:
                return spaceId, status.HTTP_200_OK
            else:
                logging.error(f"No spaceId found for hierarchyId: {hierarchyId}.")
                return None, status.HTTP_404_NOT_FOUND
            
        except Exception as e:
            # Log and handle unexpected errors
            logging.error(f"Error while getting spaceId for hierarchy id {hierarchyId}: {e}")
            return None, status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def getCreatedHierarchy(self, userId: str, spaceId: None):
        try:
            if not spaceId== None:
                hierarchys = self.applicationDB["hierarchys"].find({"spaceId": spaceId, "createdBy": userId},{"_id":0,"spaceId":0,"useCaseId":0,"createdBy":0,"useCaseRoles":0})
            hierarchys = self.applicationDB["hierarchys"].find({"createdBy": userId},{"_id":0,"spaceId":0,"useCaseId":0,"createdBy":0,"useCaseRoles":0})
            if hierarchys:
                return list(hierarchys), status.HTTP_200_OK
            else:
                return None, status.HTTP_404_NOT_FOUND
        except Exception as e:
            # Log and handle unexpected errors
            logging.error(f"Error while fetching hierarchys for user {userId}: {e}")
            return None, status.HTTP_500_INTERNAL_SERVER_ERROR

    def getSpaceName(self, spaceId: str):
        try:
            # Validate input data
            if not isinstance(spaceId, str):
                return None, status.HTTP_400_BAD_REQUEST
            
            if self.applicationDB is None:
                logging.error("Application database is not initialized.")
                return None, status.HTTP_500_INTERNAL_SERVER_ERROR
            
            spaceName = list(self.applicationDB["spaces"].find({"spaceId": spaceId},{"_id":0,"spaceId":0,"createdBy":0,"usecases":0}))[0]
            
            if spaceName:
                return spaceName['spaceName'], status.HTTP_200_OK
            else:
                logging.error(f"No space found for spaceId: {spaceId}.")
                return None, status.HTTP_404_NOT_FOUND
            
        except Exception as e:
            # Log and handle unexpected errors
            logging.error(f"Error while fetching spaceName for spaceId {spaceId}: {e}")
            return None, status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def getHierarchyRoles(self, hierarchyId: str):
        try:
            hierarchyRoles = list(self.applicationDB["hierarchys"].find({"hierarchyId": hierarchyId},{"_id":0,"hierarchyName":0,"hierarchyId":0,"spaceId":0,"useCaseId":0,"createdBy":0}))[0]
            if hierarchyRoles:
                return hierarchyRoles['useCaseRoles'], status.HTTP_200_OK
            else:
                return None, status.HTTP_404_NOT_FOUND
        except Exception as e:
            # Log and handle unexpected errors
            logging.error(f"Error while fetching hierarchy roles for hierarchy {hierarchyId}: {e}")
            return None, status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def getHierarchyAndSpaceNames(self, hierarchyIds: list):
        try:
            results = {}
            for hierarchyId in hierarchyIds:
                hierarchyData = self.applicationDB["hierarchys"].find_one({"hierarchyId": hierarchyId}, {"_id":0,"hierarchyId":0,"useCaseId":0,"useCaseRoles":0,"createdBy":0})
                if not hierarchyData:
                    return None, status.HTTP_404_NOT_FOUND 
                spaceData= self.applicationDB["spaces"].find_one({"spaceId": hierarchyData["spaceId"]},{"_id":0,"spaceId":0,"createdBy":0,"usecases":0})
                spaceName = spaceData["spaceName"]
                hierarchyInfo = {"HId": hierarchyId,"HName": hierarchyData["hierarchyName"]}

                if spaceName not in results:
                    results[spaceName] = [hierarchyInfo]
                else:
                    results[spaceName].append(hierarchyInfo)
            return [results], status.HTTP_200_OK
        except Exception as e:
            logging.error(f"Error while fetching hierarchy name and space name for hierarchy {hierarchyId}: {e}")
            return None, status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def getUseCaseId(self, hierarchyId: str):
        try:
            hierarchyData = self.applicationDB["hierarchys"].find_one({"hierarchyId": hierarchyId}, {"_id":0,"hierarchyId":0,"hierarchyName":0,"spaceId":0,"useCaseRoles":0,"createdBy":0})
            if not hierarchyData:
                return None, status.HTTP_404_NOT_FOUND 
            return hierarchyData["useCaseId"], status.HTTP_200_OK
        except Exception as e:
            logging.error(f"Error while fetching hierarchy name and space name for hierarchy {hierarchyId}: {e}")
            return None, status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def getUnassignedUseCases(self, spaceId: str, configInstance: object):
        try:
            # Validate spaceId
            if not isinstance(spaceId, str):
                return None, status.HTTP_400_BAD_REQUEST
            
            # Validate configInstance
            if not hasattr(configInstance, 'getUseCases') or not callable(configInstance.getUseCases):
                return None, status.HTTP_400_BAD_REQUEST
            
            result = {}
            useCases, status_code = configInstance.getUseCases()

            spaceData = self.applicationDB["spaces"].find_one({"spaceId": spaceId}, {"_id":0,"spaceId":0,"createdBy":0,"spaceName":0})

            assignedUseCases = spaceData["usecases"]
            for useCase, useCaseName in useCases.items():
                if useCase not in assignedUseCases:
                    result[useCase] = useCaseName

            if not result:
                logging.error(f"All use cases assigned for spaceId: {spaceId}.")
                return None, status.HTTP_404_NOT_FOUND
            
            return result, status.HTTP_200_OK
        except Exception as e:
            logging.error(f"Error while fetching unassigned use cases for space {spaceId}: {e}")
            return None, status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def getAssignedUseCases(self, spaceId: str, configInstance: object):
        try:
            # Validate spaceId
            if not isinstance(spaceId, str):
                return None, status.HTTP_400_BAD_REQUEST
            
            # Validate configInstance
            if not hasattr(configInstance, 'getUseCases') or not callable(configInstance.getUseCases):
                return None, status.HTTP_400_BAD_REQUEST
            
            result = {}
            useCases, status_code = configInstance.getUseCases()

            spaceData = self.applicationDB["spaces"].find_one({"spaceId": spaceId}, {"_id":0,"spaceId":0,"createdBy":0,"spaceName":0})

            assignedUseCases = spaceData["usecases"]
            for useCase, useCaseName in useCases.items():
                if useCase in assignedUseCases:
                    result[useCase] = useCaseName
            
            if not result:
                logging.error(f"No use cases assigned for spaceId: {spaceId}.")
                return None, status.HTTP_404_NOT_FOUND
            
            return result, status.HTTP_200_OK
        except Exception as e:
            logging.error(f"Error while fetching unassigned use cases for space {spaceId}: {e}")
            return None, status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def assignUseCase(self, spaceId: str, useCaseIds: list):
        try:
            if not isinstance(spaceId, str):
                return status.HTTP_400_BAD_REQUEST
            
            if not isinstance(useCaseIds, list):
                return status.HTTP_400_BAD_REQUEST
            
            result = self.applicationDB["spaces"].update_one(
                {"spaceId": spaceId},
                {"$addToSet": {"usecases": {"$each": useCaseIds}}}
            )

            if result.modified_count > 0:
                return status.HTTP_200_OK
            
            return status.HTTP_501_NOT_IMPLEMENTED
        
        except Exception as e:
            logging.error(f"Error while assigning usecase {useCaseIds} for space {spaceId}: {e}")
            return None, status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def getHierarchyIds(self, spaceId: str, useCaseId: str):
        try:
            if not isinstance(spaceId, str) or not isinstance(useCaseId, str):
                return status.HTTP_400_BAD_REQUEST
            
            hierarchyIds = list(self.applicationDB["hierarchys"].find({"spaceId": spaceId,"useCaseId": useCaseId},{"_id":0,"hierarchyName":0,"spaceId":0,"useCaseId":0,"createdBy":0,"useCaseRoles":0}))
            hierarchy_id_list = [hierarchy["hierarchyId"] for hierarchy in hierarchyIds]

            if not hierarchyIds:
                return status.HTTP_404_NOT_FOUND, None
            
            return status.HTTP_200_OK, hierarchy_id_list
        
        except Exception as e:
            logging.error(f"Error while fetching hierarchy Ids for space {spaceId} with usecase {useCaseId}: {e}")
            return None, status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def removeHierarchys(self, hierarchyIds: list):
        try:
            if not isinstance(hierarchyIds, list):
                return status.HTTP_400_BAD_REQUEST
            
            result = self.applicationDB["hierarchys"].delete_many({"hierarchyId": {"$in": hierarchyIds}})

            if not result.deleted_count > 0:
                return status.HTTP_304_NOT_MODIFIED

            return status.HTTP_200_OK
        except Exception as e:
            logging.error(f"Error while removing hierarchy: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def removeUseCase(self, spaceId: str, useCaseId: str):
        try:
            if not isinstance(spaceId, str) or not isinstance(useCaseId, str):
                return status.HTTP_400_BAD_REQUEST
            
            result = self.applicationDB["spaces"].update_one(
                {"spaceId": spaceId},
                {"$pull": {"usecases": useCaseId}}
            )

            if not result.modified_count > 0:
                return status.HTTP_404_NOT_FOUND

            return status.HTTP_200_OK
        except Exception as e:
            logging.error(f"Error while removing use cases from spaceId {spaceId}: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def getSpaceHiearchyIds(self, spaceId: str):
        try:
            hierarchyIds = list(self.applicationDB["hierarchys"].find({"spaceId": spaceId},{"_id":0,"hierarchyName":0,"spaceId":0,"useCaseId":0,"createdBy":0,"useCaseRoles":0}))
            hierarchy_id_list = [hierarchy["hierarchyId"] for hierarchy in hierarchyIds]
            if not hierarchyIds:
                return status.HTTP_404_NOT_FOUND, None
            else:
                return status.HTTP_200_OK, hierarchy_id_list
        except Exception as e:
            logging.error(f"Error while fetching hierarchy Ids for space {spaceId}: {e}")
            return None, status.HTTP_500_INTERNAL_SERVER_ERROR
    
    
        
    def removeOrganization(self, orgId: str):
        try:
            result = self.applicationDB["organizations"].delete_one(
                {"orgId": orgId}
            )
            if result.deleted_count==1:
                return status.HTTP_200_OK
            else:
                return status.HTTP_422_UNPROCESSABLE_ENTITY
        except Exception as e:
            logging.error(f"Error while removing Org: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def updateSpaceName(self, spaceId: str, spaceName: str):
        try:
            result = self.applicationDB["spaces"].update_one(
                {"spaceId": spaceId},
                {"$set": {"spaceName": spaceName}}
            )
            return status.HTTP_200_OK
        except Exception as e:
            logging.error(f"Error while removing space: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def updateOrganization(self, data: dict):
        try:
            # Check if orgName already exists
            existing_org_name = self.applicationDB["organizations"].find_one({"orgName": data.get("orgName")})
            if existing_org_name:
                logging.error("Org Name Already Existed")
                return status.HTTP_409_CONFLICT
            
            self.applicationDB["organizations"].update_one(
                {"orgId": data['orgId']},
                {"$set": {**data}}
            )
            return status.HTTP_200_OK
        except Exception as e:
            logging.error(f"Error while updating org: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def getHierarchyDetails(self, userId: list):
        try:
            hierarchyData = list(self.applicationDB["hierarchys"].find({
                "createdBy": userId
            }, {
                "_id":0,
                "hierarchyId": 1,
                "hierarchyName":1,
                "spaceId": 1
            }))
            if not hierarchyData:
                return None, status.HTTP_404_NOT_FOUND
            
            for hierarchy in hierarchyData:
                spaceData= self.applicationDB["spaces"].find_one({"spaceId": hierarchy["spaceId"]},{"_id":0,"spaceId":0,"createdBy":0,"usecases":0})
                spaceName = spaceData["spaceName"]
                hierarchy["spaceName"] = spaceName

            return hierarchyData, status.HTTP_200_OK
        except Exception as e:
            logging.error(f"Error while fetching hierarchy details: {e}")
            return None, status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def updateHierarchyName(self, hierarchyId: str, hierarchyName: str):
        try:
            result = self.applicationDB["hierarchys"].update_one(
                {"hierarchyId": hierarchyId},
                {"$set": {"hierarchyName": hierarchyName}}
            )
            return status.HTTP_200_OK
        except Exception as e:
            logging.error(f"Error while removing hierarchy: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def checkExistingUser(self, username: str, email: str):
        try:
            if not isinstance(username, str) or not isinstance(email, str):
                raise TypeError("Username and email should be strings.")
            
            if self.applicationDB is None:
                raise RuntimeError("applicationDB is not initialized.")
            
            userCollection = self.applicationDB["users"]
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
            # if not isinstance(userId, ObjectId):
            #     raise TypeError("UserId should be object")
            
            if self.applicationDB is None:
                raise RuntimeError("applicationDB is not initialized.")
            
            userData = self.applicationDB["users"].find_one({"_id": ObjectId(userId)})
            if userData:
                return status.HTTP_200_OK
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
            
            if self.applicationDB is None:
                raise RuntimeError("applicationDB is not initialized.")
            
            userCollection = self.applicationDB["users"]
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
            
            if self.applicationDB is None:
                raise RuntimeError("applicationDB is not initialized.")
            
            userCollection = self.applicationDB["users"]
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
            
            collection = self.applicationDB[collectionName]
            
            return collection.insert_one(data).inserted_id
        except TypeError as te:
            logging.error(str(te))
            raise
        except Exception as e:
            logging.error(f"Error inserting data into '{collectionName}' collection: {e}")
            raise
    
    def getUserCredentials(self, userId: str):
        try:
            user = self.applicationDB["users"].find_one(
                {"userId":ObjectId(userId)},
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
            # Ensure applicationDB is properly initialized
            if not hasattr(self, 'applicationDB') or self.applicationDB is None:
                logging.error("ApplicationDB is not initialized.")
                return {"status_code": status.HTTP_500_INTERNAL_SERVER_ERROR, "detail": "Internal server error"}, None
            # Attempt to find the user in the users table
            user = self.applicationDB["users"].find_one(
                {"username": username}
            )
            
            print("user id --",user)
            # Check if the user exists
            if not user:
                logging.info("User not found.")
                return {"status_code": status.HTTP_404_NOT_FOUND, "detail": "User not found"}, None

            # Retrieve user credentials from the userCredentials table using userId
            credentials = self.applicationDB["userCredentials"].find_one(
                {"userId": user["_id"]},
                {"_id": 0}
            )
            # Verify that credentials were found
            if not credentials:
                logging.error("Credentials not found for the user.")
                return {"status_code": status.HTTP_404_NOT_FOUND, "detail": "Credentials not found"}, None

            # Verify the password
            if check_password_hash(credentials["password"], password):
                # Successful authentication, so we return user data (excluding password)
                user_data = {key: value for key, value in user.items() if key != "_id"}
                user_data["lastLogin"] = credentials.get("lastLogin")
                logging.info(f"User {username} authenticated successfully.")
                return {"status_code": status.HTTP_200_OK, "detail": "Authentication successful"}, user
            else:
                logging.info("Invalid Credentials: Incorrect password.")
                return {"status_code": status.HTTP_401_UNAUTHORIZED, "detail": "Invalid credentials"}, None

        except Exception as e:
            logging.error(f"Error while checking user credentials: {e}")
            return {"status_code": status.HTTP_500_INTERNAL_SERVER_ERROR, "detail": "Internal server error"}, None


        
    def checkDeviceLogin(self, deviceHash: str, activeStatus: str):
        try:
            activeStatus = self.applicationDB["userAttributes"].find_one({"deviceHash": deviceHash, "activeStatus": activeStatus}, {"_id": 0})
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
            activeStatus = self.applicationDB["userAttributes"].find_one({"userId":ObjectId(userId)}, {"_id": 0, "userId": 0})
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
                "userId":ObjectId(userId),
                "deviceHash": deviceHash,
                "activeStatus": activeStatus
            }

            # Perform the update operation
            result = self.applicationDB["userAttributes"].insert_one(data)

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
        
    def update_last_login(self, userId):
        # Get the current UTC time
        current_time = datetime.utcnow()
        
        # Update the lastLogin field in userCredentials collection
        result = self.applicationDB["userCredentials"].update_one(
            {"userId": ObjectId(userId)},  # filter by userId
            {"$set": {"lastLogin": current_time}}  # set lastLogin to current UTC time
        )
        
        # Check if the update was successful
        if result.modified_count > 0:
            return status.HTTP_200_OK
        else:
            return status.HTTP_304_NOT_MODIFIED
    
    def addRefreshToken(self, userId: str, deviceHash: str, refreshToken: str) -> int:
        try:
            data = {
                "userId":ObjectId(userId),
                "deviceHash": deviceHash,
                "refreshToken": refreshToken
            }
            # Perform the update operation
            result = self.applicationDB["refreshTokens"].insert_one(data)

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
            result = self.applicationDB["userAttributes"].delete_one({"userId":ObjectId(userId), "deviceHash": deviceHash})

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
            result = self.applicationDB["refreshTokens"].delete_one({"userId":ObjectId(userId), "deviceHash": deviceHash})

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
            result = self.applicationDB["refreshTokens"].find_one({"userId":ObjectId(userId), "deviceHash": deviceHash})

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
            filter = {"userId":ObjectId(userId)}

            update_operation = {
                "$set": {
                    "password": password
                }
            }
            # Perform the update operation
            result = self.applicationDB["users"].update_one(filter, update_operation)

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
            userAttributes = self.applicationDB["userAttributes"].find_one({"userId":ObjectId(userId), "deviceHash": deviceHash}, {"_id": 0, "userId": 0})
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
            users = self.applicationDB["users"].find_one({"username": username, "role": role}, {"_id": 0})
            if users is not None:
                return status.HTTP_200_OK, users.get("userId")
            else:
                # User not found or user Id not available
                return status.HTTP_404_NOT_FOUND, None
        except Exception as e:
            # Log and handle unexpected errors
            logging.error(f"Error while checking users for user name {username}: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR, None
        
    def getUserDetails(self, userId: ObjectId):
        try:
            users = self.applicationDB["users"].find_one({"_id": ObjectId(userId)}, {"_id": 0})
            if users is not None:
                return status.HTTP_200_OK, users
            else:
                # User not found or user Id not available
                return status.HTTP_404_NOT_FOUND, None
        except Exception as e:
            # Log and handle unexpected errors
            logging.error(f"Error while checking users for userId {userId}: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR, None
    
    def getUserInfo(self, emailId: str):
        try:
            users = self.applicationDB["users"].find_one({"emailId": emailId}, {"_id": 0})
            if users is not None:
                return status.HTTP_200_OK, users.get("userId")
            else:
                # User not found or user Id not available
                return status.HTTP_404_NOT_FOUND, None
        except Exception as e:
            # Log and handle unexpected errors
            logging.error(f"Error while checking users for emailId {emailId}: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR, None
        
    def getUserOrg(self, userId: str):
        try:
            users = self.applicationDB["users"].find_one({"_id":ObjectId(userId)}, {"_id": 0})
            if users is not None:
                return status.HTTP_200_OK, users.get("orgId")
            else:
                # User not found or user Id not available
                return status.HTTP_404_NOT_FOUND, None
        except Exception as e:
            # Log and handle unexpected errors
            logging.error(f"Error while checking users for userId {userId}: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR, None
    
    def getAuthenticationDetails(self, userId: str):
        try:
            authenticationDetails = self.applicationDB["userAuthentication"].find_one({"userId":ObjectId(userId)}, {"_id": 0})
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
            filter = {"userId":ObjectId(userId)}

            # Construct the update operation
            update_operation = UpdateOne(filter, {"$set": data})

            # Perform the update operation using bulk_write with the update_operation
            result = self.applicationDB["userAuthentication"].bulk_write([update_operation])

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
            user = self.applicationDB["users"].find_one({"_id":ObjectId(userId)})
            if user and role in user.get("role", {}):
                return status.HTTP_200_OK
            else:
                # User not found or user Id not available
                return status.HTTP_404_NOT_FOUND
        except Exception as e:
            # Log and handle unexpected errors
            logging.error(f"Error while checking users for user id {userId}: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
        

    def unassignedAdmins(self, spaceId: str):
        try:
            # Check if spaceId is a string
            if not isinstance(spaceId, str):
                return status.HTTP_400_BAD_REQUEST, None

            unassignedAdmins = list(self.applicationDB["users"].find(
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
        
    def unassignSpace(self, orgId: str, userId: str, spaceId: str):
        try:
            # Validate input data
            if not isinstance(userId, str) or not isinstance(spaceId, str) or not isinstance(orgId, str):
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. userId and spaceId must be strings."
                }
            
            # Check if user exists and is an admin
            user = self.applicationDB["users"].find_one({"_id":ObjectId(userId)})
            if not user:
                return status.HTTP_404_NOT_FOUND
            
            user_role = user.get("role", {})
            user_orgs = user.get("orgIds")

            if orgId not in user_orgs:
               return status.HTTP_401_UNAUTHORIZED
            
            if "analyst" in user_role:
                spaceIds = [ spaceId for spaceIdList in user_role.get("analyst", {}).values() for spaceId in spaceIdList]
                if spaceId not in spaceIds:
                    return status.HTTP_409_CONFLICT
                self.applicationDB["users"].update_one({"_id":ObjectId(userId)}, {"$pull": {f"role.analyst.{orgId}": spaceId}})

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
            assignedAdmins = list(self.applicationDB["users"].find(
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
            unassigned_users = list(self.applicationDB["users"].find({
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
            assigned_users = self.applicationDB["users"].find({
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
            user = self.applicationDB["users"].find_one({"_id":ObjectId(userId),f"role.user.{hierarchyId}": useCaseRole})
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
            user = self.applicationDB["users"].find_one({"_id":ObjectId(userId)})
            if user and "user" in user.get("role", {}):
                hierarchyIds = user.get("role", {}).get("user", [])
                if hierarchyId in hierarchyIds:
                    return status.HTTP_409_CONFLICT
                self.applicationDB["users"].update_one({"_id":ObjectId(userId)}, {"$set": {f"role.user.{hierarchyId}": useCaseRole}})
                return status.HTTP_200_OK
            else:
                return status.HTTP_404_NOT_FOUND
        except Exception as e:
            # Log and handle unexpected errors
            logging.error(f"Error while assigning Role for user id {userId}: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def unassignUseCaseRole(self, userId: str, hierarchyId: str):
        try:
            user = self.applicationDB["users"].find_one({"_id":ObjectId(userId)})
            if user and "user" in user.get("role", {}):
                hierarchyIds = user.get("role", {}).get("user", [])
                if not hierarchyId in hierarchyIds:
                    return status.HTTP_409_CONFLICT
                self.applicationDB["users"].update_one({"_id":ObjectId(userId)}, {"$unset": {f"role.user.{hierarchyId}": ""}})
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
            
            if self.applicationDB is None:
                logging.error("Users database is not initialized.")
                return None, status.HTTP_500_INTERNAL_SERVER_ERROR
            
            # Query the document with the specified userId
            result = self.applicationDB["users"].find_one({"_id":ObjectId(userId)})
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
                result = self.applicationDB["users"].update_many(
                    {"role.user": {"$exists": True}, f"role.user.{hierarchyId}": {"$exists": True}},
                    {"$unset": {f"role.user.{hierarchyId}": ""}, "$pull": {"hierarchyId": hierarchyId}}
                )
                if not result.modified_count > 0:
                    return status.HTTP_304_NOT_MODIFIED
                 
            return status.HTTP_200_OK
        
        except Exception as e:
            logging.error(f"Error while removing hierarchy role for users: {e}")
            return None, status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def removeSpaceRole(self, spaceId: str):
        try:
            spaceId= spaceId
            result = self.applicationDB["users"].update_many(
                {"role.admin": {"$exists": True, "$in": [spaceId]}},
                {"$pull": {"role.admin": spaceId}}
            )
            if not result.modified_count >= 1:
                return status.HTTP_304_NOT_MODIFIED
            return status.HTTP_200_OK
        except Exception as e:
            logging.error(f"Error while removing hierarchy role for users: {e}")
            return None, status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def getAdminsDetails(self):
        try:
            # Find documents where the role is "admin" and project only the specified fields
            adminsDocuments = self.applicationDB["users"].find(
                {"role.admin": {"$exists": True},
                 "role.superadmin": {"$exists": False},
                "role.user": {"$exists": False},
                },{"contactNumber": 0})
            # Convert the cursor to a list of dictionaries
            adminsData = list(adminsDocuments)
            if adminsData:
                for admin in adminsData:
                    admin['userId'] = str(admin['_id'])
                    del admin['_id']  
                return status.HTTP_200_OK, adminsData
            else:
                return status.HTTP_404_NOT_FOUND,[]
        except Exception as e:
            logging.error(f"Error while removing space: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def updateProfile(self, data: dict, userId):
        try:
            status_code = self.checkUser(userId= userId)

            if status_code == 404:
                return status.HTTP_404_NOT_FOUND
            if status_code == 400:
                return status.HTTP_400_BAD_REQUEST
            # if not status_code == 302:
            #     return status.HTTP_500_INTERNAL_SERVER_ERROR
            
            updated = self.applicationDB["users"].update_one(
                {"_id": ObjectId(userId)},
                {"$set": {**data}}
            )

            if updated.modified_count == 1:
                return status.HTTP_200_OK
            else:
                return status.HTTP_302_FOUND       
                  
        except Exception as e:
            logging.error(f"Error while updating profile: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
    
    
    def updateUserDetails(self, data: object):
        try:
            status_code = self.checkUser(userId= data["userId"])
            if status_code == 404:
                return status.HTTP_404_NOT_FOUND
            if status_code == 400:
                return status.HTTP_400_BAD_REQUEST

            if data.get("username"):
                if not data.get("username") == "":
                    status_code = self.checkUserName(username= data["username"])
                    if status_code == 400:
                        return status.HTTP_400_BAD_REQUEST
                    if status_code == 500:
                        return status.HTTP_500_INTERNAL_SERVER_ERROR
                    if status_code == 302:
                        return status.HTTP_302_FOUND
                
            self.applicationDB["users"].update_one(
                {"_id":ObjectId(data["userId"])},
                {"$set": {**data}}
            )
                
            # if not data.get("username") == "":
            #     status_code = self.checkEmail(email= data["email"])
            #     print("------status2",status_code)
            #     if status_code == 400:
            #         return status.HTTP_400_BAD_REQUEST
            #     if status_code == 500:
            #         return status.HTTP_500_INTERNAL_SERVER_ERROR
            #     if status_code == 302:
            #         return status.HTTP_302_FOUND
            #     self.applicationDB["users"].update_one(
            #         {"_id":ObjectId(data["userId"])},
            #         {"$set": {"email": data["email"]}}
            #     )
            return status.HTTP_200_OK
        except Exception as e:
            logging.error(f"Error while updating user: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def createUserCollections(self):
        collections = ["users", "userAuthentication", "userAttributes", "refreshTokens"]
        try:
            if self.applicationDB is None:
                logging.error("usersDB is not initialized.")
                return False, 500  # MongoDB not initialized, return 500
            
            for collection_name in collections:
                if collection_name not in self.applicationDB.list_collection_names():
                    self.applicationDB.create_collection(collection_name)
                    logging.info(f"Collection '{collection_name}' created successfully.")
            return True, 200  # Collections created successfully, return 200
        except Exception as e:
            logging.error(f"Error creating collections: {e}")
            return False, 500  # Error occurred during collection creation, return 500
        
    def assignUserToOrg(self, orgId: str, userId: str):
        try:
            # Validate input data
            if not isinstance(userId, str) or not isinstance(orgId, str):
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. userId and orgId must be strings."
                }
            # Check if user exists and is an admin
            user = self.applicationDB["users"].find_one({"_id": ObjectId(userId)})

            if not user:
                return status.HTTP_404_NOT_FOUND
            
            user_orgIds = user.get("orgIds", [])
            
            if orgId in user_orgIds:
                return status.HTTP_409_CONFLICT

            self.applicationDB["users"].update_one({"_id": ObjectId(userId)}, {"$push": {"orgIds": orgId}})
            return status.HTTP_200_OK
            
        except Exception as e:
            # Log and handle unexpected errors
            logging.error(f"Error while assigning user {userId} for org id {orgId}: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def unassignUserToOrg(self, orgId: str, userId: str):
        try:
            # Validate input data
            if not isinstance(userId, str) or not isinstance(orgId, str):
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. userId and orgId must be strings."
                }
            
            # Check if user exists and is an admin
            user = self.applicationDB["users"].find_one({"_id":ObjectId(userId)})

            if not user:
                return status.HTTP_404_NOT_FOUND
            
            user_orgIds = user.get("orgIds", [])
            
            if orgId not in user_orgIds:
                return status.HTTP_409_CONFLICT

            result = self.applicationDB["users"].update_one({"_id":ObjectId(userId)}, {"$pull": {"orgIds": orgId}})
            # Check if the update modified any documents
            if result.modified_count > 0:
                logging.info("Update successful.")
            else:
                logging.info("No documents were updated.")
            return status.HTTP_200_OK
            
        except Exception as e:
            # Log and handle unexpected errors
            logging.error(f"Error while unassigning User {userId} for org id {orgId}: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR

    def getOrganizationsforAdmin(self, userId):
        try:
            if self.applicationDB is None:
                logging.error("Application database is not initialized.")
                return None, status.HTTP_500_INTERNAL_SERVER_ERROR
            
            adminDocument = self.applicationDB["users"].find(
                {"_id":ObjectId(userId), 
                },{"_id": 0, "role":1})
            adminDocument = list(adminDocument)
            org_ids = adminDocument[0]['role']['admin']
            if len(org_ids) > 0:
                adminOrgs = []
                for orgId in org_ids:
                    org ={}
                    orgName = self.applicationDB["organizations"].find_one({"orgId": orgId}, {"_id": 0, "orgName": 1})
                    org["orgId"] = orgId
                    org["orgName"] = orgName['orgName']
                    adminOrgs.append(org)

                return adminOrgs, status.HTTP_200_OK
            else:
                logging.info("No org found in application database for this admin.")
                return {}, status.HTTP_404_NOT_FOUND
        except Exception as e:
            logging.error(f"Error while retrieving spaces: {e}")
            return None, status.HTTP_500_INTERNAL_SERVER_ERROR    
        
    def assignSpace(self, orgId: str, userId: str, spaceId: str):
        try:
            # Validate input data
            if not isinstance(userId, str) or not isinstance(spaceId, str) or not isinstance(orgId, str):
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. userId and spaceId must be strings."
                }
            # Ensure the applicationDB is properly initialized
            if not hasattr(self, 'applicationDB') or self.applicationDB is None:
                logging.error("ApplicationDB is not initialized.")
                return status.HTTP_500_INTERNAL_SERVER_ERROR, None
            
            # Check if user exists and is an admin
            # applicationDB = ApplicationDataBase()
            if not hasattr(self.applicationDB, 'users'):
                logging.error("The 'users' collection does not exist in the applicationDB.")
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Database not initialized properly."
                }
        
            # Check if the user exists in the database
            user = self.applicationDB["users"].find_one({"_id":ObjectId(userId)})
            if not user:
                return status.HTTP_404_NOT_FOUND
            
            user_role = user.get("role", {})
            user_orgs = user.get("orgIds")
            if orgId not in user_orgs:
                return status.HTTP_401_UNAUTHORIZED
            
            if "analyst" in user_role:
                spaceIds = [ spaceId for spaceIdList in user_role.get("analyst", {}).values() for spaceId in spaceIdList]
                if spaceId in spaceIds:
                    return status.HTTP_409_CONFLICT
                self.applicationDB["users"].update_one({"_id":ObjectId(userId)}, {"$push": {f"role.analyst.{orgId}": spaceId}})

            # elif "user" in user_role:
            #     if spaceId in user_role.get("user", []):
            #         return status.HTTP_409_CONFLICT
            #     self.applicationDB["users"].update_one({"_id":ObjectId(userId)}, {"$push": {"role.user": spaceId}})


            return status.HTTP_200_OK
            
        except Exception as e:
            # Log and handle unexpected errors
            logging.error(f"Error while assigning space for user id {userId}: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def generateRandomKey(self):
        # Define the pattern lengths for each section
        pattern = [4, 4, 4, 4]
        
        # Generate each part of the key according to the pattern
        key_parts = [''.join(random.choices(string.ascii_uppercase + string.digits, k=part)) for part in pattern]
        
        # Join parts with hyphens
        return '-'.join(key_parts)
    
    def generate_id(self,length):
        result = ''
        characters = '0123456789'
        for i in range(length):
            result += random.choice(characters)
        return result

    def get_current_timestamp(self):
        return int(time.time())
    def createClientAPIKey(self, userId, orgId, keyName):
        try: 
            """Creates a new client API key if user is admin and key name is unique."""
            # Verify the user role
            user = self.applicationDB["users"].find_one({"_id": ObjectId(userId)})
            if not user or orgId not in user["role"]["admin"]:
                return 403,"Unauthorized access"    

            # Check if keyName is unique
            existing_key = self.applicationDB["clientApiKeys"].find_one({"keyName": keyName})
            if existing_key:
                return 409,"Key name already exists"

            # Generate the new API key and store it with the creation date
            new_key = self.generateRandomKey()
            utc_datetime = datetime.now(timezone.utc).replace(second=0, microsecond=0)
            api_key_data = {
                "createdBy": userId,
                "orgId":orgId,
                "keyName": keyName,
                "clientApiKey": new_key,
                "timestamp": int(utc_datetime.timestamp()),
                "status": "active"
            }
            
            self.applicationDB["clientApiKeys"].insert_one(api_key_data)
            return 200, new_key
        except Exception as e:
             # Log and handle unexpected errors
            logging.error(f"Error while creating key with keyName {keyName}: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR, str(e)


    def delete_clientApiKey(self, userId, orgId, keyName):
        try:
        # Verify the user role
            user = self.applicationDB["users"].find_one({"_id": userId})
            if not user or orgId not in user["role"]["admin"]:
                return 403,"Unauthorized access" 
            
            """Deletes the API key with the specified key name."""
            updated = self.applicationDB["clientApiKeys"].update_one(
                {"keyName": keyName, "userId": userId, "orgId": orgId}, 
                {"$set": {"status": "inactive", "deletedBy": userId}}
            )
            
            if updated.modified_count > 0:
                return {"status": 200, "detail": "API key deleted successfully"}
            return {"status": 404, "detail": "API key not found"}
        except Exception as e:
             # Log and handle unexpected errors
            logging.error(f"Error deleting key {keyName}: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR, str(e)
        
    def getClientAPIKeys(self, userId, orgId):
        try: 
            """Creates a new client API key if user is admin and key name is unique."""
            # Verify the user role
            user = self.applicationDB["users"].find_one({"_id": ObjectId(userId)})
            if not user or orgId not in user["orgIds"]:
                return 403,"Unauthorized access"    

            # Check if keyName is unique
            keys = list(self.applicationDB["clientApiKeys"].find({"orgId": orgId, "status":"active"}, {"_id":0, "status": 0}))
            if not keys:
                return 404,f"No keys found for orgId {orgId}"
            for key in keys:
                createdBy = key.get("createdBy")
                timestamp = key.get("timestamp")

                # Convert timestamp to datetime object
                date = datetime.fromtimestamp(timestamp)
                # Format the date
                day = date.day
                month = date.strftime("%B")  # Full month name
                year = date.year
                key["timestamp"]=f"{day} {month} {year}"
                status_code, username = self.getUserDetails(createdBy)
                if status_code == 200:
                    key["createdBy"] = username.get("username")
                else:
                    key["createdBy"] = ""
            return 200, keys
        except Exception as e:
             # Log and handle unexpected errors
            logging.error(f"Error while getting keys for orgId {orgId}: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR, str(e)

    

    def getProfile(self, userId):
        try:
            
            if self.applicationDB is None:
                logging.error("Application database is not initialized.")
                return status.HTTP_500_INTERNAL_SERVER_ERROR, None
            
            user = self.applicationDB["users"].find_one({"_id": ObjectId(userId)},{"_id":0,"role":0})
            if user:
                return status.HTTP_200_OK, user
            else:
                logging.error(f"No data found for userId: {userId}.")
                return status.HTTP_404_NOT_FOUND, None
            
        except Exception as e:
            logging.error(f"Error while retrieving data for userId {userId}: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR, None
        
        
    def add_prompt(self, json_data):
        try:
            # Ensure the database is initialized
            if self.applicationDB is None:
                logging.error("Application database is not initialized.")
                return status.HTTP_500_INTERNAL_SERVER_ERROR, {"error": "Database not initialized"}

            # Check if required fields are present
            required_fields = ["clientApiKey", "appType"]
            missing_fields = [field for field in required_fields if field not in json_data]
            if missing_fields:
                logging.error(f"Missing required fields: {missing_fields}")
                return status.HTTP_400_BAD_REQUEST, {"error": f"Missing fields: {missing_fields}"}
            # Generate a unique promptId and timestamp
            prompt_id = self.generate_id(4)  # Generate a unique promptId
            timestamp = self.get_current_timestamp()  # Get the current timestamp in ISO format
            # Add promptId and timestamp to json_data
            json_data["promptId"] = prompt_id
            json_data["timestamp"] = timestamp
            # Access the prompts collection
            prompts = self.applicationDB["LLMPrompts"]
            
            # Log the collection details
            logging.info(f"Accessing collection 'LLMPrompts' in database: {self.applicationDB.name}")
            logging.info(f"json_data to be inserted: {json_data}")
            # Check if the promptId already exists for the same clientApiKey
            existing_prompt = prompts.find_one({"clientApiKey": json_data["clientApiKey"], "promptId": prompt_id})
            if existing_prompt:
                logging.error(f"PromptId {prompt_id} already exists for clientApiKey {json_data['clientApiKey']}")
                return status.HTTP_400_BAD_REQUEST, {"error": f"PromptId {prompt_id} already exists for this clientApiKey"}

            # Insert the data into the MongoDB collection
            try:
                # If the collection does not exist, MongoDB will create it automatically
                logging.info(f"Inserting data into 'LLMPrompts' collection.")
                result = prompts.insert_one(json_data)
                if result.inserted_id:
                    logging.info(f"Prompt added successfully with ID: {result.inserted_id}")
                    return status.HTTP_200_OK, {"message": "Prompt added successfully"}
                else:
                    logging.error("Failed to insert the prompt. Result: {result}")
                    return status.HTTP_500_INTERNAL_SERVER_ERROR, {"error": "Database insertion failed"}
            except Exception as e:
                logging.error(f"Error inserting prompt into database: {e}")
                return status.HTTP_500_INTERNAL_SERVER_ERROR, {"error": "Database insertion failed"}

        except Exception as e:
            logging.error(f"Unexpected error in add_prompt: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR, {"error": "An unexpected error occurred"}

    def get_llm_prompts_data(self):
        try:
            # Establishing a connection to the MongoDB client
           
            llm_prompts = self.applicationDB["LLMPrompts"]
            # Fetching all documents, excluding the _id field, and sorting by timestamp in descending order
            llm_prompts_cursor = llm_prompts.find({}, {"_id": 0}).sort("timestamp", -1)

            # Convert the cursor to a list and return the data
            result = list(llm_prompts_cursor)

            # Log the retrieved data
            logging.info("Retrieved data: %s", result)
            return result

        except ConnectionError as e:
            logging.error(f"Connection error while accessing the database: {e}")
            return {"error": "Database connection failed", "detail": str(e)}
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return {"error": "An unexpected error occurred", "detail": str(e)}
        
    def update_prompt(self,json_data):
        """
        Updates the prompt in the MongoDB collection.
        
        :param json_data: Dictionary containing the prompt data to update.
        :return: Boolean indicating success or failure.
        """
        try:
            prompts =self.applicationDB["LLMPrompts"]
            client_api_key = json_data["clientApiKey"]
            prompt_id = json_data["promptId"]
            # Delete the existing record
            delete_record = {"clientApiKey": client_api_key, "promptId": prompt_id}
            prompts.delete_one(delete_record)
            # Adjust fields based on appType
            if json_data["appType"] == "simple":
                json_data.pop("memoryType", None)
                json_data.pop("kValue", None)
                json_data.pop("tokenLimit", None)
            elif json_data["appType"] == "conversational":
                memory_type = json_data.get("memoryType", "")
                if memory_type in ["buffer", "summarised"]:
                    json_data.pop("kValue", None)
                    json_data.pop("tokenLimit", None)
                elif memory_type == "windowBuffer":
                    json_data.pop("tokenLimit", None)
                elif memory_type == "tokenBuffer":
                    json_data.pop("kValue", None)

            # Add timestamp
            json_data["timestamp"] = datetime.utcnow()

            # Insert the updated prompt
            prompts.insert_one(json_data)
            return True

        except Exception as e:
            print(f"Error updating prompt: {e}")
            return False    
    def delete_prompt(self, json_data):
        """
        Deletes one or more prompts from the MongoDB collection.

        :param json_data: Dictionary containing required keys:
                        - "clientApiKey": The API key for identifying the client.
                        - "promptId": A single prompt ID (str) or a list of prompt IDs (list).
        :return: Dictionary with details of the operation.
        """
        try:
            # Extract client API key and prompt ID from input data
            client_api_key = json_data.get("clientApiKey")
            prompt_id = json_data.get("promptId")

            # Validate required fields
            if not client_api_key or not prompt_id:
                logging.error("Missing required fields: 'clientApiKey' or 'promptId'")
                return {"status_code": 400, "detail": "Missing 'clientApiKey' or 'promptId'."}

            # Check if clientApiKey exists in the database
            client_exists = self.applicationDB["LLMPrompts"].find_one({"clientApiKey": client_api_key})
            if not client_exists:
                logging.error(f"Invalid clientApiKey: {client_api_key}")
                return {"status_code": 404, "detail": "Invalid 'clientApiKey'. No matching client found."}

            # Access the MongoDB collection
            prompts = self.applicationDB["LLMPrompts"]

            # Check if prompt_id is a list or a single value
            if isinstance(prompt_id, list):
                # For multiple deletions, use delete_many with $in operator
                query = {"clientApiKey": client_api_key, "promptId": {"$in": prompt_id}}
                result = prompts.delete_many(query)
            else:
                # For single deletion, use delete_one
                query = {"clientApiKey": client_api_key, "promptId": prompt_id}
                result = prompts.delete_one(query)

            # Return appropriate details
            if result.deleted_count > 0:
                return {"deleted_count": result.deleted_count, "status_code": 200}
            else:
                return {"status_code": 404, "detail": "No matching prompts found to delete."}

        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return {"status_code": 500, "detail": "Unexpected server error."}


    def add_payload(self, document):
        """
        Saves payload to MongoDB.

        :param organisation: Name of the organisation (used as a collection name).
        :param document: Dictionary containing `clientApiKey` and `parsedContent`.
        :return: Dictionary with success status, payloadId, or error message.
        """
        try:
            # Extract fields from the document
            client_api_key = document.get("clientApiKey")
            parsed_content = document.get("parsedContent")
            payloadPath = document.get("path")
            # Validate required fields
            if not client_api_key or not parsed_content:
                missing_fields = []
                if not client_api_key:
                    missing_fields.append("clientApiKey")
                if not parsed_content:
                    missing_fields.append("parsedContent")
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

            # Generate payloadId from the current timestamp
            payload_id = self.generate_id(4)
            timestamp = self.get_current_timestamp()
            # Process the parsed content
            processed_payloads = [
                {
                    "payloadName": payload_name,
                    "items": [
                        {
                            "index": item["index"],
                            "question": item["question"],
                            "answer": item["answer"]
                        }
                        for item in items
                    ]
                }
                for payload_name, items in parsed_content.items()
            ]

            # Create the full document to insert into MongoDB
            payload_document = {
                "payloadId": payload_id,
                "clientApiKey": client_api_key,
                "payloadPath":payloadPath,
                "payloads": processed_payloads,
                "timestamp":timestamp
            }

            # Insert the document into the MongoDB collection
            payload_collection = self.applicationDB["payload"]
            insert_result = payload_collection.insert_one(payload_document)

            # Check if the insertion was successful
            if not insert_result.acknowledged:
                raise Exception("Failed to insert document into MongoDB.")

            # Return success
            return {"success": True, "payloadId": payload_id}

        except ValueError as ve:
            # Validation errors
            print(f"Validation Error: {ve}")
            return {"success": False, "error": str(ve)}

      
        except Exception as e:
            # Generic error handling
            print(f"An unexpected error occurred: {e}")
            return {"success": False, "error": f"An unexpected error occurred: {str(e)}"}
        
    def get_payload_details(self):
            """
            Fetches payload details from the MongoDB collection for the given organisation.

            :param organisation: Name of the organisation (used as a database name).
            :return: List of payload details or an error message.
            """
            try:

                # Connect to the organisation database and collection
                db = self.applicationDB
                payload_collection = db["payload"]

                # Query the collection for payload details, excluding the "_id" field
                payload_data = list(
                    payload_collection.find({}, {"_id": 0}).sort("timestamp", DESCENDING)
                )

                if not payload_data:
                    logging.warning("No payload data found.")
                    return {"success": False, "message": "No payload data found."}

                logging.info(f"Payload data fetched successfully: {len(payload_data)} records.")
                return {"success": True, "data": payload_data}

            except Exception as e:
                logging.error(f"An unexpected error occurred: {e}")
                return {"success": False, "error": "An unexpected error occurred."}    

    def delete_payload(self, json_data):
        """
        Deletes one or more payloadss from the MongoDB collection.

        :param json_data: Dictionary containing required keys:
                        - "clientApiKey": The API key for identifying the client.
                        - "payloadId": A single payload ID (str) or a list of payload IDs (list).
        :return: Dictionary with details of the operation:
                - "deleted_count": Number of deleted payloads.
                - "status_code": HTTP status code.
        """
        try:
            # Extract client API key and prompt ID from input data
            client_api_key = json_data.get("clientApiKey")
            payloadId = json_data.get("payloadId")
          
            # Validate required fields
            if not client_api_key or not payloadId:
                logging.error("Missing required fields: 'clientApiKey' or 'payloadId'")
                return {"status_code": 400, "detail": "Missing 'clientApiKey' or 'payloadId'."}

            # Access the MongoDB collection
            prompts = self.applicationDB["payload"]

            # Check if prompt_id is a list or a single value
            if isinstance(payloadId, list):
                # For multiple deletions, use delete_many with $in operator
                query = {"clientApiKey": client_api_key, "payloadId": {"$in": payloadId}}
                result = prompts.delete_many(query)
            else:
                # For single deletion, use delete_one
                query = {"clientApiKey": client_api_key, "payloadId": payloadId}
                result = prompts.delete_one(query)

            # Return appropriate details
            return {"deleted_count": result.deleted_count, "status_code": 200 if result.deleted_count > 0 else 404}

        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return {"status_code": 500, "detail": "Unexpected server error."}


    def add_model(self, json_data):
        try:
            model_type = json_data["modelType"].lower()
            if model_type == "stt":
                collection_name = "STTModels"
            elif model_type == "llm":
                collection_name = "LLMModels"
            elif model_type == "rag":
                collection_name = "EmbeddingModels"
            else:
                logging.error(f"Invalid modelType: {model_type}")
                return (400, False)

            db = self.applicationDB
            collection = db[collection_name]
            client_api_key = json_data["clientApiKey"]
            mode = json_data["mode"]
            print("jsondata",json_data)
            model_id = None
            while True:
                model_id = self.generate_id(4)
                if not collection.find_one({"clientApiKey": client_api_key, "modelId": model_id}):
                    break

            model_data = {
                "clientApiKey": client_api_key,
                "modelId": model_id,
                "mode": mode,
                "modelType": json_data["modelType"],
                "modelName": json_data["modelName"],
                "engine": json_data["engine"],
                "timestamp": self.get_current_timestamp(),
            }
            collection.insert_one(model_data)
            return (200, True)

        except KeyError as e:
            logging.error(f"KeyError: {e}")
            return (400, False)

        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return (500, False)
    def get_model_details(self, model: str):
        """
        Fetches model details from MongoDB for a specific model type.

        :param model: Model type ('llm', 'stt', 'rag', etc.).
        :return: List of model details as dictionaries or None in case of an error.
        """
        try:
            # Validate model type
            if not model or not isinstance(model, str):
                logging.error("Invalid or missing model type.")
                return None

            # Handle special case for "rag"
            if model.lower() == "rag":
                collection_name = "EmbeddingModels"
            else:
                collection_name = f"{model.upper()}Models"

            # Access the appropriate collection
            db = self.applicationDB
            if collection_name not in db.list_collection_names():
                logging.error(f"Collection '{collection_name}' does not exist in the database.")
                return None

            models_collection = db[collection_name]

            # Fetch all records sorted by timestamp
            model_details = list(
                models_collection.find(
                    {},  # No filter, fetch all records
                    {"_id": 0}  # Exclude _id field
                ).sort("timestamp", DESCENDING)
            )

            if not model_details:
                logging.warning(f"No records found in collection '{collection_name}'.")
                return None

            logging.info(f"Fetched {len(model_details)} records from collection '{collection_name}'.")
            return model_details
        except Exception as e:
            logging.error(f"Unexpected error occurred: {e}")
            return None
        
  
    def delete_model(self, json_data):
        """
        Deletes one or more models from the MongoDB collection.

        :param json_data: Dictionary containing required keys:
                        - "clientApiKey": The API key for identifying the client.
                        - "modelId": A single payload ID (str) or a list of payload IDs (list).
        :return: Dictionary with details of the operation:
                - "deleted_count": Number of deleted payloads.
                - "status_code": HTTP status code.
        """
        try:
            # Extract client API key and modelId from input data
            client_api_key = json_data.get("clientApiKey")
            modelId = json_data.get("modelId")
            model_type = json_data["modelType"].lower()
            # Validate required fields
            if not client_api_key or not modelId or not model_type:
                logging.error("Missing required fields: 'clientApiKey' or 'modelId'")
                return {"status_code": 400, "detail": "Missing 'clientApiKey' or 'modelId'."}
            if model_type == "stt":
                collection_name = "STTModels"
            elif model_type == "llm":
                collection_name = "LLMModels"
            elif model_type == "rag":
                collection_name = "EmbeddingModels"
            else:
                logging.error(f"Invalid modelType: {model_type}")
                return (400, False)
            # Access the MongoDB collection
            models = self.applicationDB[collection_name]

            # Check if modelId is a list or a single value
            if isinstance(modelId, list):
                # For multiple deletions, use delete_many with $in operator
                query = {"clientApiKey": client_api_key, "modelId": {"$in": modelId}}
                result = models.delete_many(query)
            else:
                # For single deletion, use delete_one
                query = {"clientApiKey": client_api_key, "modelId": modelId}
                result = models.delete_one(query)

            # Return appropriate details
            return {"deleted_count": result.deleted_count, "status_code": 200 if result.deleted_count > 0 else 404}

        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return {"status_code": 500, "detail": "Unexpected server error."}

      