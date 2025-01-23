import os
import logging
import yaml
from fastapi import HTTPException,status
from Database.users import *
from Database.applicationDataBase import *
from ApplicationManagment.usecases import UseCases
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

def initilizeHierarchyDB(hierarchyId: str):
    HierarchyDB = HierarchyDataBase(hierarchyId= hierarchyId)
    return HierarchyDB


def generate_hierarchy_id():
    space_id = "".join(random.choice(string.ascii_lowercase) for _ in range(4))
    return space_id 

class Hierarchy:
    def __init__(self, role: dict, userId: str):
        self.role = role
        self.userId = userId
        self.applicationDB = initilizeApplicationDB()
        self.userDB = initilizeUserDB()

    def createHierarchy(self, usecaseInstance: object, data: dict):
        try:
            if not "admin" in self.role:
                return {
                        "status_code": status.HTTP_401_UNAUTHORIZED,
                        "detail": "Unauthorized Access"
                }
            spaceId = data["spaceId"]
            status_code = self.applicationDB.checkSpace(spaceId = spaceId)
            if status_code == 404:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail": "Space Not Found",
                }
            if not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error",
                }
            hierarchyName = data["hierarchyName"]
            useCaseId = data["useCaseId"]
            status_code, useCaseRoles = usecaseInstance.getUseCaseRoles(useCaseId= useCaseId)
            if status_code == 404:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "No use cases roles in application config database."
                }
            if not status_code == 200:
                return{
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error occurred."
                }
            hierarchyId = generate_hierarchy_id()
            status_code = self.applicationDB.createHierarchy(hierarchyName = hierarchyName, hierarchyId = hierarchyId, spaceId = spaceId, useCaseId = useCaseId, userId = self.userId, useCaseRoles = useCaseRoles)

            if status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
                while status_code != status.HTTP_422_UNPROCESSABLE_ENTITY:
                    spaceId = generate_hierarchy_id()
                    status_code = self.applicationDB.createHierarchy(hierarchyName = hierarchyName, hierarchyId = hierarchyId, spaceId = spaceId, useCaseId = useCaseId, userId = self.userId, useCaseRoles = useCaseRoles)
                    if status_code == status.HTTP_409_CONFLICT:
                        return {
                            "status_code": status.HTTP_409_CONFLICT,
                            "detail": "Hierarchy Name Already Existed"
                        }
            if status_code == status.HTTP_409_CONFLICT:
                return {
                    "status_code": status.HTTP_409_CONFLICT,
                    "detail": "Hierarchy Name Already Existed"
                }
            
            if not status_code == 200:
                return{
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error occurred."
                }
            else:
                return {
                    "status_code": status_code,
                    "detail": "Hierarchy Created Successfully"
                }
        except Exception as e:
            logging.error(f"Error while creating Hierarchy: {e}")
            return{
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"{e}"
            }
        
    def getSpaceUseCases(self):
        try:
            if not "admin" in self.role:
                return {
                        "status_code": status.HTTP_401_UNAUTHORIZED,
                        "detail": "Unauthorized Access"
                }
            
            status_code = self.applicationDB.checkSpace(spaceId = self.spaceId)
            if status_code == 404:
                return{
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail": "Space Not Found",
                }
            if not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error",
                }
            spaceUseCases, status_code = self.applicationDB.getSpaceUseCases(spaceId=self.spaceId)
            if status_code == status.HTTP_404_NOT_FOUND:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "No use space use cases found in application database."
                }
            if not status_code == 200:
                return{
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error occurred."
                }
            else:
                return {
                    "status_code": status_code,
                    "spaceUseCases": spaceUseCases
                }
        except Exception as e:
            logging.error(f"Error while retrieving space use cases: {e}")
            return{
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"{e}"
            } 
    
    def assignHierarchy(self, data: dict):
        try:
            hierarchyId = data["hierarchyId"]
            useCaseRole = data["useCaseRole"]
            userIds = data["userIds"]

            if not "admin" in self.role:
                return {
                        "status_code": status.HTTP_401_UNAUTHORIZED,
                        "detail": "Unauthorized Access"
                }
             
            status_code = self.applicationDB.checkHierarchy(hierarchyId= hierarchyId)
            if status_code == 404:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail": "Hierarchy Not Found",
                }
            if not status_code == 200:
                return{
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error",
                }
            
            status_code = self.applicationDB.checkHierarchyRoles(hierarchyId= hierarchyId, useCaseRole= useCaseRole)
            if status_code == 404:
                return{
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail": "Use Case Role  Not Found",
                }
            if not status_code == 200:
                return{
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error",
                }
            
            for userId in userIds:
                status_code = self.userDB.assignUseCaseRole(userId = userId, hierarchyId= hierarchyId, useCaseRole=useCaseRole)
                if status_code == 409:
                    return{
                        "status_code": status.HTTP_409_CONFLICT,
                        "detail": "Hierarchy Already Assigned To User",
                    }
                if status_code == 404:
                    return{
                        "status_code": status.HTTP_401_UNAUTHORIZED,
                        "detail": "Unauthorized Access",
                    }
                if not status_code == 200:
                    return{
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "detail": "Internal server error",
                    }
            return {
                "status_code": status_code,
                "detail": "Hierarchy Assigned Successfully"
            }
        except Exception as e:
            logging.error(f"Error while assigning Hierarchy: {e}")
            return{
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"{e}"
            }
        
    def unassignHierarchy(self, data: dict):
        try:
            hierarchyId = data["hierarchyId"]
            userIds = data["userIds"]

            if not "admin" in self.role:
                return {
                        "status_code": status.HTTP_401_UNAUTHORIZED,
                        "detail": "Unauthorized Access"
                }
            
            status_code = self.applicationDB.checkHierarchy(hierarchyId= hierarchyId)
            if status_code == 404:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail": "Hierarchy Not Found",
                }
            if not status_code == 200:
                return{
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error",
                }
            
            for userId in userIds:
                status_code = self.userDB.unassignUseCaseRole(userId = userId, hierarchyId= hierarchyId)
                if status_code == 409:
                    return{
                        "status_code": status.HTTP_409_CONFLICT,
                        "detail": "Hierarchy Already Unassigned To User",
                    }
                if status_code == 404:
                    return{
                        "status_code": status.HTTP_401_UNAUTHORIZED,
                        "detail": "Unauthorized Access",
                    }
                if not status_code == 200:
                    return{
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "detail": "Internal server error",
                    }
            return {
                "status_code": status_code,
                "detail": "Hierarchy Unassigned Successfully"
            }
        except Exception as e:
            logging.error(f"Error while unassigning Hierarchy: {e}")
            return{
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"{e}"
            }

    def getCreatedHierarchy(self, data: dict):
        try:
            spaceId = data["spaceId"]
            if not "admin" in self.role:
                return {
                        "status_code": status.HTTP_401_UNAUTHORIZED,
                        "detail": "Unauthorized Access"
                }
            
            status_code = self.applicationDB.checkSpace(spaceId = spaceId)
            if status_code == 404:
                return{
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail": "Space Not Found",
                }
            if not status_code == 200:
                return{
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error",
                }
            hierarchys, status_code = self.applicationDB.getCreatedHierarchy(userId= self.userId,spaceId=spaceId)
            if status_code == status.HTTP_404_NOT_FOUND:
                return{
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "No Assigned Hierarchys Found"
                }
            if not status_code == 200:
                return{
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error occurred."
                }
            else:
                return {
                    "status_code": status_code,
                    "hierarchys": hierarchys
                }
        except Exception as e:
            logging.error(f"Error while retrieving space assigned hierarchys: {e}")
            return{
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"{e}"
            }

    def getHierarchyRoles(self, data: dict):
        try:
            hierarchyId = data["hierarchyId"]
            if not "admin" in self.role:
                return {
                        "status_code": status.HTTP_401_UNAUTHORIZED,
                        "detail": "Unauthorized Access"
                }
            
            status_code = self.applicationDB.checkHierarchy(hierarchyId = hierarchyId)
            if status_code == 404:
                return{
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail": "hierarchy Not Found",
                }
            if not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error",
                }
            hierarchyRoles, status_code = self.applicationDB.getHierarchyRoles(hierarchyId=hierarchyId)
            if status_code == status.HTTP_404_NOT_FOUND:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "No Hierarchy Roles Found"
                }
            if not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR, 
                    "detail": "Internal server error occurred."
                }
            else:
                return {
                    "status_code": status_code,
                    "hierarchyRoles": hierarchyRoles
                }
        except Exception as e:
            logging.error(f"Error while retrieving hierarchy roles: {e}")
            return{
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"{e}"
            }
    
    def getHierarchyAndSpaceNames(self, hierarchyIds: list):
        try:
            if not "user" in self.role:
                return {
                        "status_code": status.HTTP_401_UNAUTHORIZED,
                        "detail": "Unauthorized Access"
                }
            
            hierarchy_space_names, status_code = self.applicationDB.getHierarchyAndSpaceNames(hierarchyIds= hierarchyIds)
            if status_code == status.HTTP_404_NOT_FOUND:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "No Hierarchy Found"
                }
            if not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR, 
                    "detail": "Internal server error occurred."
                }
            else:
                return {
                    "status_code": status_code,
                    "hierarchy_space_names": hierarchy_space_names
                }
        except Exception as e:
            logging.error(f"Error while retrieving hierarchy names: {e}")
            return{
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"{e}"
            }

    def getUseCaseId(self, hierarchyId: str):
        try:
            if "user" not in self.role and "admin" not in self.role:
                return {
                        "status_code": status.HTTP_401_UNAUTHORIZED,
                        "detail": "Unauthorized Access"
                }
            status_code = self.applicationDB.checkHierarchy(hierarchyId = hierarchyId)
            if status_code == 404:
                return{
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail": "hierarchy Not Found",
                }
            if not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error",
                }
            useCaseId, status_code = self.applicationDB.getUseCaseId(hierarchyId= hierarchyId)
            if status_code == status.HTTP_404_NOT_FOUND:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "No Use Case Found"
                }
            if not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR, 
                    "detail": "Internal server error occurred."
                }
            else:
                return {
                    "status_code": status_code,
                    "useCaseId": useCaseId
                }
        except Exception as e:
            logging.error(f"Error while retrieving usecase id: {e}")
            return{
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"{e}"
            }
    
    def getHierarchyDetails(self):
        try:
            if not "admin" in self.role:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail": "Unauthorized Access",
                }
            hierarchyDetails, status_code = self.applicationDB.getHierarchyDetails(userId= self.userId)
            if status_code == status.HTTP_404_NOT_FOUND:
                return {
                        "status_code": status.HTTP_404_NOT_FOUND, 
                        "detail": "No hierarchys found in application database."
                }
            if not status_code == 200:
                return {
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "detail": "Internal server error occurred."
                }
            else:
                return {
                    "status_code": status_code,
                    "hierarchyDetails": hierarchyDetails
                }
        except Exception as e:
            logging.error(f"Error while retrieving hierarchyDetails: {e}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"{e}"
            }
        
    def deleteHierarchy(self, data: list):
        try:
            hierarchyIds = data

            if not "admin" in self.role:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail":"Unauthorized Access",
                }
            
            for hierarchyId in hierarchyIds:
                status_code = self.applicationDB.checkHierarchy(hierarchyId= hierarchyId)

                if status_code == 404:
                    return {
                        "status_code": status.HTTP_401_UNAUTHORIZED,
                        "detail": f"HierarchyId Id {hierarchyId} Not Found",
                    }
                
                if not status_code == 200:
                    return {
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "detail": "Internal server error",
                    }

            status_code = self.userDB.removeHierarchyRole(hierarchyIds= hierarchyIds)
            for hierarchyId in hierarchyIds:
                hierarchyDB = initilizeHierarchyDB(hierarchyId= hierarchyId)
                status_code= hierarchyDB.removeHierarchyDB()
            status_code = self.applicationDB.removeHierarchys(hierarchyIds= hierarchyIds)

            if not status_code == 200:
                return HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error occurred."
                    )
            return {
                "status_code": status.HTTP_200_OK,
                "detail": "Hierarchies Removed Successfully"
            }
        except Exception as e:
            logging.error(f"Error while removing spaces: {e}")
            return {
                "status_code":status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"{e}"
            }
    
    def updateHierarchyName(self, data: dict):
        try:
            hierarchyName = data["hierarchyName"]
            hierarchyId = data["hierarchyId"]

            if not "admin" in self.role:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail":"Unauthorized Access",
                }
            
            status_code = self.applicationDB.checkHierarchy(hierarchyId= hierarchyId)

            if status_code == 404:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail": f"Hierarchy Id {hierarchyId} Not Found",
                }
            
            if not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error",
                }
            
            status_code = self.applicationDB.updateHierarchyName(hierarchyId= hierarchyId, hierarchyName= hierarchyName)

            if not status_code == 200:
                return HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error occurred."
                    )
            
            return {
                "status_code": status.HTTP_200_OK,
                "detail": "Hierarchy Name Updated Successfully"
            }
        except Exception as e:
            logging.error(f"Error while updating hierarchy name: {e}")
            return {
                "status_code":status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"{e}"
            }
    
    def addHierarchyConfig(self, hierarchyId: str, data: dict):
        try:
            if not "admin" in self.role:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail":"Unauthorized Access",
                }
            
            status_code = self.applicationDB.checkHierarchy(hierarchyId= hierarchyId)

            if status_code == 404:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail": f"Hierarchy Id {hierarchyId} Not Found",
                }
            
            if not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error",
                }
            
            hierarchyDB = initilizeHierarchyDB(hierarchyId= hierarchyId)
            status_code = hierarchyDB.addHierarchyConfig(data= data)

            if not status_code == 200:
                return HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error occurred."
                    )
            
            return {
                "status_code": status.HTTP_200_OK,
                "detail": "Hierarchy Config Added Successfully"
            }
        except Exception as e:
            logging.error(f"Error while updating hierarchy name: {e}")
            return {
                "status_code":status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"{e}"
            }