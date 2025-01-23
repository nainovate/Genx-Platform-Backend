import os
import logging
from pymongo.mongo_client import MongoClient
from fastapi import status
from pymongo.errors import OperationFailure

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


class ApplicationDataBase:
    def __init__(self):
        self.status_code = None  # Default status code
        try:
            db_uri = "mongodb://"+mongo_ip+":"+mongo_port+"/"
            self.client = MongoClient(db_uri)
            self.applicationDB = self._get_application_db()
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
    
    def createSpace(self, spaceName: str, spaceId: str, usecases: list, userId: str):
        try:
            # Validate input types
            if not isinstance(spaceName, str) or not isinstance(spaceId, str) or not isinstance(usecases, list) or not isinstance(userId, str):
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
                "usecases": usecases,
                "createdBy": userId
            }

            # Insert the new space data into the database
            if self.applicationDB["spaces"].insert_one(data):
                logging.info(f"Space {spaceName} created successfully with space id {spaceId}")
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
    
    def removeSpace(self, spaceId: str):
        try:
            result = self.applicationDB["spaces"].delete_one(
                {"spaceId": spaceId}
            )
            return status.HTTP_200_OK
        except Exception as e:
            logging.error(f"Error while removing space: {e}")
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
        
    
        
    
