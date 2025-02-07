import os
import logging
import yaml
from fastapi import HTTPException,status
from Database.applicationDataBase import *
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


def generate_role_id():
    role_id = "".join(random.choice(string.ascii_lowercase) for _ in range(4))
    return role_id 

class Role:
    def __init__(self, role: dict, userId: str, orgIds: list, spaceIds:dict):
        self.role = role
        self.orgIds = orgIds
        self.spaceIds = spaceIds
        self.userId = userId
        self.applicationDB = initilizeApplicationDB()

    def createRole(self, data: dict):
        try:
            if not isinstance(data, dict) or "spaceIds" not in data or "orgId" not in data or "roleName"  not in data or "description" not in data:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. Expected a dictionary with 'RoleName' and 'orgId' keys."
                }
            if len(data["spaceIds"]) == 0 or data["orgId"]==''or data["roleName"]=='':
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data."
                }
            # Check if user has the right role to create a space
            if "analyst" not in self.role:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail": "Unauthorized Access"
                }
            roleInfo = {"roleName":data["roleName"], "description":data["description"]}
            spaceIds = data['spaceIds']
            orgId = data["orgId"]
            # Ensure the organization ID is valid for the user
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

            # Create the space in the organization database
            status_code = organizationDB.createRole(roleInfo=roleInfo, spaceIds=spaceIds, userId=self.userId)

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
                    "detail": "Role Created Successfully"
                }

            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": "Internal server error occurred."
            }
        except Exception as e:
            logging.error(f"Error while creating Role: {e}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": str(e)
            }
    
    def getAnalystSpaces(self):
        try:
            if not "analyst" in self.role:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail": "Unauthorized Access",
                }
            spaceIds = self.spaceIds
            roles_data = []
            for orgId,spaceIds in spaceIds.items():
                applicationDB = ApplicationDataBase()
                org_list,status = applicationDB.getOrgInfo(orgId=orgId)
                spaceInfo= org_list
                spaces=[]
                for spaceId in spaceIds:
                    organizationDB = OrganizationDataBase(orgId)
                    space, status_code = organizationDB.getSpaceInfo(spaceId=spaceId)
                    spaces.append(space)
                spaceInfo["spaces"] = spaces
                roles_data.append(spaceInfo)

            if len(roles_data) == 0:
                return {
                        "status_code": status.HTTP_404_NOT_FOUND,
                        "detail": "No spaces found for the Analyst."
                }

            return {
                "status_code": status_code,
                "spaces": roles_data
            }
        except Exception as e:
            logging.error(f"Error while retrieving spaces: {e}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"{e}"
            }

    def getRolesInspace(self, data):
        try:
            # if not "admin" in self.role:
            #     return {
            #         "status_code": status.HTTP_401_UNAUTHORIZED,
            #         "detail": "Unauthorized Access",
            #     }
            orgId = data['orgId']
            spaceId = data["spaceId"]
            if not orgId in self.orgIds:
                return {
                        "status_code": status.HTTP_401_UNAUTHORIZED,
                        "detail": "Unauthorized Access"
                }
            organizationDB = OrganizationDataBase(orgId)
            roles, status_code = organizationDB.getRolesInSpace(self.role, spaceId)

            if status_code == status.HTTP_404_NOT_FOUND:
                return {
                        "status_code": status.HTTP_404_NOT_FOUND, 
                        "detail": "No roles found in organization database."
                }
            
            if not status_code == 200:
                return {
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "detail": "Internal server error occurred."
                }

            return {
                "status_code": status_code,
                "roles": roles
            }
        except Exception as e:
            logging.error(f"Error while creating Role: {e}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": str(e)
            }

    def updateRole(self, data: dict):
        try:
            if not "analyst" in self.role:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail":"Unauthorized Access",
                }
            orgId = data["orgId"]
            spaceId = data["roleId"]
            if orgId == '' or spaceId=='':
                return {
                    "status_code": 422,
                    "detail":" OrgId and RoleId cannot be empty",
                }
            if not orgId in self.orgIds:
                return {
                        "status_code": status.HTTP_401_UNAUTHORIZED,
                        "detail": "Unauthorized Access"
                }
             # Initialize the organization database
            organizationDB = OrganizationDataBase(orgId)
            status_code = organizationDB.checkRole(roleId= data["roleId"])
            if status_code == 400:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid spaceId. Expected a string."
                }
            
            if status_code == 404:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": f"Role Not Found for roleId: {data['roleId']}",
                }
            
            if not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error",
                }
            data.pop("orgId")
            status_code = organizationDB.updateRole(data)
            if status_code == status.HTTP_409_CONFLICT:
                return {
                        "status_code": status.HTTP_409_CONFLICT,
                        "detail": "Role Name Already Exists, Try new Role name"
                }
                
            if not status_code == 200:
                return {
                        status_code:status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "detail":"Internal server error occurred."
                    }
            return {
                "status_code": status.HTTP_200_OK,
                "detail": "Role Details Updated Successfully"
            }
        except Exception as e:
            logging.error(f"Error while updating Role Details: {e}")
            return {
                "status_code":status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"{e}"
            }
        
    def removeRole(self, data: dict):
        try:
            if not "analyst" in self.role:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail":"Unauthorized Access",
                }
            roleId = data['roleId'] 
            orgId = data['orgId'] 
              
            if roleId == '' or orgId=='':
                return {
                    "status_code": 422,
                    "detail":" OrgId and RoleId cannot be empty",
                }
            
            if not orgId in self.orgIds:
                return {
                        "status_code": status.HTTP_401_UNAUTHORIZED,
                        "detail": "Unauthorized Access"
                }   
             # Initialize the organization database
            organizationDB = OrganizationDataBase(orgId)
            status_code = organizationDB.checkRole(roleId)
            if status_code == 400:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid spaceId. Expected a string."
                }
            
            if status_code == 404:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": f"Role Not Found for roleId: {roleId}",
                }
            
            if not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error",
                }
            status_code = organizationDB.removeRole(roleId)
            if status_code == 422:
                return {
                    "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                    "detail": f"Role Not Found for roleId: {roleId}",
                }
            
            if not status_code == 200:
                return HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error occurred."
                    )
            return {
                "status_code": status.HTTP_200_OK,
                "detail": "Role removed Successfully"
            }
        except Exception as e:
            logging.error(f"Error while Deleting Role.: {e}")
            return {
                "status_code":status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"{e}"
            }


    def getAnalystRoles(self):
        try:
            if not "analyst" in self.role:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail": "Unauthorized Access",
                }
            spaceids = self.spaceIds
            roles_data = []
            for orgId,spaceIds in spaceids.items():
                applicationDB = ApplicationDataBase()
                org_list,status = applicationDB.getOrgInfo(orgId=orgId)
                roleInfo= org_list
                spaces=[]
                for spaceId in spaceIds:
                    organizationDB = OrganizationDataBase(orgId)
                    space, status_code = organizationDB.getSpaceInfo(spaceId=spaceId)
                    roles, status_code = organizationDB.getRolesInfo(spaceId=space.get("spaceId"))
                    space["roles"] = roles
                    spaces.append(space)
                roleInfo["spaces"] = spaces
                roles_data.append(roleInfo)
            if len(roles_data) == 0:
                return {
                        "status_code": status.HTTP_404_NOT_FOUND,
                        "detail": "No spaces found for the Analyst."
                }
            return {
                "status_code": 200,
                "roles": roles_data
            }
        except Exception as e:
            logging.error(f"Error while retrieving spaces: {e}")
            return {
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
        
    '''def deleteHierarchy(self, data: list):
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
            }'''
    
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
    
    '''def addHierarchyConfig(self, hierarchyId: str, data: dict):
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
            }'''
    
    
    def unassignRole(self, data: dict):
        try:
            expected_keys = {"orgId", "spaceId", "userIds", "roleId"}

            # Validate input data type and required fields
            if not isinstance(data, dict) or set(data.keys()) != expected_keys:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. Expected a dictionary with keys 'orgId', 'spaceId', 'userIds', and 'roleId'."
                }

            orgId = data.get("orgId", "").strip()
            spaceId = data.get("spaceId", "").strip()
            roleId = data.get("roleId", "").strip()
            userIds = data.get("userIds")

            # Ensure orgId, spaceId, and roleId are non-empty strings
            if not all(isinstance(value, str) and value for value in [orgId, spaceId, roleId]):
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "orgId, spaceId, and roleId must be non-empty strings."
                }

            # Ensure userIds is a non-empty list of valid strings
            if not isinstance(userIds, list) or not userIds or not all(isinstance(userId, str) and userId.strip() for userId in userIds):
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "userIds must be a non-empty list of valid strings."
                }

            # Check if the orgId is authorized
            if orgId not in self.orgIds:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail": "Unauthorized access to the specified orgId."
                }

            # Ensure only analysts can perform this action
            if "analyst" not in self.role:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail": "Unauthorized Access. Only analysts can unassign roles."
                }

            # Iterate over the userIds and unassign the role
            for userId in userIds:
                status_code = self.applicationDB.unassignRole(orgId=orgId, userId=userId.strip(), spaceId=spaceId, roleId=roleId)

                if status_code["status_code"] != 200:
                    return status_code

            return {
                "status_code": status.HTTP_200_OK,
                "detail": f"Role {roleId} successfully unassigned from users in space {spaceId}."
            }

        except Exception as e:
            logging.error(f"Error while unassigning role: {e}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"Internal server error: {e}"
            }




    def getUsersByRole(self, data: dict):
        try:
            expected_keys = {"orgId", "spaceId", "roleId"}
            
            # Validate input data type and required fields
            if not isinstance(data, dict) or set(data.keys()) != expected_keys:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. Expected a dictionary with keys 'orgId', 'spaceId', and 'roleId'."
                }

            orgId = data.get("orgId")
            spaceId = data.get("spaceId")
            roleId = data.get("roleId")

            if not all(isinstance(value, str) and value.strip() for value in [orgId, spaceId, roleId]):
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "orgId, spaceId, and roleId must be non-empty strings."
                }

            # Ensure only Analysts can fetch users
            if "analyst" not in self.role:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail": "Unauthorized Access. Only Analysts can fetch users by role."
                }

            # Call the database function to get users with the specified role
            users = self.applicationDB.getUsersByRole(orgId=orgId, spaceId=spaceId, roleId=roleId)
            
            return users

        except Exception as e:
            logging.error(f"Error while retrieving users by role: {e}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"Internal server error: {e}"
            }
