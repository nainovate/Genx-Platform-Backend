import os
import logging
import yaml
from fastapi import  HTTPException, status
from Database.applicationDataBase import ApplicationDataBase
from Database.organizationDataBase import *
import random
import string


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
    
def initilizeApplicationDB():
    applicationDB = ApplicationDataBase()
    return applicationDB

def generate_space_id():
    space_id = "".join(random.choice(string.ascii_lowercase) for _ in range(4))
    return space_id 

class Spaces:
    def __init__(self, userId: str, role: dict, orgIds: list):
        self.role = role
        self.userId = userId
        self.orgIds = orgIds
        self.applicationDB = initilizeApplicationDB()

    def createSpace(self, data: dict):
        try:
            if not isinstance(data, dict) or "spaceName" not in data or "orgIds" not in data or len(data) != 2:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. Expected a dictionary with 'spaceName' and 'orgIds' keys."
                }

            # Check if user has the right role to create a space
            if "admin" not in self.role:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail": "Unauthorized Access"
                }

            spaceName = data["spaceName"]
            orgIds = data["orgIds"]
            # Ensure the organization ID is valid for the user
            for orgId in orgIds:
                if orgId not in self.orgIds:
                    return {
                        "status_code": status.HTTP_401_UNAUTHORIZED,
                        "detail": "Unauthorized Access"
                    }

                # Initialize the organization database
                organizationDB = OrganizationDataBase(orgId)
                
                # Check if organizationDB is initialized successfully
                if organizationDB.status_code != 200:
                    return {
                        "status_code": organizationDB.status_code,
                        "detail": "Error initializing the organization database"
                    }


                status_code = organizationDB.createSpace(spaceName=spaceName, userId=self.userId)

                # Handle space creation statuses
                if status_code == status.HTTP_400_BAD_REQUEST:
                    return {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "detail": "Invalid input data types. Expected strings for spaceName, spaceId, and userId."
                    }

                if status_code == status.HTTP_409_CONFLICT:
                    return {
                        "status_code": status.HTTP_409_CONFLICT,
                        "detail": "Space Name Already Exists"
                    }
                
            # Return final status
            if status_code == status.HTTP_200_OK:
                return {
                    "status_code": status.HTTP_200_OK,
                    "detail": "Space Created Successfully"
                }

            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": "Internal server error occurred."
            }
        except Exception as e:
            logging.error(f"Error while creating space: {e}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": str(e)
            }
        
    def getSpacesInOrg(self, data):
        try:
            # if not "admin" in self.role:
            #     return {
            #         "status_code": status.HTTP_401_UNAUTHORIZED,
            #         "detail": "Unauthorized Access",
            #     }
            orgId = data['orgId']
            if not orgId in self.orgIds:
                return {
                        "status_code": status.HTTP_401_UNAUTHORIZED,
                        "detail": "Unauthorized Access"
                }
            organizationDB = OrganizationDataBase(orgId)
            spaces, status_code = organizationDB.getSpaceInOrg(self.role,self.userId,orgId=orgId)

            if status_code == status.HTTP_404_NOT_FOUND:
                return {
                        "status_code": status.HTTP_404_NOT_FOUND, 
                        "detail": "No spaces found in organization database."
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
    
    def getAdminAllSpaces(self):
        try:
            if not "admin" in self.role:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail": "Unauthorized Access",
                }
            orgIds = self.orgIds
            spaces_data = []
            for orgId in orgIds:
                applicationDB = ApplicationDataBase()
                org_list,status_code = applicationDB.getOrgInfo(orgId=orgId)
                spaceInfo= org_list
                organizationDB = OrganizationDataBase(orgId)
                spaces, status_code = organizationDB.getSpaceInOrg(self.role, self.userId, orgId=orgId)
                spaceInfo["spaces"] = spaces
                spaces_data.append(spaceInfo)

            
            if len(spaces_data) == 0:
                return {
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "detail": "Internal server error occurred."
                }

            return {
                "status_code": status_code,
                "spaces": spaces_data
            }
        
        except Exception as e:
            logging.error(f"Error while retrieving spaces: {e}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"{e}"
            } 

    def assignSpace(self, data: dict):
        try:
            expected_keys = {"orgId", "spaceId", "userIds"}
            if not isinstance(data, dict) or not data.keys() == expected_keys:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. Expected a dictionary with keys 'orgId', 'spaceId' and 'userIds'."
                }
        
            spaceId = data["spaceId"]
            userIds = data["userIds"]
            orgId = data["orgId"]
            if orgId not in self.orgIds:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail":"Unauthorized Access",
                }

            if not isinstance(userIds, list):
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. 'userIds' must be a list."
                }
        
            if not "admin" in self.role:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail":"Unauthorized Access",
                }
            
            organizationDB = OrganizationDataBase(orgId)
            status_code = organizationDB.checkSpace(spaceId = spaceId)
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
     
                status_code = self.applicationDB.assignSpace(orgId = orgId, userId= userId, spaceId= spaceId)

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
                
                if status_code == 409:
                    return {
                        "status_code": status.HTTP_409_CONFLICT,
                        "detail": "Space Already Assigned To User",
                    }
                
                if status_code == 401:
                    return {
                        "status_code": status.HTTP_401_UNAUTHORIZED,
                        "detail": "User is not in Org",
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
            expected_keys = {"orgId", "spaceId", "userIds"}
            if not isinstance(data, dict) or not data.keys() == expected_keys:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. Expected a dictionary with keys 'spaceId' and 'userIds'."
                }
        
            spaceId = data["spaceId"]
            userIds = data["userIds"]
            orgId = data["orgId"]

            if orgId not in self.orgIds:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail":"Unauthorized Access",
                }

            if not isinstance(userIds, list):
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. 'userIds' must be a list."
                }
        
            if not "admin" in self.role:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail":"Unauthorized Access",
                }
            
            organizationDB = OrganizationDataBase(orgId)
            status_code = organizationDB.checkSpace(spaceId = spaceId)
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
            
            if status_code == 409:
                    return {
                        "status_code": status.HTTP_409_CONFLICT,
                        "detail": "Space Already Assigned To User",
                    }
            
            if not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error",
                }
            
            
            for userId in userIds:
     
                status_code = self.applicationDB.unassignSpace(orgId = orgId, userId= userId, spaceId= spaceId)

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
                
                if status_code == 409:
                    return {
                        "status_code": status.HTTP_409_CONFLICT,
                        "detail": "Space Already unssigned To User",
                    }
                
                if not status_code == 200:
                    return {
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "detail": "Internal server error",
                    }
                
            return {
                "status_code": status_code,
                "detail": f"Space {spaceId} unassigned to user {userId} successfully."
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
                spaceName, status_code = self.organizationDB.getSpaceName(spaceId = space)

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


    def getSpaceId(self, hierarchyId: str):
        try:
            if not isinstance(hierarchyId, str):
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid hierarchyId. Expected a string."
                }
            
            status_code = self.organizationDB.checkHierarchy(hierarchyId= hierarchyId)

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
            
            spaceId, status_code = self.organizationDB.getSpaceId(hierarchyId= hierarchyId)

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
            
            status_code = self.organizationDB.checkSpace(spaceId= spaceId)

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
            
            unassignedUseCases, status_code = self.organizationDB.getUnassignedUseCases(spaceId= spaceId, configInstance= self.organizationconfigDB)

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
            
            status_code = self.organizationDB.checkSpace(spaceId= spaceId)

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
            
            assignedUseCases, status_code = self.organizationDB.getAssignedUseCases(spaceId= spaceId, configInstance= self.organizationconfigDB)
            
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
            
            status_code = self.organizationDB.checkSpace(spaceId= spaceId)

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
                status_code = self.organizationconfigDB.checkUseCases(useCaseId= useCaseId)

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

            status_code = self.organizationDB.assignUseCase(spaceId= spaceId, useCaseIds= useCaseIds)

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
    
    '''def unassignUseCase(self, data: dict):
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

            status_code = self.organizationDB.checkSpace(spaceId= spaceId)

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
                status_code = self.organizationconfigDB.checkUseCases(useCaseId= useCaseId)

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
                
                status_code, hierarchyIds = self.organizationDB.getHierarchyIds(spaceId= spaceId, useCaseId= useCaseId)

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
                        status_code = self.organizationDB.checkHierarchy(hierarchyId= hierarchyId)

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

                    status_code = self.organizationDB.removeHierarchys(hierarchyIds= hierarchyIds)

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

                status_code = self.organizationDB.removeUseCase(spaceId= spaceId, useCaseId= useCaseId)

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
                status_code = self.organizationDB.checkSpace(spaceId= spaceId)

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
                
                status_code, hierarchyIds = self.organizationDB.getSpaceHiearchyIds(spaceId= spaceId)

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

                    status_code = self.organizationDB.removeHierarchys(hierarchyIds= hierarchyIds)
                    if status_code == 304:
                        logger.info("No Hierarchys Found To Delete")
                    
                    if not status_code == 200:
                        return {
                            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                            "detail": "Internal Server Error"
                        }

                status_code = self.userDB.removeSpaceRole(spaceId= spaceId)

                status_code = self.organizationDB.removeSpace(spaceId= spaceId)
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
            }'''
    
    def updateSpaceName(self, data: dict):
        try:
            spaceName = data["spaceName"]
            spaceId = data["spaceId"]
            orgId = data["orgId"]
            if not orgId in self.orgIds:
                return {
                        "status_code": status.HTTP_401_UNAUTHORIZED,
                        "detail": "Unauthorized Access"
                }
            if not "admin" in self.role:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail":"Unauthorized Access",
                }
             # Initialize the organization database
            organizationDB = OrganizationDataBase(orgId)
            status_code = organizationDB.checkSpace(spaceId= spaceId)
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
            status_code = organizationDB.updateSpaceName(spaceId= spaceId, spaceName= spaceName)
            if status_code == status.HTTP_409_CONFLICT:
                return {
                        "status_code": status.HTTP_409_CONFLICT,
                        "detail": "Space Name Already Exists, Try new Space name"
                }
                
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
        
    def removeSpace(self, data: dict):
        try:
            if not "admin" in self.role:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail":"Unauthorized Access",
                }
            spaceId = data['spaceId'] 
            orgId = data['orgId']   
            if not orgId in self.orgIds:
                return {
                        "status_code": status.HTTP_401_UNAUTHORIZED,
                        "detail": "Unauthorized Access"
                }   
             # Initialize the organization database
            organizationDB = OrganizationDataBase(orgId)
            status_code = organizationDB.checkSpace(spaceId)
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
            status_code = organizationDB.removeSpace(spaceId)
            if status_code == 422:
                return {
                    "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                    "detail": f"Space Not Found for spaceId: {spaceId}",
                }
            
            if not status_code == 200:
                return HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error occurred."
                    )
            return {
                "status_code": status.HTTP_200_OK,
                "detail": "Space removed Successfully"
            }
        except Exception as e:
            logging.error(f"Error while updating Org name: {e}")
            return {
                "status_code":status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"{e}"
            } 


    def getUsersInOrg(self, data):
        try:
            if not "admin" in self.role and not "analyst" in self.role:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail": "Unauthorized Access",
                }
            
            # Check if the organization exists before fetching users
            org_status = self.applicationDB.checkOrg(data["orgId"])
            if org_status == status.HTTP_404_NOT_FOUND:
                logging.warning(f"Organization with orgId {data['orgId']} not found.")
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "Organization not found."
                }
            elif org_status != status.HTTP_200_OK:
                logging.error(f"Error checking organization with orgId {data['orgId']}.")
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Error validating organization."
                }

            # Proceed with fetching users if organization exists
            status_code, users = self.applicationDB.getUsersInOrg(data["orgId"], self.role)

            if status_code == status.HTTP_404_NOT_FOUND:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND, 
                    "detail": "No users found for Org."
                }
            
            if status_code != 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error occurred."
                }

            return {
                "status_code": status_code,
                "users_list": users
            }

        except Exception as e:
            logging.error(f"Error while retrieving Users: {e}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"{e}"
            }
 
    
    
    def getAllUsers(self):
        try:
            # if not "admin" in self.role:
            #     return {
            #         "status_code": status.HTTP_401_UNAUTHORIZED,
            #         "detail": "Unauthorized Access",
            #     }
            
            status_code, users = self.applicationDB.getAllUsers(self.role)

            if status_code == status.HTTP_404_NOT_FOUND:
                return {
                        "status_code": status.HTTP_404_NOT_FOUND, 
                        "detail": "No users found."
                }
            
            elif not status_code == 200:
                return {
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "detail": "Internal server error occurred."
                }

            return {
                "status_code": status_code,
                "users_list": users
            }
        
        except Exception as e:
            logging.error(f"Error while retrieving All Users: {e}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"{e}"
            } 

    def getAllAnalystsInOrg(self, data):
        try:
            if not "admin" in self.role:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail": "Unauthorized Access",
                }
            status_code, analysts = self.applicationDB.getAnalystsInOrg( data["orgId"])
            if status_code == status.HTTP_404_NOT_FOUND:
                return {
                        "status_code": status.HTTP_404_NOT_FOUND, 
                        "detail": "No Analysts found for Space."
                }
            
            if not status_code == 200:
                return {
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "detail": "Internal server error occurred."
                }
            return {
                "status_code": status_code,
                "analysts_list": analysts
            }
        
        except Exception as e:
            logging.error(f"Error while retrieving analysts: {e}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"{e}"
            }       



    
