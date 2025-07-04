from datetime import datetime
import os
import logging
import random
import time
from bson import ObjectId
from fastapi.responses import JSONResponse
from pymongo import UpdateOne
import pymongo
from pymongo import MongoClient, DESCENDING
from pymongo.mongo_client import MongoClient
from fastapi import HTTPException, status
from pymongo.errors import OperationFailure
from werkzeug.security import check_password_hash
from pymongo.errors import PyMongoError
from Database.evaluationSetup import MongoDBHandler
from utils import StatusRecord
from db_config import config,eval_config,bench_config,finetuning_config

# Set up logging
projectDirectory = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
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
            self.responseCollection = self.organizationDB[finetuning_config['metric_response']]
            self.dataset_collection = self.organizationDB[finetuning_config['dataset_collection']]
            self.status_collections = self.organizationDB[finetuning_config['status_collection']]
            self.finetune_configCollection = self.organizationDB[finetuning_config['finetune_config']]
            self.results_collection = self.organizationDB[eval_config['RESULTS_COLLECTION']]
            self.status_collection = self.organizationDB[eval_config['STATUS_COLLECTION']]
            self.config_collection = self.organizationDB[eval_config['CONFIG_COLLECTION']]
            self.metrics_collection = self.organizationDB[eval_config['METRICS_COLLECTION']]
            self.llmPrompts_collection=self.organizationDB['LLMPrompts']
            self.ingest_configuration = self.organizationDB['ingestConfigs']
            self.vector_config = self.organizationDB['vectorDbConfig']
            self.splitter_config = self.organizationDB['splitterDbConfig']
            self.embedding_models = self.organizationDB['embeddingModels']
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
    
    def createSpace(self, spaceName: str, userId: str):
        try:

            # Validate input types
            if not isinstance(spaceName, str) or not isinstance(userId, str):
                logging.error("Invalid input data types. Expected strings for spaceName, and userId.")
                return status.HTTP_400_BAD_REQUEST
            
            if self.organizationDB is None:
                logging.error("Organization database is not initialized.")
                return status.HTTP_500_INTERNAL_SERVER_ERROR
            
            # Check if spaceName already exists
            existing_space_name = self.organizationDB["spaces"].find_one({"spaceName": spaceName})
            if existing_space_name:
                logging.error("Space Name Already Exists")
                return status.HTTP_409_CONFLICT
            
            data = {
                "spaceName": spaceName,
                "createdBy": userId
            }

            # Insert the new space data into the database
            self.organizationDB["spaces"].insert_one(data)
            logging.info(f"Space {spaceName} created successfully ")
            return status.HTTP_200_OK
        except Exception as e:
            logging.error(f"Error while creating space: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def removeSpace(self, spaceId: str):
        try:
            result = self.organizationDB["spaces"].delete_one(
                {"_id": ObjectId(spaceId)}
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

            space = self.organizationDB["spaces"].find_one({"_id": ObjectId(spaceId)})
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
                {"_id": ObjectId(spaceId)},
                {"$set": {"spaceName": spaceName}}
            )
            if result.matched_count==1:
                return status.HTTP_200_OK
            else:
                return status.HTTP_422_UNPROCESSABLE_ENTITY
        except Exception as e:
            logging.error(f"Error while updating space: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR

    def getSpaceInOrg(self,role,userId,orgId):
        try:
            if self.organizationDB is None:
                logging.error("Organization database is not initialized.")
                return None, status.HTTP_500_INTERNAL_SERVER_ERROR
            if "admin" in role:
                spaces_list = list(self.organizationDB["spaces"].find({"createdBy":userId}, {"createdBy":0}))
                if len(spaces_list) > 0:
                    spaces = [{"spaceId":str(space["_id"]),"spaceName":space["spaceName"]} for space in spaces_list]
                    parsedSpaces =[]
                    for space in spaces:
                        role_list = list(self.organizationDB["roles"].find({"spaceIds": {"$elemMatch": {"$eq": space["spaceId"]}}}, {"_id": 1, "roleName":1, "description":1}))
                        if len(role_list):
                            roles = [{"roleId":str(role["_id"]),"roleName":role["roleName"],"description":role["description"]} for role in role_list]
                            space["roles"] = roles
                        parsedSpaces.append(space)
                    return parsedSpaces, status.HTTP_200_OK
                else:
                    logging.info("No spaces found for this Org.")
                    return [], status.HTTP_404_NOT_FOUND
            elif "analyst" in role:
                spaceIds = role["analyst"][f"{orgId}"]
                if len(spaceIds) ==0:
                    return [], status.HTTP_404_NOT_FOUND
                spaces_list =[]
                for spaceId in spaceIds:
                    space = self.organizationDB["spaces"].find_one({"_id":ObjectId(spaceId)}, {"_id": 1,"createdBy":0})
                    if space:
                        space["_id"] = str(space["_id"])
                        spaces_list.append(space)
                return spaces_list,status.HTTP_200_OK
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
    
    def createRole(self, roleInfo:dict, spaceIds:dict, userId: str):
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
            
            
            data = {
                "roleName": roleInfo["roleName"],
                "description":roleInfo["description"],
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
            space = self.organizationDB["spaces"].find_one({"_id":ObjectId(spaceId)}, {"_id": 1,"createdBy":0})
            if space:
                spaceInfo = {"spaceId":str(space["_id"]),"spaceName":space["spaceName"]}
                return spaceInfo, status.HTTP_200_OK
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
                roles_list = list(self.organizationDB["roles"].find({"spaceIds": {"$elemMatch": {"$eq": spaceId}}}, {"_id": 1, "roleName":1, "description":1}))
            # elif "admin" in role:
            #     spaces_list = list(self.organizationDB["spaces"].find({}, {"_id": 0,"createdBy":0}))
            if len(roles_list) > 0:
                roles = [{"roleId":str(role["_id"]),"roleName":role["roleName"],"description":role["description"]} for role in roles_list]
                parsedRoles =[]
                for role in roles:
                    tasks_list = list(self.organizationDB["tasks"].find({"roleIds": {"$elemMatch": {"$eq": role["roleId"]}}}, {"_id": 1, "taskName":1, "description":1}))
                    if len(tasks_list):
                        tasks = [{"taskId":str(task["_id"]),"taskName":task["taskName"],"description":task["description"]} for task in tasks_list]
                        role["tasks"] = tasks
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
            if not isinstance(roleId, str):
                return status.HTTP_400_BAD_REQUEST

            role = self.organizationDB["roles"].find_one({"_id": ObjectId(roleId)})
            if role:
                return status.HTTP_200_OK
            else:
                return status.HTTP_404_NOT_FOUND
        except Exception as e:
            # Log and handle unexpected errors
            logging.error(f"Error while checking space for roleId {roleId}: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
        

    def checkRoleAccess(self, roleId: str, spaceId: str):
        try:
            # Check if spaceId is a string
            if not isinstance(roleId, str):
                return status.HTTP_400_BAD_REQUEST

            role = self.organizationDB["roles"].find_one({"_id":ObjectId(roleId) , "spaceIds": {"$elemMatch": {"$eq": spaceId}}})
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
                {"_id": ObjectId(data['roleId'])},
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
                {"_id": ObjectId(roleId)}
            )
            if result.deleted_count==1:
                return status.HTTP_200_OK
            else:
                return status.HTTP_422_UNPROCESSABLE_ENTITY
        except Exception as e:
            logging.error(f"Error while removing Space: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def getRoleTasks(self, roleId: str):
        try:
            if not isinstance(roleId, str):
                return status.HTTP_400_BAD_REQUEST
            tasks = self.organizationDB["tasks"].find({"roleIds": {"$elemMatch": {"$eq": roleId}}}, {"roleIds": 0})
            tasks_list = list(tasks)
            
            if tasks_list:
                result = [{"taskName": task["taskName"], "taskId": str(task["_id"]),"taskDescription":str(task["description"]),"agentId":task.get("agentId","")} for task in tasks_list]
                return result, status.HTTP_200_OK
            else:
                return {"detail": "No tasks found for the given roleId."}, status.HTTP_404_NOT_FOUND
        except Exception as e:
            logging.error(f"Error while retrieving tasks: {e}")
            return None, status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def getTasks(self):
        try:
            tasks = self.organizationDB["tasks"].find({}, {"roleIds": 0})
            tasks_list = list(tasks)
            
            if tasks_list:
                result = [{"taskName": task["taskName"], "taskId": str(task["_id"]),"description":str(task["description"]),"agentId":task.get("agentId","")} for task in tasks_list]
                return result, status.HTTP_200_OK
            else:
                return [], status.HTTP_404_NOT_FOUND
        except Exception as e:
            logging.error(f"Error while retrieving tasks: {e}")
            return None, status.HTTP_500_INTERNAL_SERVER_ERROR

    def getAgents(self):
        try:
            agents = self.organizationDB["DeploymentConfig"].find()
            agents_list = list(agents)
            if len(agents_list) ==0:
                return agents_list,status.HTTP_404_NOT_FOUND
            
            else:
                result = [{**agent, "_id": str(agent["_id"])} for agent in agents_list]
                return result, status.HTTP_200_OK
                
        except Exception as e:
            logging.error(f"Error while fetching agents: {e}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": "Internal server error."
            }
    

    def checkAgent(self, agentId: str):
        try:
            if not isinstance(agentId, str):
                return status.HTTP_400_BAD_REQUEST

            role = self.organizationDB["DeploymentConfig"].find_one({"_id": ObjectId(agentId)})
            if role:
                return status.HTTP_200_OK
            else:
                return status.HTTP_404_NOT_FOUND
        except Exception as e:
            # Log and handle unexpected errors
            logging.error(f"Error while checking space for roleId {agentId}: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
        

    def getRolesInfo(self,spaceId):
        try:
            if self.organizationDB is None:
                logging.error("Organization database is not initialized.")
                return None, status.HTTP_500_INTERNAL_SERVER_ERROR
            roles = self.organizationDB["roles"].find({"spaceIds": {"$elemMatch": {"$eq": spaceId}}}, {"createdBy":0})
            roles_list = list(roles)
            if roles_list:
                result = [{"roleName": role["roleName"], "roleId": str(role["_id"]),"description":role["description"]} for role in roles_list]
                return result, status.HTTP_200_OK
            else:
                logging.info("roles not found.")
                return [], status.HTTP_404_NOT_FOUND
        except Exception as e:
            logging.error(f"Error while retrieving spaces: {e}")
            return [], status.HTTP_500_INTERNAL_SERVER_ERROR


    def createTask(self, taskInfo: dict):
        try:
            # Validate input types
            if self.organizationDB is None:
                logging.error("Organization database is not initialized.")
                return status.HTTP_500_INTERNAL_SERVER_ERROR
            
            # Check if taskName already exists
            existing_task_name = self.organizationDB["tasks"].find_one({"taskName": taskInfo["taskName"]})
            if existing_task_name:
                logging.error("Task Name Already Exists")
                return status.HTTP_409_CONFLICT

            # Insert the new task data into the database
            try:
                self.organizationDB["tasks"].insert_one(taskInfo)
                logging.info(f"Task {taskInfo['taskName']} created successfully")
                return status.HTTP_200_OK
            except Exception as e:
                logging.error(f"Error inserting task into database: {e}")
                return status.HTTP_500_INTERNAL_SERVER_ERROR

        except Exception as e:
            logging.error(f"Error while creating Task: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
            
    def checkTask(self, taskId: str):
        try:
            if not isinstance(taskId, str) or not ObjectId.is_valid(taskId):
                return status.HTTP_400_BAD_REQUEST
            
            task = self.organizationDB["tasks"].find_one({"_id": ObjectId(taskId)})
            
            if not task:
                return status.HTTP_404_NOT_FOUND  # Return 404 if task doesn't exist

            return status.HTTP_200_OK  # Return the found task

        except Exception as e:
            return status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def updateTask(self, taskId: str, taskInfo: dict):
        try:
            # Validate input types
            if self.organizationDB is None:
                logging.error("Organization database is not initialized.")
                return status.HTTP_500_INTERNAL_SERVER_ERROR

            # Check for duplicate task name only if taskName is being updated
            if 'taskName' in taskInfo:
                try:
                    existing_task_name = self.organizationDB["tasks"].find_one({
                        "taskName": taskInfo['taskName'] # Exclude current task
                    })

                    if existing_task_name:
                        logging.error(f"Task Name '{taskInfo['taskName']}' Already Exists for another task.")
                        return status.HTTP_409_CONFLICT
                except Exception as e:
                    logging.error(f"Error checking for duplicate task name: {e}", exc_info=True)
                    return status.HTTP_500_INTERNAL_SERVER_ERROR

            # Update the task data in the database
            try:
                result = self.organizationDB["tasks"].update_one(
                    {"_id": ObjectId(taskId)},
                    {"$set": taskInfo}
                )

                if result.modified_count == 0:
                    logging.error(f"No task was updated with ID: {taskId}")
                    return status.HTTP_404_NOT_FOUND

                logging.info(f"Task updated successfully")
                return status.HTTP_200_OK

            except Exception as e:
                logging.error(f"Error updating task in database: {e}", exc_info=True)
                return status.HTTP_500_INTERNAL_SERVER_ERROR

        except Exception as e:
            logging.error(f"Unexpected error while updating Task: {e}", exc_info=True)
            return status.HTTP_500_INTERNAL_SERVER_ERROR
    

    def deleteTask(self, taskId: str):
        try:
            if not isinstance(taskId, str) or not ObjectId.is_valid(taskId):
                return status.HTTP_400_BAD_REQUEST
            
            result = self.organizationDB["tasks"].delete_one({"_id": ObjectId(taskId)})
            
            if result.deleted_count == 0:
                return status.HTTP_404_NOT_FOUND  # Return 404 if no task was deleted
            
            return status.HTTP_200_OK  # Successfully deleted task
        
        except Exception as e:
            logging.error(f"Error deleting task from database: {e}", exc_info=True)
            return status.HTTP_500_INTERNAL_SERVER_ERROR


    def get_metrics_by_process_id(self, process_id):
        try:
            
            if not process_id:
                return {"status_code": status.HTTP_400_BAD_REQUEST, 
                        "message": "Missing required 'process_id' in the request data."}

            document = self.responseCollection.find_one({"process_id": process_id})
            

            if not document:
                return {"status_code": status.HTTP_404_NOT_FOUND,
                         "message": f"No document found with process_id: {process_id}"}

            metrics = document.get("metrics", [])

            if not metrics:
                return {"status_code": status.HTTP_404_NOT_FOUND, 
                        "message": "No metrics found for the given process_id."}

            return {"status_code": status.HTTP_200_OK, 
                    "message": "Metrics retrieved successfully.", "data": metrics}

        except pymongo.errors.ConnectionFailure:
            return {"status_code": status.HTTP_503_SERVICE_UNAVAILABLE,
                     "message": "Database connection failed. Please try again later."}

        except HTTPException as http_exc:
            return {"status_code": http_exc.status_code, 
                    "message": http_exc.detail}

        except Exception as e:
            return {"status_code": status.HTTP_500_INTERNAL_SERVER_ERROR, 
                    "message": "Error retrieving metrics.", "detail": str(e)}
        
    def fetch_process_status(self, process_id):
        """Fetch the document with the given process ID."""
        try:

            # Validate process_id
            if not process_id or not isinstance(process_id, str):
                logging.error("Invalid process ID.")
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid process ID. It must be a non-empty string."
                }

            # Ensure MongoDB collection is initialized
            if self.status_collection is None:
                logging.error("MongoDB collection is not initialized.")
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Database connection issue."
                }

            # Fetch the document
            document = self.status_collections.find_one({"process_id": process_id})

            # If process ID does not exist, return an error response
            if not document:
                logging.warning(f"Process ID {process_id} not found.")
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": f"Process ID {process_id} not found."
                }

            return document  # Return the found document

        except Exception as e:
            logging.error(f"Database error while fetching process status: {str(e)}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"Database error: {str(e)}"
            }




    def get_documents_by_user_id(self, user_id):
        try:
            # Validate input
            if not user_id:
                return {"status_code": status.HTTP_400_BAD_REQUEST, "detail": "user_id is required"}

            # Fetch all documents matching the user_id from MongoDB
            documents = self.responseCollection.find({"user_id": user_id}).to_list(length=None)

            if not documents:
                # If no documents are found, return a 404 error
                return {
                    "status_code":status.HTTP_404_NOT_FOUND,
                    "detail":{"message": f"No documents found for user_id: {user_id}","detail":status.HTTP_404_NOT_FOUND}
                }

            # Convert ObjectId to string for JSON serialization
            for doc in documents:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
                for key, value in doc.items():
                    if isinstance(value, datetime):  # Check for datetime fields
                        doc[key] = value.isoformat()
            # Return the full documents as a successful response
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"message": "Documents retrieved successfully.",
                         "detail":status.HTTP_200_OK, "data": documents}
            )

        except HTTPException as http_exc:
            # Handle HTTP exceptions
            return JSONResponse(
                status_code=http_exc.status_code,
                content={"message": http_exc.detail}
            )
        except ConnectionError as conn_err:
            # Handle MongoDB connection issues
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "message": "Database connection error.",
                    "detail": str(conn_err)
                }
            )
        except Exception as e:
            # Generic error handling for unforeseen issues
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"message": "Error retrieving documents.", "detail": str(e)}
            )
        
    def insertdataset(self, document):
        try:
            if not self.client:
                raise Exception("Database client is not connected.")
            
            client_api_key = document.get("clientApiKey")
            dataset_content = document.get("datasetContent")
            path = document.get("path")
            dataset_type = document.get("dataset_name")

            if not client_api_key or not dataset_content or not path or not dataset_type:
                missing_fields = [
                    field for field in ["clientApiKey", "datasetContent", "path","dataset_name"]
                    if not document.get(field)
                ]
                return({"status_code":422, "detail":f"Missing required fields: {', '.join(missing_fields)}"})


            if not os.path.exists(path):
                raise FileNotFoundError(f"Path does not exist: {path}")
            if not os.access(path, os.R_OK):
                raise PermissionError(f"Path is not readable: {path}")

            dataset_id = self.generate_id(4)
            timestamp = self.get_current_timestamp()
            payload_document = {
                "dataset_name": dataset_type,
                "dataset_id": dataset_id,
                "clientApiKey": client_api_key,
                "dataset_path": path,
                "dataset": dataset_content,
                "timestamp": timestamp,
                
            }

            insert_result = self.dataset_collection.insert_one(payload_document)
            if not insert_result.acknowledged:
                raise Exception("Failed to insert document into MongoDB.")

            return 200, {"success": True, "dataset_id": dataset_id}

        except FileNotFoundError as fnfe:
            return 404, {"success": False, "error": str(fnfe)}
        except PermissionError as pe:
            return 403, {"success": False, "error": str(pe)}
        except ValueError as ve:
            return 400, {"success": False, "error": str(ve)}
        except Exception as e:
            return 500, {"success": False, "error": f"Unexpected error: {str(e)}"}
    def generate_id(self,length):
        result = ''
        characters = '0123456789'
        for i in range(length):
            result += random.choice(characters)
        return result
    def get_current_timestamp(self):
        return int(time.time())
    



    async def get_dataset_path(self, dataset_id):
        try:
            
            dataset_id = str(dataset_id)
           
            # Convert dataset_id to ObjectId if necessary
            query = {"dataset_id": dataset_id}

            document = self.dataset_collection.find_one(query)
            

            if document and "dataset_path" in document:
                return {"status_code": 200, "dataset_path": document["dataset_path"]}
            else:
                return {"status_code": 404, "detail": "Dataset not found."}

        except Exception as e:
            return {"status_code": 500, "detail": str(e)}
    def dataset_details(self):
        """
        Fetches datasets details from the MongoDB collection for the given organisation.

        :return: Dictionary containing success status and dataset details or an error message.
        """
        try:
            # Query the collection for dataset details, excluding the "_id" field
            datasets = self.dataset_collection.find({}, {"_id": 0, "dataset": 0}).sort("timestamp", DESCENDING).to_list(length=None)

            if datasets is None:
                logging.error("Unexpected None response from database query.")
                return {"success": False, "error": "Unexpected database response."}

            if not datasets:
                logging.warning("No datasets data found.")
                return {"success": False, "message": "No dataset data found."}

            logging.info(f"Datasets fetched successfully: {len(datasets)} records.")
            return {"success": True, "data": datasets}

        except ConnectionError as e:
            logging.error(f"Database connection error: {e}")
            return {"success": False, "error": f"Database connection failed: {str(e)}"}

        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return {"success": False, "error": "An unexpected error occurred."}
        

    def delete_dataset(self, json_data):
        try:
            print("json data ",json_data)
            client_api_key = json_data["clientApiKey"]
            dataset_Ids = json_data["dataset_Ids"]

            if not client_api_key or not dataset_Ids:
                logging.error("Missing required fields: 'clientApiKey' or 'dataset_Ids'")
                return {"status_code": 400, "detail": "Missing 'clientApiKey' or 'dataset_Ids'."}

          

            # Ensure dataset_Id is a string and handle list case
            if isinstance(dataset_Ids, list):
                dataset_Ids = [str(item) for item in dataset_Ids]  # Convert items to strings

            # For multiple deletions, use delete_many with $in operator
            query = {"clientApiKey": client_api_key, "dataset_id": {"$in": dataset_Ids} if isinstance(dataset_Ids, list) else str(dataset_Ids)}
            

            if isinstance(dataset_Ids, list):
                result = self.dataset_collection.delete_many(query)
            else:
                result = self.dataset_collection.delete_one(query)
            print("result ---",result)
            return {"deleted_count": result.deleted_count, "status_code": 200 if result.deleted_count > 0 else 404}

        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return {"status_code": 500, "detail": "Unexpected server error."}
        
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
            prompts = self.organizationDB["payload"]

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
          
    async def config_record(self, config_data):
        """
        Inserts a new fine-tuning configuration record into the database.
        
        Args:
            config_data (dict): Dictionary containing user_id, process_id, model_id, dataset_path.
        
        Returns:
            dict: A response dictionary with status_code and message.
        """
        try:
            print("entered to database ")
            # Validate required fields
            required_keys = {"user_id", "process_id", "model_id", "dataset_path","Timestamp"}
            if not required_keys.issubset(config_data.keys()):
                missing_keys = required_keys - config_data.keys()
                return {"status_code": 400, "detail": f"Missing required fields: {missing_keys}"}

            # Generate timestamp
            timestamp = self.get_current_timestamp()

            # Insert the new record
            self.finetune_configCollection.insert_one({
                "user_id": config_data["user_id"],
                "process_id": config_data["process_id"],
                "model_id": config_data["model_id"],
                "dataset_path": config_data["dataset_path"],
                "timestamp": timestamp
            })

            return {"status_code": 200, "detail": "Record inserted successfully"}
        
        except Exception as e:
            logging.error(f"Error inserting config record: {str(e)}")
            return {"status_code": 500, "detail": "Internal server error"}

    def addPrompt(self, data: dict):
        try:
            org_id = data.get("orgId")
            if not org_id:
                return status.HTTP_400_BAD_REQUEST, False, "Missing 'orgId' in request data"
            
            prompt_name = data.get("promptName", "").strip()
            if not prompt_name:
                return status.HTTP_400_BAD_REQUEST, False, "Prompt name is required"

            # Check if prompt with the same name already exists
            existing_prompt = self.llmPrompts_collection.find_one({"promptName": prompt_name})
            if existing_prompt:
                return status.HTTP_409_CONFLICT, False, "A prompt with this name already exists"

            timestamp = self.get_current_timestamp()
            
            # Prepare document for insertion
            prompt_document = {
                "promptName": prompt_name,
                "taskType": data.get("taskType", ""),
                "systemMessage": data.get("systemMessage", ""),
                "aiMessage": data.get("aiMessage", ""),
                "humanMessage": data.get("humanMessage", ""),
                "inputData": data.get("inputData", {}),
                "timestamp": timestamp
            }
            print("Prompt Document:", prompt_document)  # Debugging

            # Insert into MongoDB
            result = self.llmPrompts_collection.insert_one(prompt_document)
            return status.HTTP_200_OK, True, "Prompt added successfully"

        except Exception as e:
         print(f"Error in addPrompt: {e}")
         return status.HTTP_500_INTERNAL_SERVER_ERROR, False, str(e) 

    def get_prompts_data(self):
        """
        Fetches LLM Prompts data for a given organization (by orgId).

        :return: List of prompts data or raises HTTPException if error occurs.
        """
        try: 
            if not self.orgId:
                return status.HTTP_400_BAD_REQUEST, False, "Missing 'orgId' in request data"
            # Query to get the prompts data for this org_id
            prompts = self.llmPrompts_collection.find({}).to_list(length=100)  # Adjust the query if needed
            logger.info(f"The prompts are: {prompts}")

            if not prompts:
                logger.warning(f"No prompts found for orgId {self.orgId}")
                return [], 404  # Return empty list and 404 status if no data found

            # Inline serialization: Convert ObjectId to string directly in the list
            prompts = [
                {k: (str(v) if isinstance(v, ObjectId) else v) for k, v in prompt.items()} 
                for prompt in prompts
            ]

            return prompts, 200  # Return the prompts and a success status code

        except Exception as e:
            logger.error(f"Error fetching prompts for org {self.orgId}: {e}")
            raise HTTPException(status_code=500, detail=f"Error fetching prompts for orgId {self.orgId}") 
            
    async def update_status_in_mongo(self, status_record):
        """ Update only the status field of a model in MongoDB """
        try:
            timestamp = self.get_current_timestamp()
            # Update the status and last_updated fields
            self.status_collections.update_one(
                {"process_id": status_record["process_id"], 
                 "user_id": status_record["user_id"],
                 "model_id": status_record["model_id"]},
                {
                    "$set": {
                        "status": status_record["status"],
                        "last_updated": timestamp
                    }
                },
                upsert=True
            )
            return {
                "status_code": 200,
                "detail": f"Status updated successfully for process {status_record['process_id']}, model {status_record['model_id']}."
            }
        
        except Exception as e:
            return {
                "status_code": 500,
                "detail": f"Failed to update status for process {status_record['process_id']}, model {status_record['model_id']}: {str(e)}"
            }
    
    async def store_session_metrics(self, user_id, process_id, session_metrics, model_id, target_loss):
        print("Entered metrics into the DB")

        try:
            timestamp = self.get_current_timestamp()
            document = {
                "process_id": process_id,
                "user_id": user_id,
                "model_id": model_id,
                "Target_loss": target_loss,
                "iterations_count": len(session_metrics),
                "metrics": session_metrics,
                "timestamp": timestamp,
            }

            result = self.responseCollection.insert_one(document)  

            return {
                "status_code": 200,
                "message": "Data inserted successfully!",
                "inserted_id": str(result.inserted_id),
            }

        except Exception as e:
            return {
                "status_code": 500,
                "message": f"Failed to insert data: {str(e)}",
            }



    async def update_result_path(self, process_id, results_path):
        try:
            result =  self.responseCollection.update_one(
                {"process_id": process_id,},
                {"$set": {"results_path": results_path}},
                upsert=True
            )
            if result.matched_count > 0:
                logging.info(f"Process {process_id} updated in DB")
            else:
                logging.info(f"Process {process_id} inserted in DB")
        except Exception as e:
            logging.error(f"An error occurred while inserting/updating data for process_id {process_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


    async def get_metrics(self, process_id):
        """
        Fetch the metrics field from a MongoDB document based on process_id.

        Args:
            process_id (str): The process ID to search for.

        Returns:
            List[dict]: A list of metrics if found.

        Raises:
            HTTPException: If the document or metrics field is not found.
        """
        try:
            # Query the MongoDB collection
            document =  self.responseCollection.find_one({"process_id": process_id})

            # Check if the document exists
            if not document:
                return {
                    "status_code" :status.HTTP_404_NOT_FOUND,
                     "detail": "Document not Found"}
            # Extract the metrics field
            metrics = document.get("metrics")

            # Check if metrics is present in the document
            if metrics is None:
                return {
                    "status_code" :status.HTTP_404_NOT_FOUND,
                     "detail": f"metrics' field not found in the document. with {process_id}"}
            return metrics
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    # Evaluation
    async def check_ongoing_task(self, user_id: str):
        """Check if the user already has an ongoing evaluation task."""
        return  self.status_collection.find_one({"user_id": user_id, "overall_status": "In Progress"}) is not None

    async def insert_config_record(self, config_data: dict):
        try:
            insert_result =  self.config_collection.insert_one({  # ✅ Correct: Await only the function call
                "user_id": config_data.get('user_id'),
                "process_id": config_data.get('process_id'),
                "process_name": config_data.get("process_name"),
                "model_id": config_data.get("model_id"),
                "model_name": config_data.get("model_name"),
                "payload_file_path": config_data.get("payload_file_path"),
                "timestamp": int(datetime.utcnow().timestamp())
            })

            # Log the inserted ID (optional)
            logging.info(f"Inserted document ")

            return {"success": True, "inserted": "sucessfully"}

        except PyMongoError as e:
            logging.error(f"Database Error: {e}")
            return {"success": False, "error": "Database insertion failed"}

        except Exception as e:
            logging.error(f"Unexpected Error: {e}")
            return {"success": False, "error": "An unexpected error occurred"}
    async def check_process_name(self, process_name: str):
        if not process_name:
            raise HTTPException(status_code=400, detail="process_name parameter is required")
        
        existing_process = self.config_collection.find_one({"process_name": process_name})
        
        if existing_process:
            return {"exists": True, "message": "Process name already exists"}
        else:
            return {"exists": False, "message": "Process name is available"}
        
    async def update_status_record(self, status_record: dict):
        try:
            update_result = self.status_collection.update_one(
                {"process_id": status_record["process_id"]},
                {
                    "$set": {
                        "user_id": status_record["user_id"],
                        "process_name": status_record["process_name"],
                        "models": status_record["models"],  
                        "overall_status": status_record["overall_status"],
                        "start_time": status_record["start_time"],
                        "end_time": status_record.get("end_time", None)  
                    }
                },
                upsert=True
            )

            logging.info(f"Updated documents for process_id {status_record['process_id']}")
            return {"success": True, "modified_count": 1}

        except PyMongoError as e:
            logging.error(f"Database Error: {e}")
            return {"success": False, "error": str(e)}

        except Exception as e:
            logging.error(f"Unexpected Error: {e}")
            return {"success": False, "error": str(e)}

    async def update_results_record(self, process_id: str,process_name: str, user_id: str, config_type: str, model_id: str,model_name:str, results: dict):
        """Update the status of a specific process in the database."""
        timestamp = datetime.utcnow()
        result =  self.results_collection.update_one(
                {"user_id": user_id, "process_id": process_id, "process_name": process_name, "config_type": config_type},
                {"$push": {"models": {"model_id": model_id, "model_name": model_name, "results": results}}},
                upsert=True
        )
    async def get_results(self, process_id: str):
        try:
            document =  self.results_collection.find_one({"process_id": process_id})
            if not document:
                raise HTTPException(status_code=404, detail="Document not found.")
            results = document.get("models")
            if results is None:
                raise HTTPException(status_code=404, detail="'results' object not found in the document.")
            return results
        except Exception as e:
            # Handle any unexpected exceptions
            raise HTTPException(status_code=500, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving results: {e}")
    async def update_results_path(self, process_id, results_path):
        try:
            result = self.results_collection.update_one(
                {"process_id": process_id,},
                {"$set": {"results_path": results_path}},
                upsert=True
            )
            if result.matched_count > 0:
                logger.info(f"Process {process_id} updated in DB")
            else:
                logger.info(f"Process {process_id} inserted in DB")
        except Exception as e:
            logger.error(f"An error occurred while inserting/updating data for process_id {process_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    async def check_model_completed_status(self, process_id: str):
        # Fetch the existing record
        existing_record = self.status_collection.find_one({"process_id": process_id})        
        if existing_record:
            # Check if any model's status is "Completed"
            return any(model['status'] == "Completed" for model in existing_record['models']) is not None
    async def get_result_document_by_process_id(self, process_id: str):
        """Get the status of a specific process."""
        document = self.results_collection.find_one({"process_id": process_id})
        return document if document else None
    async def update_metric_status_record(self, status_record: StatusRecord, process_name):
        # Prepare the metrics object to add to the database
        metrics_data = {
            "metric_id": status_record.metric_id,  # Add the metric_id
            "models": [model_status.dict() for model_status in status_record.models],  # Convert models to dictionaries
            "metric_overall_status": status_record.overall_status  # Add the overall_status
        }
        timestamp = int(datetime.utcnow().timestamp())
        # Ensure the metric_id does not already exist in the metrics array
        status = self.status_collection.update_one(
            {
                "process_id": status_record.process_id,  # Match the process_id
                "metrics.metric_id": {"$ne": status_record.metric_id}  # Ensure the metric_id is not already in the array
            },
            {
                "$push": {
                    "metrics": metrics_data  # Add the new metric record to the array
                },
                "$set": {
                    "user_id": status_record.user_id,  # Update the user_id
                    "start_time": status_record.start_time,  # Update the start_time
                    "end_time": status_record.end_time,  # Update the end_time
                    "process_name": process_name,  # Add or update the process_name
                    "timestamp": timestamp  # Add or update the timestamp
                }
            },
            upsert=True  # Create the document if it does not exist
        )
    async def update_metric_model_status(self, process_id: str, model_id: str, new_status: str, metric_id: str, overall_status: str):
        # Check if the metric_id already exists in the metrics array
        existing_metric = self.status_collection.find_one(
            {
                "process_id": process_id,
                "metrics.metric_id": metric_id
            },
            {"metrics.$": 1}  # Only fetch the specific metric array for efficiency
        )
        
        if existing_metric:
            # If the metric exists, update the existing model status in that metric
            status = self.status_collection.update_one(
                {
                    "process_id": process_id,  # Match the process by ID
                    "metrics.metric_id": metric_id  # Match the specific metric by ID
                },
                {
                    "$set": {
                        "metrics.$.models.$[model].status": new_status,  # Update the model's status within the existing metric
                        "metrics.$.metric_overall_status": overall_status  # Update the overall status for the matched metric
                    }
                },
                array_filters=[
                    {"model.model_id": model_id}  # Filter for the correct model inside metrics' models
                ]
            )
        else:
            # If the metric does not exist, add a new metric to the metrics array
            new_metric = {
                "metric_id": metric_id,
                "models": [
                    {
                        "model_id": model_id,
                        "status": new_status  # Add the model status to the new metric
                    }
                ],
                "metric_overall_status": overall_status  # Add the overall status to the new metric
            }

            self.status_collection.update_one(
                {
                    "process_id": process_id  # Match the process by ID
                },
                {
                    "$push": {
                        "metrics": new_metric  # Push the new metric to the metrics array
                    }
                }
            )

    async def update_metrics_results_record(
        self, process_id, user_id, config_type, object_id, metric_id, 
        process_name, model_id, metrics_results
        ):
            # Define the ranges for each metric
            metric_ranges = {
                "MRR": {
                    "Excellent": "0.8 - 1.0",
                    "Moderate": "0.5 - 0.8",
                    "Poor": "0 - 0.5"
                },
                "ROUGE_score": {
                    "ROUGE-1": {
                        "Excellent": "0.45 - 1.0",
                        "Moderate": "0.30 - 0.45",
                        "Poor": "0 - 0.30"
                    },
                    "ROUGE-2": {
                        "Excellent": "0.25 - 1.0",
                        "Moderate": "0.15 - 0.25",
                        "Poor": "0 - 0.15"
                    },
                    "ROUGE-L": {
                        "Excellent": "0.40 - 1.0",
                        "Moderate": "0.25 - 0.40",
                        "Poor": "0 - 0.25"
                    }
                },
                "BERT_score": {
                    "Excellent": "0.8 - 1.0",
                    "Moderate": "0.5 - 0.8",
                    "Poor": "0 - 0.5"
                }
            }

            # Format metrics_results to retain only the scores
            for metric, values in metrics_results.items():
                if metric == "ROUGE_score":
                    for rouge_type, rouge_score in values.items():
                        values[rouge_type] = rouge_score
                else:
                    metrics_results[metric] = values

            # Get the current timestamp as Unix time
            current_timestamp = int(datetime.utcnow().timestamp())

            # Check if the document exists for the given process_id and user_id
            existing_document = self.metrics_collection.find_one(
                {
                    "user_id": user_id,
                    "process_id": process_id,
                    "process_name": process_name,
                    "config_type": config_type,
                    "eval_id": object_id,
                    "metric_id": metric_id
                }
            )

            if existing_document:
                # Update the existing document
                self.metrics_collection.update_one(
                    {
                        "user_id": user_id,
                        "process_id": process_id,
                        "config_type": config_type,
                        "eval_id": object_id,
                        "metric_id": metric_id
                    },
                    {
                        "$push": {
                            "models": {
                                "model_id": model_id,
                                "metrics_results": metrics_results
                            }
                        },
                        "$set": {
                            "timestamp": current_timestamp
                        }
                    }
                )
            else:
                # Create a new document
                self.metrics_collection.insert_one(
                    {
                        "user_id": user_id,
                        "process_id": process_id,
                        "process_name": process_name,
                        "config_type": config_type,
                        "eval_id": object_id,
                        "metric_id": metric_id,
                        "timestamp": current_timestamp,
                        "ranges": metric_ranges,
                        "models": [
                            {
                                "model_id": model_id,
                                "metrics_results": metrics_results
                            }
                        ]
                    }
                )
    async def update_metric_overall_status(self, process_id: str, metric_id: str, overall_status: str):
    
        metric =self.status_collection.update_one(
            {
                "process_id": process_id,  # Match the process
                "metrics.metric_id": metric_id  # Match the specific metric in the array
            },
            {
                "$set": {
                    "metrics.$.metric_overall_status": overall_status  # Update the matched array element
                }
            }
        )
    async def get_process_results(self, user_id: str, page: int, page_size: int):
        results = []
        total_count = 0

        for orgId in self.orgId:
            organizationDB = OrganizationDataBase(orgId)

            # Calculate skip value for pagination
            skip = (page - 1) * page_size

            # Fetch documents for the specific user_id from the organization’s config collection
            cursor = organizationDB.config_collection.find({"user_id": user_id}).sort("timestamp", -1).skip(skip).limit(page_size)
            for document in cursor:
                process_id = document.get("process_id")
                # Fetch the overall_status for the process_id from the status_collection
                status_document = organizationDB.status_collection.find_one({"process_id": str(process_id)})
                overall_status = status_document.get("overall_status") if status_document else None
                
                # Append the task details
                results.append({
                    "process_id": process_id,
                    "process_name": document.get("process_name"),
                    "model_id": document.get("model_id"),
                    "model_name": document.get("model_name"),
                    "payload_path": document.get("payload_file_path"),
                    "timestamp": document.get("timestamp"),
                    "overall_status": overall_status,
                    "organization_id": orgId
                })
            # Fetch the total count of documents for this user_id in the organization
            org_count = organizationDB.config_collection.count_documents({"user_id": user_id})
            total_count += org_count  # Sum up counts across all organizations

        # Calculate total pages based on aggregated count
        total_pages = (total_count + page_size - 1) // page_size

        # Return paginated results and metadata
        return results, total_count

    async def get_mongo_handler(service: str, org_id: str):
        if service == "evaluation":
            return MongoDBHandler(eval_config, org_id)  # Evaluation-specific handler
        elif service == "benchmarking":
            return MongoDBHandler(bench_config, org_id)  # Benchmarking-specific handler
        else:
            raise HTTPException(status_code=400, detail="Invalid service")
        
    def getRoleInfo(self, roleId):
        try:
            if self.organizationDB is None:
                logging.error("Organization database is not initialized.")
                return None, status.HTTP_500_INTERNAL_SERVER_ERROR
            role = self.organizationDB["roles"].find_one({"_id": ObjectId(roleId)},{"createdBy":0,"spaceIds":0})
            if role:
                role["roleId"]= str(role["_id"])
                del role["_id"]
                return role, status.HTTP_200_OK
            else:
                logging.info("role not found.")
                return [], status.HTTP_404_NOT_FOUND
        except Exception as e:
            logging.error(f"Error while retrieving roleInfo: {e}")
            return [], status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def getTaskInfo(self,taskId):
        try:
            task = self.organizationDB["tasks"].find_one({"_id":ObjectId(taskId)}, {"roleIds": 0, "createdBy":0})    
            if task:
                task["_id"]= str(task["_id"])
                return task, status.HTTP_200_OK
            else:
                return {}, status.HTTP_404_NOT_FOUND
        except Exception as e:
            logging.error(f"Error while retrieving tasks: {e}")
            return None, status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def getQuestionCards(self,taskId):
        try:
            questions = self.organizationDB["questions"].find({"taskId":taskId}, {"_id": 0,"question":1})  
            questions_list =list(questions)
            if len(questions_list) != 0:
                result = [object["question"] for object in questions_list]
                return result, status.HTTP_200_OK
            else:
                return [], status.HTTP_404_NOT_FOUND
        except Exception as e:
            logging.error(f"Error while retrieving tasks: {e}")
            return None, status.HTTP_500_INTERNAL_SERVER_ERROR
        
        
    def checkJob(self, jobId: str):
        try:
            # Check if spaceId is a string
            if not isinstance(jobId, str):
                return status.HTTP_400_BAD_REQUEST

            job = self.organizationDB["schedulerJobs"].find_one({"jobId": jobId}, {"_id": 0,"createdBy":0})
            if job:
                return status.HTTP_200_OK, job
            else:
                return status.HTTP_404_NOT_FOUND, None
        except Exception as e:
            # Log and handle unexpected errors
            logging.error(f"Error while checking Job for JobId {jobId}: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR, None
        
    def createJob(self, data: dict):
        try:
            if self.organizationDB is None:
                logging.error("Organization database is not initialized.")
                return status.HTTP_500_INTERNAL_SERVER_ERROR
            
            # Check if spaceName already exists
            existing_job_name = self.organizationDB["schedulerJobs"].find_one({"name": data["name"]})
            if existing_job_name:
                logging.error("Job Name Already Exists")
                return status.HTTP_409_CONFLICT
            
            data = {
                "jobId": data["jobId"],
                "job":data["job"],
                "name": data["name"],
                "config": data["config"],
                "interval": data["interval"],
                "prev_job":[],
                "next_job":data["time"],
                "createdBy": data["userId"]
            }
            # Insert the new space data into the database
            self.organizationDB["schedulerJobs"].insert_one(data)
            logging.info(f"job {data['name']} created successfully ")
            return status.HTTP_200_OK
        except Exception as e:
            logging.error(f"Error while creating job: {e}")
            print(f"Error while creating job: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def updateJob(self, data: dict, id=None):
        try:
            if self.organizationDB is None:
                logging.error("Organization database is not initialized.")
                return status.HTTP_500_INTERNAL_SERVER_ERROR
            # Check if spaceName already exists
            schedulerTask = self.organizationDB["schedulerJobs"].find_one({"jobId": data["jobId"]})
            if not schedulerTask:
                logging.error("Job Not found")
                return status.HTTP_404_NOT_FOUND
            updated_data = {}
            if id:
                updated_data["job"] = id
            updated_data["prev_job"] = schedulerTask["prev_job"]
            prev_job = schedulerTask["next_job"]
            next_job = prev_job + data["seconds"]
            updated_data["prev_job"].insert(0,prev_job)
            updated_data["next_job"] = next_job
            result = self.organizationDB["schedulerJobs"].update_one({"jobId":data['jobId']},{"$set": {**updated_data}})
            if result.matched_count==1:
                return status.HTTP_200_OK
            else:
                return status.HTTP_422_UNPROCESSABLE_ENTITY          
        except Exception as e:
            logging.error(f"Error while updating job: {e}")
            print(f"Error while updating job: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def deleteJob(self, jobId: str):
        try:
            # Check if spaceId is a string
            if not isinstance(jobId, str):
                return status.HTTP_400_BAD_REQUEST

            result = self.organizationDB["schedulerJobs"].delete_one({"jobId": jobId})
            if result.deleted_count==1:
                return status.HTTP_200_OK
            else:
                return status.HTTP_422_UNPROCESSABLE_ENTITY
        except Exception as e:
            # Log and handle unexpected errors
            logging.error(f"Error while deleting Job for JobId {jobId}: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def getAllJobs(self, type = None ,info = None):
        try:
            if self.organizationDB is None:
                logging.error("Organization database is not initialized.")
                return None, status.HTTP_500_INTERNAL_SERVER_ERROR
            if type:
                today_epoch = info["today_epoch"]
                tomorrow_epoch = info["tomorrow_epoch"]
                jobs_list = list(self.organizationDB["schedulerJobs"].find({"next_job":{ "$lt": tomorrow_epoch}}, {"_id": 0,"createdBy":0}))
            else:
                jobs_list = list(self.organizationDB["schedulerJobs"].find({}, {"_id": 0,"createdBy":0}))
            if len(jobs_list) > 0:
                return jobs_list
            else:
                logging.info("No jobs found for this Org.")
                return None
        except Exception as e:
            logging.error(f"Error while retrieving jobs: {e}")
            return None
        
  
    
    def get_ingestconfig(self):
        try:
            if not self.orgId:
                return status.HTTP_400_BAD_REQUEST, False, "Missing 'orgId' in request data"

            # Query the collection
            ingests = self.ingest_configuration.find(
                {},  # Optionally add {"orgId": self.orgId} to filter
                {"configuration_name": 1, "_id": 1}
            ).to_list(length=100)

            print(f"The ingest configs are: {ingests}")
            logger.info(f"The ingest configs are: {ingests}")

            if not ingests:
                logger.warning(f"No ingest found for orgId {self.orgId}")
                return [], 404

            # Serialize ObjectId to str
            ingests = [
                {k: (str(v) if isinstance(v, ObjectId) else v) for k, v in ingest.items()}
                for ingest in ingests
            ]

            return ingests, 200

        except Exception as e:
            logger.error(f"Error fetching ingest configs: {e}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"Database error: {str(e)}"
            }
            
    def add_ingestconfig(self, data):
        try:
            # Check for duplicate configuration_name
            existing = self.ingest_configuration.find_one({
                "configuration_name": data.get("configuration_name")
            })

            if existing:
                logger.warning(f"Duplicate config name found: {data.get('configuration_name')}")
                return {
                    "status_code": status.HTTP_409_CONFLICT,
                    "detail": f"Configuration '{data.get('configuration_name')}' already exists."
                }

            # Insert the document
            result = self.ingest_configuration.insert_one(data)

            if result.inserted_id:
                logger.info(f"Successfully added ingest config: {str(result.inserted_id)}")
                return {
                    "status_code": status.HTTP_201_CREATED,
                    "detail": "Ingest config added successfully.",
                }
            else:
                logger.warning("Insert operation did not return an inserted_id.")
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Insert failed with unknown reason."
                }

        except Exception as e:
            logger.error(f"Error adding ingest config: {e}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"Database error: {str(e)}"
            }      
            
    # in organizationDataBase.py

    def get_embedding_models(self):
        try:
            if not self.orgId:
                return status.HTTP_400_BAD_REQUEST, False, "Missing 'orgId'"

            models = self.embedding_models.find({}, {"tags": 0}).to_list(length=100)
            if not models:
                return [], 404

            models = [
                {k: (str(v) if isinstance(v, ObjectId) else v) for k, v in model.items()}
                for model in models
            ]
            return models, 200

        except Exception as e:
            logger.error(f"Error fetching embedding models: {e}")
            return {"status_code": status.HTTP_500_INTERNAL_SERVER_ERROR, "detail": str(e)}


    def get_splitter_config(self):
        try:
            if not self.orgId:
                return status.HTTP_400_BAD_REQUEST, False, "Missing 'orgId'"

            splitters = self.splitter_config.find(
                {},
            ).to_list(length=100)

            if not splitters:
                return [], 404

            splitters = [
                {k: (str(v) if isinstance(v, ObjectId) else v) for k, v in s.items()}
                for s in splitters
            ]
            return splitters, 200

        except Exception as e:
            logger.error(f"Error fetching splitter config: {e}")
            return {"status_code": status.HTTP_500_INTERNAL_SERVER_ERROR, "detail": str(e)}


    def get_vector_config(self):
        try:
            if not self.orgId:
                return status.HTTP_400_BAD_REQUEST, False, "Missing 'orgId'"

            vectors = self.vector_config.find(
                {},
            ).to_list(length=100)

            if not vectors:
                return [], 404

            vectors = [
                {k: (str(v) if isinstance(v, ObjectId) else v) for k, v in vconfig.items()}
                for vconfig in vectors
            ]
            return vectors, 200

        except Exception as e:
            logger.error(f"Error fetching vector config: {e}")
            return {"status_code": status.HTTP_500_INTERNAL_SERVER_ERROR, "detail": str(e)}
        
    def getLangflowUrl(self, deployId: str):
        try:
            result = self.organizationDB["DeploymentConfig"].find_one({"_id": ObjectId(deployId)})
            
            if result and "langflow_url" in result:
                return result["langflow_url"]
            else:
                return None

        except Exception as e:
            logging.error(f"Error fetching langflow_url for deployId {deployId}: {e}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": "Internal server error"
            }

        
