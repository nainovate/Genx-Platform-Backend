import os
import logging
import yaml
from fastapi import  HTTPException, status
from Database.users import *
from Database.applicationDataBase import *
from ApplicationManagment.usecases import *
from Database.hierarchyDataBase import *
import random
import string


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


def initilizeApplicationDB():
    applicationDB = ApplicationDataBase()
    return applicationDB

def initilizeUserDB():
    try:
        userDB = UsersSetup()
        return userDB
    except Exception as e:
        logging.error(f"Error while getting userDB: {e}")
        return None
    
def initilizeApplicationConfigDB():
    applicationDB = ApplicationSetup()
    return applicationDB

def initilizeHierarchyDB(hierarchyId: str):
    HierarchyDB = HierarchyDataBase(hierarchyId= hierarchyId)
    return HierarchyDB


def generate_space_id():
    space_id = "".join(random.choice(string.ascii_lowercase) for _ in range(4))
    return space_id 

class Spaces:
    def __init__(self, userId: str, role: dict):
        self.role = role
        self.userId = userId
        self.applicationDB = initilizeApplicationDB()
        self.applicationconfigDB = initilizeApplicationConfigDB()
        self.userDB = initilizeUserDB()

    def createSpace(self, data: dict):
        try:
            if not isinstance(data, dict) or ("spaceName" and "useCases" not in data) or len(data) != 2:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. Expected a dictionary with only 'spaceName' key."
                }

            if not "superadmin" in self.role:
                return {
                        "status_code": status.HTTP_401_UNAUTHORIZED,
                        "detail": "Unauthorized Access"
                }
            spaceName = data["spaceName"]
            useCases = data["useCases"]

            if not isinstance(useCases, list):
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. Expected useCases as list"
                }
            
            spaceId = generate_space_id()

            status_code = self.applicationDB.createSpace(spaceName = spaceName, spaceId = spaceId, usecases = useCases, userId = self.userId)

            if status_code == 400:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data types. Expected strings for spaceName, spaceId, userId, and a list for usecases."
                }
            
            if status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
                while status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
                    spaceId = generate_space_id()
                    status_code = self.applicationDB.createSpace(spaceName = spaceName, spaceId = spaceId, usecases = useCases, userId = self.userId)
                if status_code == 400:
                    return {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "detail": "Invalid input data types. Expected strings for spaceName, spaceId, userId, and a list for usecases."
                    }
            
                if status_code == status.HTTP_409_CONFLICT:
                    return {
                            "status_code": status.HTTP_409_CONFLICT,
                            "detail": "Space Name Already Existed"
                    }

            if status_code == status.HTTP_409_CONFLICT:
                return {
                        "status_code": status.HTTP_409_CONFLICT,
                        "detail": "Space Name Already Existed"
                }
            
            if not status_code == 200:
                return {
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "detail": "Internal server error occurred."
                }
    
            return {
                "status_code": status_code,
                "detail": "Space Created Successfully"
            }
        except Exception as e:
            logging.error(f"Error while creating space: {e}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail":f"{e}"
            }
        
    def getSpaces(self):
        try:
            if not "superadmin" in self.role:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail": "Unauthorized Access",
                }
            
            spaces, status_code = self.applicationDB.getSpaces()

            if status_code == status.HTTP_404_NOT_FOUND:
                return {
                        "status_code": status.HTTP_404_NOT_FOUND, 
                        "detail": "No spaces found in application database."
                }
            
            if not status_code == 200:
                return {
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "detail": "Internal server error occurred."
                }

            return {
                "status_code": status_code,
                "spaces": spaces
            }
        
        except Exception as e:
            logging.error(f"Error while retrieving spaces: {e}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"{e}"
            }      
    
    def assignSpace(self, data: dict):
        try:
            expected_keys = {"spaceId", "userIds"}
            if not isinstance(data, dict) or not data.keys() == expected_keys:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. Expected a dictionary with keys 'spaceId' and 'userIds'."
                }
        
            spaceId = data["spaceId"]
            userIds = data["userIds"]

            if not isinstance(userIds, list):
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. 'userIds' must be a list."
                }
        
            if not "superadmin" in self.role:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail":"Unauthorized Access",
                }
            
            status_code = self.applicationDB.checkSpace(spaceId = spaceId)

            if status_code == 400:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid spaceId. Expected a string."
                }
            
            if status_code == 404:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": f"Space Not Found for spaceId: {spaceId}",
                }
            
            if not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error",
                }
            
            for userId in userIds:
                status_code = self.userDB.assignSpace(userId= userId, spaceId= spaceId)

                if status_code == 400:
                    return {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "detail": "Invalid input data. userId and spaceId must be strings."
                    }
                
                if status_code == 404:
                    return {
                        "status_code": status.HTTP_404_NOT_FOUND,
                        "detail": "User not found."
                    }
                
                if status_code == 403:
                    return {
                        "status_code": status.HTTP_403_FORBIDDEN,
                        "detail": "User is not an admin and cannot be assigned a space."
                    }
                
                if status_code == 409:
                    return {
                        "status_code": status.HTTP_409_CONFLICT,
                        "detail": "Space Already Assigned To Admin",
                    }
                
                if not status_code == 200:
                    return {
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "detail": "Internal server error",
                    }
                
            return {
                "status_code": status_code,
                "detail": f"Space {spaceId} assigned to user {userId} successfully."
            }
        
        except Exception as e:
            logging.error(f"Error while assigning space for user id {userId}: {e}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"{e}"
            }
        
    def unassignSpace(self, data: dict):
        try:
            expected_keys = {"spaceId", "userIds"}
            if not isinstance(data, dict) or not data.keys() == expected_keys:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. Expected a dictionary with keys 'spaceId' and 'userIds'."
                }
        
            spaceId = data["spaceId"]
            userIds = data["userIds"]

            if not isinstance(userIds, list):
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. 'userIds' must be a list."
                }
        
            if not "superadmin" in self.role:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail":"Unauthorized Access",
                }
            
            status_code = self.applicationDB.checkSpace(spaceId = spaceId)

            if status_code == 400:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid spaceId. Expected a string."
                }
            
            if status_code == 404:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": f"Space Not Found for spaceId: {spaceId}",
                }
            
            if not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error",
                }
            
            for userId in userIds:
                status_code = self.userDB.unassignSpace(userId = userId, spaceId = spaceId)

                if status_code == 400:
                    return {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "detail": "Invalid input data. userId and spaceId must be strings."
                    }
                
                if status_code == 404:
                    return {
                        "status_code": status.HTTP_404_NOT_FOUND,
                        "detail": "User not found."
                    }
                
                if status_code == 403:
                    return {
                        "status_code": status.HTTP_403_FORBIDDEN,
                        "detail": "User is not an admin and cannot be assigned a space."
                    }
                
                if status_code == 409:
                    return {
                        "status_code": status.HTTP_409_CONFLICT,
                        "detail": "Space Already Unassigned To Admin",
                    }
                
                if not status_code == 200:
                    return {
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "detail": "Internal server error",
                    }
                
            return {
                "status_code": status_code,
                "detail": f"Space {spaceId} unassigned from user {userId} successfully."
            }
        
        except Exception as e:
            logging.error(f"Error while unassigning space for user id {userId}: {e}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"{e}"
            }
    
    def getAssignedSpaces(self):
        try:
            if not "admin" in self.role:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail":"Unauthorized Access",
                }
            
            spaces, status_code = self.userDB.getAssignedSpaces(userId = self.userId)

            if status_code == status.HTTP_400_BAD_REQUEST:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. userId must be strings."
                }
            
            if status_code == 403:
                return {
                    "status_code": status.HTTP_403_FORBIDDEN,
                    "detail": "User is not an admin and cannot get assigned spaces."
                }

            if status_code == status.HTTP_404_NOT_FOUND:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": f"No assigned spaces found found for userId: {self.userId}"
                }
            
            if not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error occurred."
                }
            
            spacesList = []

            for space in spaces:
                spaceName, status_code = self.applicationDB.getSpaceName(spaceId = space)

                if status_code == 404:
                    return {
                        "status_code": status.HTTP_404_NOT_FOUND,
                        "detail": f"No space found for spaceId: {space}."
                    }
                
                if not status_code == 200:
                    return {
                            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                            "detail": "Internal server error occurred."
                    }
                
                assignedSpaces = {}
                assignedSpaces[space] = spaceName
                spacesList.append(assignedSpaces)

            return {
                "status_code": status.HTTP_200_OK,
                "assignedSpaces": spacesList
            }
                
        except Exception as e:
            logging.error(f"Error while retrieving assigned spaces for userId{self.userId}: {e}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"{e}"
            }

    def getSpaceUseCases(self,usecaseInstance: object, spaceId: str):
        try:
            if not isinstance(spaceId, str):
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid spaceId. Expected a string."
                }
            
            if not isinstance(usecaseInstance, UseCases):
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid usecaseInstance. Expected an instance of YourUseCaseClass."
                }
            
            spaceId= spaceId

            if not "admin" in self.role:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail":"Unauthorized Access",
                }
            
            status_code = self.applicationDB.checkSpace(spaceId = spaceId)

            if status_code == 400:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid spaceId. Expected a string."
                }
            
            if status_code == 404:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": f"Space Not Found for spaceId: {spaceId}",
                }
            
            if not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error",
                }
            
            spaceUseCases, status_code = self.applicationDB.getSpaceUseCases(spaceId= spaceId)

            if status_code == 400:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid spaceId. Expected a string."
                }
            
            if status_code == 404:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": f"No space use cases found for spaceId: {spaceId}."
                }
            
            if not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error occurred."
                }
            
            useCases = {}
            for usecase in spaceUseCases:
                status_code, useCaseName = usecaseInstance.getUseCaseName(useCaseId= usecase)

                if status_code == 400:
                    return {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "detail": "Invalid useCaseId. Expected a string."
                    }
                
                if status_code == 404:
                    return {
                        "status_code": status.HTTP_404_NOT_FOUND,
                        "detail": f"No use case name found for useCaseId: {usecase}."
                    }
                
                if not status_code == 200:
                    return {
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "detail":"Internal server error occurred."
                    }
                
                useCases[usecase] = useCaseName

            return {
                "status_code": status.HTTP_200_OK,
                "spaceUseCases": useCases
            }
        
        except Exception as e:
            logging.error(f"Error while retrieving space use cases for space Id {spaceId}: {e}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"{e}"
            }   

    def getSpaceId(self, hierarchyId: str):
        try:
            if not isinstance(hierarchyId, str):
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid hierarchyId. Expected a string."
                }
            
            status_code = self.applicationDB.checkHierarchy(hierarchyId= hierarchyId)

            if status_code == 400:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid hierarchyId. Expected a string."
                }
            
            if status_code == 404:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "Hierarchy Not Found",
                }
            
            if not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error",
                }
            
            spaceId, status_code = self.applicationDB.getSpaceId(hierarchyId= hierarchyId)

            if status_code == 400:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid hierarchyId. Expected a string."
                }
            
            if status_code == status.HTTP_404_NOT_FOUND:
                return{
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": f"No spaceId found for hierarchyId: {hierarchyId}."
                }
            
            if not status_code == 200:
                 return{
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error occurred."
                }
            
            return spaceId

        except Exception as e:
            logging.error(f"Error while getting spaceId for hierarchy id {hierarchyId}: {e}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"{e}"
            }
    
    def getUnassignedUseCases(self, spaceId: str):
        try:
            if not isinstance(spaceId, str):
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid spaceId. Expected a string."
                }
            
            if not "superadmin" in self.role:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail":"Unauthorized Access",
                }
            
            status_code = self.applicationDB.checkSpace(spaceId= spaceId)

            if status_code == 400:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid spaceId. Expected a string."
                }
            
            if status_code == 404:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": f"Space Not Found for spaceId: {spaceId}",
                }
            
            if not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error",
                }
            
            unassignedUseCases, status_code = self.applicationDB.getUnassignedUseCases(spaceId= spaceId, configInstance= self.applicationconfigDB)

            if status_code == 400:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid configInstance. Expected an object with a callable method 'getUseCases'."
                }
            
            if status_code == status.HTTP_404_NOT_FOUND:
                return{
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": f"All use cases are assigned to spaceId: {spaceId}"
                }
            
            if not status_code == 200:
                return{
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error occurred."
                }
            
            return {
                "status_code": status_code,
                "unassignedUseCases": unassignedUseCases
            }
        
        except Exception as e:
            logging.error(f"Error while fetching unassigned use cases for space {spaceId}: {e}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"{e}"
            }
    
    def getAssignedUseCases(self, spaceId: str):
        try:
            if not isinstance(spaceId, str):
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid spaceId. Expected a string."
                }
            
            if not "superadmin" in self.role:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail":"Unauthorized Access",
                }
            
            status_code = self.applicationDB.checkSpace(spaceId= spaceId)

            if status_code == 400:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid spaceId. Expected a string."
                }
            
            if status_code == 404:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": f"Space Not Found for spaceId: {spaceId}",
                }
            
            if not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error",
                }
            
            assignedUseCases, status_code = self.applicationDB.getAssignedUseCases(spaceId= spaceId, configInstance= self.applicationconfigDB)
            
            if status_code == 400:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid configInstance. Expected an object with a callable method 'getUseCases'."
                }
            
            if status_code == status.HTTP_404_NOT_FOUND:
                return{
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": f"No use cases are assigned to spaceId: {spaceId}"
                }
            
            if not status_code == 200:
                return{
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error occurred."
                }
            
            return {
                "status_code": status_code,
                "assignedUseCases": assignedUseCases
            }
        except Exception as e:
            logging.error(f"Error while retrieving assignedUseCases for space Id: {e}")
            return{
                "status_code":status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail":f"{e}"
            }
    
    def assignUseCase(self, data: dict):
        try:
            expected_keys = {"spaceId", "useCaseIds"}

            if not isinstance(data, dict) or not data.keys() == expected_keys:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. Expected a dictionary with keys 'spaceId' and 'useCaseIds'."
                }
        
            spaceId = data["spaceId"]
            useCaseIds = data["useCaseIds"]

            if not isinstance(useCaseIds, list):
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. 'useCaseIds' must be a list."
                }
        
            if not "superadmin" in self.role:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail":"Unauthorized Access",
                }
            
            status_code = self.applicationDB.checkSpace(spaceId= spaceId)

            if status_code == 400:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid spaceId. Expected a string."
                }
            
            if status_code == 404:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": f"Space Not Found for spaceId: {spaceId}",
                }
            
            if not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error",
                }
            
            for useCaseId in useCaseIds:
                status_code = self.applicationconfigDB.checkUseCases(useCaseId= useCaseId)

                if status_code == 400:
                    return {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "detail": "Invalid input data. Expected a useCaseId in string."
                    }

                if status_code == 404:
                    return {
                        "status_code": status.HTTP_404_NOT_FOUND,
                        "detail": f"UseCase Not Found for useCaseId {useCaseId}",
                    }
                
                if not status_code == 200:
                    return {
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "detail": "Internal server error",
                    }

            status_code = self.applicationDB.assignUseCase(spaceId= spaceId, useCaseIds= useCaseIds)

            if status_code == 400:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. spaceId must be a string and useCaseIds must be a list"
                }

            if status_code == 501:
                return {
                    "status_code": status.HTTP_501_NOT_IMPLEMENTED,
                    "detail": "Use Cases are not assigend to space"
                }
            
            if not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal Server Error"
                }
            
            return {
                "status_code": status_code,
                "detail": f"Use Cases {useCaseIds} Added To Space {spaceId}"
            }
        
        except Exception as e:
            logging.error(f"Error while assigning usecase {useCaseIds} for space {spaceId}: {e}")
            return {
                "status_code":status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"{e}"
            }
    
    def unassignUseCase(self, data: dict):
        try:
            expected_keys = {"spaceId", "useCaseIds"}

            if not isinstance(data, dict) or not data.keys() == expected_keys:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. Expected a dictionary with keys 'spaceId' and 'useCaseIds'."
                }
        
            spaceId = data["spaceId"]
            useCaseIds = data["useCaseIds"]

            if not isinstance(useCaseIds, list):
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. 'useCaseIds' must be a list."
                }
        
            if not "superadmin" in self.role:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail":"Unauthorized Access",
                }

            status_code = self.applicationDB.checkSpace(spaceId= spaceId)

            if status_code == 400:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid spaceId. Expected a string."
                }
            
            if status_code == 404:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": f"Space Not Found for spaceId: {spaceId}",
                }
            
            if not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error",
                }
            
            for useCaseId in useCaseIds:
                status_code = self.applicationconfigDB.checkUseCases(useCaseId= useCaseId)

                if status_code == 400:
                    return {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "detail": "Invalid input data. Expected a useCaseId in string."
                    }

                if status_code == 404:
                    return {
                        "status_code": status.HTTP_404_NOT_FOUND,
                        "detail": f"UseCase Not Found for useCaseId {useCaseId}",
                    }
                
                if not status_code == 200:
                    return {
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "detail": "Internal server error",
                    }
                
                status_code, hierarchyIds = self.applicationDB.getHierarchyIds(spaceId= spaceId, useCaseId= useCaseId)

                if status_code == 400:
                    return {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "detail": "Invalid input data. Expected spaceId and useCaseId in form of string"
                    }
                
                if status_code == 404:
                    logger.info(f"No Hierarchy Founnd for spaceId {spaceId} with useCaseId {useCaseId}")
                     
                if status_code == 500:
                    return {
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "detail": "Internal Server Error"
                    }

                if status_code == 200:
                    status_code = self.userDB.removeHierarchyRole(hierarchyIds= hierarchyIds)

                    if status_code == 400:
                        return {
                            "status_code": status.HTTP_400_BAD_REQUEST,
                            "detail": "Invalid input data. Expected hierarchyIds in form of list"
                        }
                    
                    if status_code == 304:
                        logger.info("Hierarchy Role not removed from users")
                    
                    if status_code == 500:
                        return {
                            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                            "detail": "Internal Server Error"
                        }
                    
                    for hierarchyId in hierarchyIds:
                        status_code = self.applicationDB.checkHierarchy(hierarchyId= hierarchyId)

                        if status_code == 400:
                            return {
                                "status_code": status.HTTP_400_BAD_REQUEST,
                                "detail": "Invalid hierarchyId. Expected a string."
                            }
                        
                        if status_code == 404:
                            return {
                                "status_code": status.HTTP_404_NOT_FOUND,
                                "detail": f"HierarchyID {hierarchyId} Not Found",
                            }
                        
                        if not status_code == 200:
                            return {
                                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                                "detail": "Internal server error",
                            }
                        
                        hierarchyDB = initilizeHierarchyDB(hierarchyId= hierarchyId)
                        status_code= hierarchyDB.removeHierarchyDB()

                    status_code = self.applicationDB.removeHierarchys(hierarchyIds= hierarchyIds)

                    if status_code == 400:
                        return {
                            "status_code": status.HTTP_400_BAD_REQUEST,
                            "detail": "Invalid input. Expected a list of hierarchyIds."
                        }
                    
                    if status_code == 404:
                        return {
                            "status_code": status.HTTP_404_NOT_FOUND,
                            "detail": "No hierarchies found to remove."
                        }
                    
                    if status_code == 500:
                        return {
                                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                                "detail": "Internal server error",
                            }

                status_code = self.applicationDB.removeUseCase(spaceId= spaceId, useCaseId= useCaseId)

                if status_code == 400:
                    return {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "detail": "Invalid input. Expected strings for spaceId and useCaseId."
                    }
                
                if status_code == 404:
                    return {
                        "status_code": status.HTTP_404_NOT_FOUND,
                        "detail": f"Use case {useCaseId} not found in space {spaceId}."
                    }

                if status_code == 500:
                    return {
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "detail": "Internal server error occurred."
                    }
            
            return {
                "status_code": status.HTTP_200_OK,
                "detail": f"Use Cases {useCaseIds} Removed From Space {spaceId} Successfully"
            }
        except Exception as e:
            logging.error(f"Error while removing usecases {useCaseIds} from space Id {spaceId}: {e}")
            return {
                "status_code":status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"{e}"
            }
        
    def deleteSpaces(self, data: list):
        try:
            if not isinstance(data, list):
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. Expected a dictionary with keys 'spaceId' and 'useCaseIds'."
                }

            spaceIds = data

            if not "superadmin" in self.role:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail":"Unauthorized Access",
                }
            
            for spaceId in spaceIds:
                status_code = self.applicationDB.checkSpace(spaceId= spaceId)

                if status_code == 400:
                    return {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "detail": "Invalid spaceId. Expected a string."
                    }
                
                if status_code == 404:
                    return {
                        "status_code": status.HTTP_404_NOT_FOUND,
                        "detail": f"Space Not Found for spaceId: {spaceId}",
                    }
                
                if not status_code == 200:
                    return {
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "detail": "Internal server error",
                    }
                
                status_code, hierarchyIds = self.applicationDB.getSpaceHiearchyIds(spaceId= spaceId)

                if status_code == 200:
                    status_code = self.userDB.removeHierarchyRole(hierarchyIds= hierarchyIds)
                    if status_code == 304:
                        logger.info("No Hierarchy Roles for User to remove")
                    
                    if not status_code == 200:
                        return {
                            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                            "detail": "Internal Server Error"
                        }
                    
                    for hierarchyId in hierarchyIds:
                        hierarchyDB = initilizeHierarchyDB(hierarchyId= hierarchyId)
                        status_code= hierarchyDB.removeHierarchyDB()

                    status_code = self.applicationDB.removeHierarchys(hierarchyIds= hierarchyIds)
                    if status_code == 304:
                        logger.info("No Hierarchys Found To Delete")
                    
                    if not status_code == 200:
                        return {
                            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                            "detail": "Internal Server Error"
                        }

                status_code = self.userDB.removeSpaceRole(spaceId= spaceId)

                status_code = self.applicationDB.removeSpace(spaceId= spaceId)
            if not status_code == 200:
                return HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error occurred."
                    )
            return {
                "status_code": status.HTTP_200_OK,
                "detail": "Spaces Removed Successfully"
            }
        except Exception as e:
            logging.error(f"Error while removing spaces: {e}")
            return {
                "status_code":status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"{e}"
            }
    
    def updateSpaceName(self, data: dict):
        try:
            spaceName = data["spaceName"]
            spaceId = data["spaceId"]
            if not "superadmin" in self.role:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail":"Unauthorized Access",
                }
            status_code = self.applicationDB.checkSpace(spaceId= spaceId)
            if status_code == 400:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid spaceId. Expected a string."
                }
            
            if status_code == 404:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": f"Space Not Found for spaceId: {spaceId}",
                }
            
            if not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error",
                }
            status_code = self.applicationDB.updateSpaceName(spaceId= spaceId, spaceName= spaceName)
            if not status_code == 200:
                return HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error occurred."
                    )
            return {
                "status_code": status.HTTP_200_OK,
                "detail": "Spaces Name Updated Successfully"
            }
        except Exception as e:
            logging.error(f"Error while updating space name: {e}")
            return {
                "status_code":status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"{e}"
            }



    
