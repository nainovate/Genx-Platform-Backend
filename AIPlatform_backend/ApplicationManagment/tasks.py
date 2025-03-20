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
    

    def getTasks(self, data:dict):
        try:
            if not "aiengineer" in self.role and not "dataengineer" in self.role:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail": "Unauthorized Access",
                }
            
            orgId = data.get("orgId")
            if not orgId:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. orgId and roleId must be provided."
                }

            if not isinstance(orgId, str):
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
            tasks, status_code = organizationDB.getTasks()
            if status_code == 404:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": f"Tasks Not Found for orgId: {orgId}"
                }
            elif not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error",
                }
            return {
                "status_code": status.HTTP_200_OK,
                "tasks": tasks
            }
        except Exception as e:
            logger.error(f"Error in getTasks For orgId: {str(e)}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": "Internal server error",
            }

    def getAgents(self, data: dict):
            try:
                if not "analyst" in self.role:
                    return {
                        "status_code": status.HTTP_401_UNAUTHORIZED,
                        "detail": "Unauthorized Access",
                    }
                orgId = data.get("orgId")                
                if not orgId:
                    return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. orgId must be provided."
                }

                if not isinstance(orgId, str):
                    return {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "detail": "Invalid orgId. Expected a string."
                    }

                if orgId not in self.orgIds:
                    return {
                        "status_code": status.HTTP_403_FORBIDDEN,
                        "detail": "Unauthorized access to the organization."
                    }

                status_code = self.applicationDB.checkOrg(orgId)
                if status_code == 404:
                    return {
                        "detail": "Organization not found.",
                         "status_code": status.HTTP_404_NOT_FOUND,
                    }
                elif status_code != 200:
                    return {
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "detail": "Error while connecting to Database."
                    }
                organizationDB = OrganizationDataBase(orgId)
                agents, status_code = organizationDB.getAgents()

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
            

    def createTask(self, data: dict):
        try:
            # Validate input data
            if not isinstance(data, dict) or "orgId" not in data or "taskName" not in data or "description" not in data or "roleIds" not in data or "spaceId" not in data:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. Expected a dictionary with 'taskName', 'description', 'orgId', 'roleIds', and 'spaceId' keys."
                }

            if data["orgId"] == '' or data["taskName"] == '' or not data["roleIds"]:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "OrgId, taskName, and roleIds are required fields."
                }
            
            # Add type validation in createTask
            if not all(isinstance(id, str) for id in data["roleIds"]):
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "roleIds must be strings"
                }

            if len(data["taskName"]) > 255:  # example max length
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "taskName too long"
                }

            # Check if user has authorization to create a task
            if "analyst" not in self.role:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail": "Unauthorized Access"
                }

            # Ensure the organization ID is valid for the user
            if data["orgId"] not in self.orgIds:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail": "Unauthorized Access"
                }

            # Check if organization exists
            status_code = self.applicationDB.checkOrg(data["orgId"])
            if status_code == 404:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "Organization not found."
                }
            elif status_code != 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Invalid or Incorrect orgId."
                }

            # Initialize the organization database
            clientApiKey = self.applicationDB.getApiKey(data["orgId"])
            organizationDB = OrganizationDataBase(data["orgId"])
            if organizationDB.status_code != 200:
                return {
                    "status_code": organizationDB.status_code,
                    "detail": "Error initializing the organization database"
                }

            # Check if the space exists
            spaceId = data["spaceId"]
            logging.info(f"Checking space with ID: {spaceId}")  # Log the spaceId for debugging
            status_code = organizationDB.checkSpace(spaceId=spaceId)
            if status_code == 404:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,  # Correct status code for "Not Found"
                    "detail": f"Space with ID {spaceId} not found."
                }
            elif status_code != 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error while checking space."
                }
            roleIds = data["roleIds"]
    
            for roleId in roleIds:
                status_code = organizationDB.checkRole(roleId=roleId)
                if status_code != 200:
                    return {
                        "status_code": status.HTTP_404_NOT_FOUND,
                        "detail": f"Role Not Found for roleId: {roleId}",
                    }
                # Check if the role is associated with the space
                status_code = organizationDB.checkRoleAccess(roleId, spaceId)
                if status_code != 200:
                    return {
                        "status_code": status.HTTP_404_NOT_FOUND,
                        "detail": f"Role doesn't have access for spaceId: {spaceId}"
                    }
            if "agentId" in data:
                agentId = data["agentId"]   
                if not isinstance(data["agentId"], str):
                    return {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "detail": "agentId must be a string"
                    }

                status_code = organizationDB.checkAgent(agentId)
                if status_code != 200:
                    return {
                        "status_code": status.HTTP_404_NOT_FOUND,
                        "detail": f"Agent with ID {data['agentId']} not found"
                    }

                # Create the task in the organization database
                taskInfo = {
                    "taskName": data["taskName"],
                    "description": data["description"],
                    "roleIds": roleIds,
                    "createdBy": self.userId,
                    "agentId": agentId,
                    "clientApiKey" : clientApiKey
                }
            else:
                taskInfo = {
                    "taskName": data["taskName"],
                    "description": data["description"],
                    "roleIds": roleIds,
                    "createdBy": self.userId,
                    "clientApiKey" : clientApiKey
                }
                
            status_code = organizationDB.createTask(taskInfo=taskInfo)


            if status_code == status.HTTP_409_CONFLICT:
                return {
                    "status_code": status.HTTP_409_CONFLICT,
                    "detail": "Task Name Already Exists."
                }
            elif status_code == status.HTTP_200_OK:
                return {
                    "status_code": status.HTTP_200_OK,
                    "detail": "Task Created Successfully."
                }

            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": "Internal server error occurred."
            }
        except Exception as e:
            logging.error(f"Error while creating Task: {e}", exc_info=True)
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": str(e)
            }
        

    
    def updateTask(self, data: dict):
        try:
            # Validate required input data
            if not isinstance(data, dict) or "orgId" not in data or "taskId" not in data:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. Expected a dictionary with 'orgId' and 'taskId' keys."
                }
            if data["orgId"] == '' or data["taskId"] == '':
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "OrgId and taskId are required fields."
                }

            # Check if at least one optional field is present
            optional_fields = ['taskName', 'description', 'agentId']
            if not any(field in data for field in optional_fields):
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "At least one of taskName, description, or agentId must be provided for update."
                }

            # Rest of the authorization and organization checks...
            if "analyst" not in self.role:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail": "Unauthorized Access"
                }

            if data["orgId"] not in self.orgIds:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail": "Unauthorized Access"
                }

            # Organization existence check...
            status_code = self.applicationDB.checkOrg(data["orgId"])
            if status_code == 404:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "Organization not found."
                }
            elif status_code != 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Invalid or Incorrect orgId."
                }

            # Initialize database...
            organizationDB = OrganizationDataBase(data["orgId"])
            if organizationDB.status_code != 200:
                return {
                    "status_code": organizationDB.status_code,
                    "detail": "Error initializing the organization database"
                }

            # Task existence check...
            status_code = organizationDB.checkTask(data["taskId"])
            
            if status_code == 404:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "Task not found"
                }
            elif status_code != 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Error checking task existence"
                }

            # Initialize taskInfo with optional fields
            taskInfo = {}

            # Add only the provided optional fields
            for field in optional_fields:
                if field in data:
                    taskInfo[field] = data[field]
            print('-------agentId',data.get("agentId"))
            if "agentId" in data and data.get("agentId"):
                agentId = data["agentId"]   
                if not isinstance(data["agentId"], str):
                    return {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "detail": "agentId must be a string"
                    }

                status_code = organizationDB.checkAgent(agentId)
                if status_code != 200:
                    return {
                        "status_code": status.HTTP_404_NOT_FOUND,
                        "detail": f"Agent with ID {data['agentId']} not found"
                    }
                taskInfo["agentId"] = data["agentId"]
                
            # Update task...
            status_code = organizationDB.updateTask(taskId=data["taskId"], taskInfo=taskInfo)
            if status_code == status.HTTP_409_CONFLICT:
                return {
                    "status_code": status.HTTP_409_CONFLICT,
                    "detail": "Task Name Already Exists."
                }
            elif status_code == status.HTTP_200_OK:
                return {
                    "status_code": status.HTTP_200_OK,
                    "detail": "Task Updated Successfully."
                }
            
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": "Task updation failed."
            }

        except Exception as e:
            logging.error(f"Error while updating Task: {e}", exc_info=True)
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": str(e)
            }     
        
    
    
    def deleteTask(self, data: dict):
        try:
            # Validate required input data
            if not isinstance(data, dict) or "orgId" not in data or "taskId" not in data:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. Expected a dictionary with 'orgId' and 'taskId' keys."
                }
            if data["orgId"] == '' or data["taskId"] == '':
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "OrgId and taskId are required fields."
                }

            # Authorization checks
            if "analyst" not in self.role:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail": "Unauthorized Access"
                }

            if data["orgId"] not in self.orgIds:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail": "Unauthorized Access"
                }

            # Check if the organization exists
            status_code = self.applicationDB.checkOrg(data["orgId"])
            if status_code == 404:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "Organization not found."
                }
            elif status_code != 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Invalid or Incorrect orgId."
                }

            # Initialize database
            organizationDB = OrganizationDataBase(data["orgId"])
            if organizationDB.status_code != 200:
                return {
                    "status_code": organizationDB.status_code,
                    "detail": "Error initializing the organization database"
                }

            # Check if task exists
            status_code = organizationDB.checkTask(data["taskId"])
            if status_code == 404:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "Task not found"
                }
            elif status_code != 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Error checking task existence"
                }

            # Delete task
            status_code = organizationDB.deleteTask(data["taskId"])
            if status_code == status.HTTP_200_OK:
                return {
                    "status_code": status.HTTP_200_OK,
                    "detail": "Task Deleted Successfully."
                }
            elif status_code == status.HTTP_404_NOT_FOUND:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "Task not found."
                }

            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": "Internal server error occurred."
            }

        except Exception as e:
            logging.error(f"Error while deleting Task: {e}", exc_info=True)
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": str(e)
            }




    def assignTask(self, data: dict):
        try:
            expected_keys = {"orgId", "spaceId", "roleId", "userId", "taskIds"}

            # Validate input data type and required fields
            if not isinstance(data, dict) or set(data.keys()) != expected_keys:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. Expected a dictionary with keys 'orgId', 'spaceId', 'roleId', 'userId', and 'taskIds'."
                }

            orgId = data.get("orgId")
            spaceId = data.get("spaceId")
            roleId = data.get("roleId")
            userId = data.get("userId")
            taskIds = data.get("taskIds")

            if not all(isinstance(value, str) and value.strip() for value in [orgId, spaceId, roleId, userId]) or not isinstance(taskIds, list):
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "orgId, spaceId, roleId, and userId must be non-empty strings, and taskIds must be a list."
                }

            # Ensure only Analysts can assign tasks
            if "analyst" not in self.role:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail": "Unauthorized Access. Only Analysts can assign tasks."
                }

            # Validate each task
            invalid_tasks = []
            valid_tasks = []
          # Initialize database
            organizationDB = OrganizationDataBase(data["orgId"])
            if organizationDB.status_code != 200:
                return {
                    "status_code": organizationDB.status_code,
                    "detail": "Error initializing the organization database"
                }
            for taskId in taskIds:
                task_status = organizationDB.checkTask(taskId)  
                
                if task_status == status.HTTP_200_OK:
                    valid_tasks.append(taskId)
                else:
                    invalid_tasks.append(taskId)

            # If all tasks are invalid, return error
            if not valid_tasks:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": f"None of the provided tasks exist: {invalid_tasks}"
                }

            # If some tasks are invalid, log warning and proceed with valid ones
            if invalid_tasks:
                logging.warning(f"The following tasks were not found and will be skipped: {invalid_tasks}")

            # Proceed with assignment of valid tasks only
            response = self.applicationDB.assignTask(
                orgId=orgId, 
                spaceId=spaceId, 
                roleId=roleId, 
                userId=userId, 
                taskIds=valid_tasks
            )

            # If there were some invalid tasks, modify the success message
            if response["status_code"] == status.HTTP_200_OK and invalid_tasks:
                response["detail"] = f"Tasks partially assigned. Successfully assigned {len(valid_tasks)} tasks. {len(invalid_tasks)} invalid tasks were skipped: {invalid_tasks}"

            return response

        except Exception as e:
            logging.error(f"Error while assigning tasks: {e}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"Internal server error: {e}"
            }
        


    def unassignTask(self, data: dict):
        try:
            expected_keys = {"orgId", "spaceId", "roleId", "userId", "taskIds"}

            # Validate input data type and required fields
            if not isinstance(data, dict) or set(data.keys()) != expected_keys:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. Expected a dictionary with keys 'orgId', 'spaceId', 'roleId', 'userId', and 'taskIds'."
                }

            orgId = data.get("orgId")
            spaceId = data.get("spaceId")
            roleId = data.get("roleId")
            userId = data.get("userId")
            taskIds = data.get("taskIds")

            if not all(isinstance(value, str) and value.strip() for value in [orgId, spaceId, roleId, userId]) or not isinstance(taskIds, list):
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "orgId, spaceId, roleId, and userId must be non-empty strings, and taskIds must be a list."
                }

            # Ensure only Analysts can unassign tasks
            if "analyst" not in self.role:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail": "Unauthorized Access. Only Analysts can unassign tasks."
                }

            # Call the database function to unassign tasks
            response = self.applicationDB.unassignTask(
                orgId=orgId,
                spaceId=spaceId,
                roleId=roleId,
                userId=userId,
                taskIds=taskIds
            )

            return response

        except Exception as e:
            logging.error(f"Error while unassigning tasks: {e}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"Internal server error: {e}"
            }


    def getTaskIds(self):
        try:
            if not "user" in self.role:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail": "Unauthorized Access",
                }
            all_tasks =[]
            for orgId, spaces in self.role["user"].items():
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
                applicationDB = ApplicationDataBase()
                orgInfo, status_code = applicationDB.getOrgInfo(orgId=orgId)
                for spaceId, rolesIds in spaces.items():
                    roles = [] 
                    for roleId, task_ids in rolesIds.items():
                        organizationDB = OrganizationDataBase(orgId)
                        roleInfo, status_code = organizationDB.getRoleInfo(roleId)
                        tasks =[]
                        for taskId in task_ids:
                            task, status_code = organizationDB.getTaskInfo(taskId=taskId)
                            tasks.append(task)
                        roleInfo["tasks"] = tasks
                        roles.append(roleInfo)
                    orgInfo["roles"] = roles
                all_tasks.append(orgInfo)
            return {
                "status_code": status.HTTP_200_OK,
                "tasks": all_tasks
            }
        except Exception as e:
            logger.error(f"Error in getTasks For orgId: {str(e)}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": "Internal server error",
            }