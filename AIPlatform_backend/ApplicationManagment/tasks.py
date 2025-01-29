import os
import logging
import yaml
from fastapi import HTTPException,status
from Database.applicationDataBase import *
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


class Task:
    def __init__(self, role: dict, userId: str, orgIds: list):
        self.role = role
        self.userId = userId
        self.orgIds = orgIds
        self.applicationDB = initilizeApplicationDB()

    def getRoleTasks(self, data:dict):
        try:
            if not "analyst" in self.role:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail": "Unauthorized Access",
                }
            
            orgId = data.get("orgId")
            roleId = data.get("roleId")

            if not orgId or not roleId:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. orgId and roleId must be provided."
                }

            if not isinstance(roleId, str) and not isinstance(orgId, str):
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid roleId or orgId. Expected a string."
                }

            status_code = self.applicationDB.checkOrg(orgId)
            if status_code == 404:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "Organization not found."
                }
            if not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error",
                }

            if orgId not in self.orgIds:
                return {
                    "status_code": status.HTTP_403_FORBIDDEN,
                    "detail": "You are not authorized to access this resource.",
                }
            
            organizationDB = OrganizationDataBase(orgId)
            status_code = organizationDB.checkRole(roleId)
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
            
            tasks, status_code = organizationDB.getRoleTasks(roleId)
            if status_code == 400:
                return {
                    "statuts_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid roleId. Expected a string."
                }
            if status_code == 404:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": f"Tasks Not Found for roleId: {roleId}"
                }
            if not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error",
                }
            return {
                "status_code": status.HTTP_200_OK,
                "tasks": tasks
            }
        except Exception as e:
            logger.error(f"Error in getTasksForRole: {str(e)}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": "Internal server error",
            }
        
    def getAgents(self, data: dict):
            try:
                print('role',self.role,data)
                if not "analyst" in self.role:
                    return {
                        "status_code": status.HTTP_401_UNAUTHORIZED,
                        "detail": "Unauthorized Access",
                    }
                orgId = data.get("orgId")

                tagName=data.get("tagName")
                
                if not orgId or not tagName:
                    return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. orgId and tagName must be provided."
                }

                if not isinstance(orgId, str) or not isinstance(tagName, str):
                    return {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "detail": "Invalid orgId and tagName. Expected a string."
                    }

                if orgId not in self.orgIds:
                    return {
                        "status_code": status.HTTP_403_FORBIDDEN,
                        "detail": "Unauthorized access to the organization."
                    }

                status_code = self.applicationDB.checkOrg(orgId)
                if status_code == 404:
                    return {
                        "status_code": status.HTTP_404_NOT_FOUND,
                        "detail": "Organization not found."
                    }
                if status_code != 200:
                    return {
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "detail": "Error while connecting to Database."
                    }
                organizationDB = OrganizationDataBase(orgId)
                agents, status_code = organizationDB.getAgents(tagName)
                if status_code == 404:
                    return {
                        "status_code": status.HTTP_404_NOT_FOUND,
                        "detail": "Agents not found."
                    }
                if status_code != 200:
                    return {
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "detail": "Internal server error."
                    }
                return {
                    "status_code": status.HTTP_200_OK,
                    "agents": agents
                }
            except Exception as e:
                logger.error(f"Error in getAgents: {str(e)}")
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error",
                }
    

                    
