import logging
import random
import string

from fastapi import HTTPException
from Database.applicationSetup import *
from Database.applicationDataBase import *

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

def generate_org_id():
    org_id = "".join(random.choice(string.ascii_lowercase) for _ in range(4))
    return org_id 

class Organization:
    def __init__(self, userId: str, role: dict):
        self.role = role
        self.userId = userId
        self.applicationDB = initilizeApplicationDB()

    def createOrganization(self, data: dict):
        try:                 
            if not isinstance(data, dict):
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. Expected a dictionary with only 'orgName' key."
                }

            if not "superadmin" in self.role:
                return {
                        "status_code": status.HTTP_401_UNAUTHORIZED,
                        "detail": "Unauthorized Access"
                }
            data["orgId"] = generate_org_id()
            status_code = self.applicationDB.createOrganization(data, self.userId)

            if status_code == 400:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data types. Expected strings for orgName, orgId, userId."
                }
            
            if status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
                while status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
                    data['orgId'] = generate_org_id()
                    status_code = self.applicationDB.createOrganization(data, userId = self.userId)
                if status_code == 400:
                    return {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "detail": "Invalid input data types. Expected strings for orgName, orgId, userId."
                    }
            
                if status_code == status.HTTP_409_CONFLICT:
                    return {
                            "status_code": status.HTTP_409_CONFLICT,
                            "detail": "Org Name Already Existed"
                    }

            if status_code == status.HTTP_409_CONFLICT:
                return {
                        "status_code": status.HTTP_409_CONFLICT,
                        "detail": "Org Name Already Existed"
                }
            
            elif not status_code == 200:
                return {
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "detail": "Internal server error occurred."
                }     
            return {
                "status_code": 200,
                "detail": "Organization Created Successfully"
            }
        except Exception as e:
            logging.error(f"Error while creating org: {e}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail":f"{e}"
            }

    def updateOrganization(self, data: dict):
        try:
            if not "superadmin" in self.role:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail":"Unauthorized Access",
                }
            status_code = self.applicationDB.checkOrg(data['orgId'])
            if status_code == 400:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid OrgId. Expected a string."
                }
            
            if status_code == 404:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": f"Org Not Found for OrgId: {data['orgId']}",
                }
            
            elif not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error",
                }
            
            status_code = self.applicationDB.updateOrganization(data)
            if status_code == 409:
                return {
                    "status_code": status.HTTP_409_CONFLICT,
                    "detail": "Org name already exists."
                }
            elif not status_code == 200:
                return HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error occurred."
                    )
            return {
                "status_code": status.HTTP_200_OK,
                "detail": "Org Updated Successfully"
            }
        except Exception as e:
            logging.error(f"Error while updating Org name: {e}")
            return {
                "status_code":status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"{e}"
            }
        
    def getOrganizations(self):
        try:
            if not "superadmin" in self.role:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail": "Unauthorized Access",
                }
            
            organizations, status_code = self.applicationDB.getOrganizations()

            if status_code == status.HTTP_404_NOT_FOUND:
                return {
                        "status_code": status.HTTP_404_NOT_FOUND, 
                        "detail": "No Organizations found in application database."
                }
            
            elif not status_code == 200:
                return {
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "detail": "Internal server error occurred."
                }

            return {
                "status_code": status_code,
                "organizations": organizations
            }
        
        except Exception as e:
            logging.error(f"Error while retrieving Organizations: {e}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"{e}"
            }     

    def removeOrganization(self, data: dict):
        try:
            if not "superadmin" in self.role:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail":"Unauthorized Access",
                }
            orgId = data['orgId']       
            status_code = self.applicationDB.checkOrg(orgId)
            if status_code == 400:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid OrgId. Expected a string."
                }
            
            elif status_code == 404:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": f"Org Not Found for OrgId: {orgId}",
                }
            
            elif not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error",
                }
            status_code = self.applicationDB.removeOrganization(orgId)
            if status_code == 422:
                return {
                    "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                    "detail": f"Org Not Found for OrgId: {orgId}",
                }
            
            elif not status_code == 200:
                return HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error occurred."
                    )
            return {
                "status_code": status.HTTP_200_OK,
                "detail": "Org removed Successfully"
            }
        except Exception as e:
            logging.error(f"Error while updating Org name: {e}")
            return {
                "status_code":status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"{e}"
            } 
        
    def assignUsersToOrg(self, data: dict):
        try:
            expected_keys = {"orgId", "userIds"}
            if not isinstance(data, dict) or not data.keys() == expected_keys:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. Expected a dictionary with keys 'userIds' and 'orgId'."
                }
        
            userIds = data["userIds"]
            orgId = data["orgId"]

            if not isinstance(userIds, list):
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. 'adminIds' must be a list."
                }
        
            # if not "superadmin" in self.role:
            #     return {
            #         "status_code": status.HTTP_401_UNAUTHORIZED,
            #         "detail":"Unauthorized Access",
            #     }

            status_code = self.applicationDB.checkOrg(orgId = orgId)
            # status_code = self.applicationDB.checkAdmin(adminId = adminId)

            if status_code == 400:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid orgId. Expected a string."
                }
            
            elif status_code == 404:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": f"Org Not Found for orgId: {orgId}",
                }
            
            elif not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error",
                }
            
            for userId in userIds:
                status_code = self.applicationDB.assignUserToOrg(orgId= orgId, userId= userId, role=self.role)

                if status_code == 400:
                    return {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "detail": "Invalid input data. orgID and userId must be strings."
                    }
                
                elif status_code == 404:
                    return {
                        "status_code": status.HTTP_404_NOT_FOUND,
                        "detail": "User not found."
                    }
                
                elif status_code == 403:
                    return {
                        "status_code": status.HTTP_403_FORBIDDEN,
                        "detail": "User cannot be assigned a org."
                    }
                
                elif status_code == 409:
                    return {
                        "status_code": status.HTTP_409_CONFLICT,
                        "detail": "user Already Assigned To Org",
                    }
                
                elif not status_code == 200:
                    return {
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "detail": "Internal server error",
                    }
                
            return {
                "status_code": status_code,
                "detail": f"users assigned to org {orgId} successfully."
            }
        
        except Exception as e:
            logging.error(f"Error while assigning users for org id {orgId}: {e}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"{e}"
            }
        
    def unassignUsersToOrg(self, data: dict):
        try:
            expected_keys = {"orgId", "userIds"}
            if not isinstance(data, dict) or not data.keys() == expected_keys:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. Expected a dictionary with keys 'userIds' and 'orgId'."
                }
        
            userIds = data["userIds"]
            orgId = data["orgId"]

            if not isinstance(userIds, list):
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. 'userIds' must be a list."
                }
        
            # if not "superadmin" in self.role:
            #     return {
            #         "status_code": status.HTTP_401_UNAUTHORIZED,
            #         "detail":"Unauthorized Access",
            #     }
            status_code = self.applicationDB.checkOrg(orgId = orgId)
            # status_code = self.applicationDB.checkAdmin(adminId = adminId)

            if status_code == 400:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid orgId. Expected a string."
                }
            
            elif status_code == 404:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": f"Org Not Found for orgId: {orgId}",
                }
            
            elif not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error",
                }
            
            for userId in userIds:
                status_code = self.applicationDB.unassignUserToOrg(orgId= orgId, userId= userId, role=self.role)
                if status_code == 400:
                    return {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "detail": "Invalid input data. orgID and userId must be strings."
                    }
                
                elif status_code == 404:
                    return {
                        "status_code": status.HTTP_404_NOT_FOUND,
                        "detail": "User not found."
                    }
                
                elif status_code == 403:
                    return {
                        "status_code": status.HTTP_403_FORBIDDEN,
                        "detail": "User cannot be unassigned from a org."
                    }
                
                elif status_code == 409:
                    return {
                        "status_code": status.HTTP_409_CONFLICT,
                        "detail": "User Already unssigned To Org",
                    }
                
                elif not status_code == 200:
                    return {
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "detail": "Internal server error",
                    }
                
            return {
                "status_code": status_code,
                "detail": f"Users unassigned to org {orgId} successfully."
            }
        
        except Exception as e:
            logging.error(f"Error while unassigning user for org id {orgId}: {e}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"{e}"
            }
        
    def getOrganizationsforUsers(self):
        try:
            # if not "admin" in self.role:
            #     return {
            #         "status_code": status.HTTP_401_UNAUTHORIZED,
            #         "detail": "Unauthorized Access",
            #     }
            
            organizations, status_code = self.applicationDB.getOrganizationsforUsers(self.userId)
            if status_code == status.HTTP_404_NOT_FOUND:
                return {
                        "status_code": status.HTTP_404_NOT_FOUND, 
                        "detail": "No Organizations found in application database."
                }
            
            elif not status_code == 200:
                return {
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "detail": "Internal server error occurred."
                }

            return {
                "status_code": status_code,
                "organizations": organizations
            }
        
        except Exception as e:
            logging.error(f"Error while retrieving Organizations: {e}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"{e}"
            }

    
            
            

            
