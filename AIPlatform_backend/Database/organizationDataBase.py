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
# from Database.applicationDataBase import ApplicationDataBase
from db_config import config, finetuning_config

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
            self.status_collection = self.organizationDB[finetuning_config['status_collection']]
            self.finetune_configCollection = self.organizationDB[finetuning_config['finetune_config']]
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
                result = [{"taskName": task["taskName"], "taskId": str(task["_id"]),"taskDescription":str(task["description"])} for task in tasks_list]
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
                result = [{"taskName": task["taskName"], "taskId": str(task["_id"]),"description":str(task["description"])} for task in tasks_list]
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