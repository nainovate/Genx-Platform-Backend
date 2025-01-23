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

class ApplicationSetup:
    def __init__(self,):
        self.status_code = None  # Default status code
        
        try:
            db_uri = "mongodb://"+mongo_ip+":"+mongo_port+"/"
            self.client = MongoClient(db_uri)
            self.applicationConfigDB = self._get_application_db()
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
            return self.client["applicationSetup"]
        except OperationFailure as op_err:
            logging.error(f"Error accessing database: {op_err}")
            self.status_code = 500
            return None
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            self.status_code = 500
            return None
        
    def initializeConfigData(self):
        try:
            if self.applicationConfigDB is None:
                logging.error("Application database is not initialized.")
                return False, 500
            
            config_collection = self.applicationConfigDB["config"]
            if "config" not in self.applicationConfigDB.list_collection_names():
                config_data = {
                    "maxOtpSendAttempts": 3,
                    "otpLockDurationMinutes": 2,
                    "maxOtpAttempts": 3,
                    "otpAttemptsDurationMinutes": 2,
                    "accessTokenExpireMinutes": 1,
                    "refreshTokenExpireDays": 7,
                    "secretKey": "BrilliusAI",
                    "userIdLength": 4,
                    "userIdChunkSize": 4
                }
                config_collection.insert_one(config_data)
                logging.info("Configuration data initialized successfully.")
                return True, 201
            else:
                logging.warning("Config data already exists in the collection.")
                return False, 409
        except Exception as e:
            logging.error(f"Error initializing config data: {e}")
            return False, 500

    def initializeUseCaseConfig(self):
        try:
            if self.applicationConfigDB is None:
                logging.error("Application database is not initialized.")
                return False, 500
            
            use_case_config_collection = self.applicationConfigDB["useCaseConfig"]
            if "useCaseConfig" not in self.applicationConfigDB.list_collection_names():
                use_case_config_data = {
                    "useCaseId": "GT1",
                    "useCaseName": "Training",
                    "useCaseConfig": {
                        "Audio": ["Assessment", "Practice"],
                        "Video": ["Assessment", "Practice"]
                    },
                    "useCaseRoles": {
                        "R1": "Traineer",
                        "R2": "Trainee"
                    }
                }
                use_case_config_collection.insert_one(use_case_config_data)
                logging.info("Use case config data initialized successfully.")
                return True, 201
            else:
                logging.warning("Use case config data already exists in the collection.")
                return False, 409
        except Exception as e:
            logging.error(f"Error initializing use case config data: {e}")
            return False, 500
    
    def getApplicationConfig(self):
        try:
            if self.applicationConfigDB is None:
                logging.error("Application database is not initialized.")
                return None, status.HTTP_500_INTERNAL_SERVER_ERROR

            config = self.applicationConfigDB["config"].find_one()

            if config:
                return config, status.HTTP_200_OK
            else:
                logging.error("No configuration found in the application database.")
                return None, status.HTTP_404_NOT_FOUND
        except Exception as e:
            logging.error(f"Error while retrieving application configuration: {e}")
            return None, status.HTTP_500_INTERNAL_SERVER_ERROR
        
    
    def getUseCases(self):
        try:
            if self.applicationConfigDB is None:
                logging.error("Application database is not initialized.")
                return None, status.HTTP_500_INTERNAL_SERVER_ERROR
            
            usecases_collection = self.applicationConfigDB["useCaseConfig"]
            
            if usecases_collection is None:
                logging.error("Use cases collection not found in application database.")
                return None, status.HTTP_500_INTERNAL_SERVER_ERROR

            usecases_list = usecases_collection.find({}, {"_id": 0, "useCaseConfig": 0, "useCaseRoles": 0})

            if usecases_list:
                usecases = {}
                for usecase in usecases_list:
                    usecases[usecase["useCaseId"]] = usecase["useCaseName"]
                return usecases, status.HTTP_200_OK
            else:
                logging.error("No use cases found in application database.")
                return None, status.HTTP_404_NOT_FOUND
        except Exception as e:
            logging.error(f"Error while retrieving application configuration: {e}")
            return None, status.HTTP_500_INTERNAL_SERVER_ERROR

    def getUseCaseRoles(self, useCaseId: str):
        try:
            if self.applicationConfigDB is None:
                logging.error("Application database is not initialized.")
                return None, status.HTTP_500_INTERNAL_SERVER_ERROR
            useCaseRoles = self.applicationConfigDB["useCaseConfig"].find_one({"useCaseId": useCaseId},{"_id":0,"useCaseConfig":0, "useCaseId":0, "useCaseName":0})
            if useCaseRoles:
                return useCaseRoles["useCaseRoles"], status.HTTP_200_OK
            else:
                logging.error("No use cases roles found in application database.")
                return None, status.HTTP_404_NOT_FOUND
        except Exception as e:
            logging.error(f"Error while retrieving application configuration: {e}")
            return None, status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def getUseCaseName(self, useCaseId: str):
        try:
            # Validate input data
            if not isinstance(useCaseId, str):
                return None, status.HTTP_400_BAD_REQUEST
            
            if self.applicationConfigDB is None:
                logging.error("Application configuration database is not initialized.")
                return None, status.HTTP_500_INTERNAL_SERVER_ERROR
            
            useCaseName = list(self.applicationConfigDB["useCaseConfig"].find({"useCaseId": useCaseId},{"_id":0,"useCaseConfig":0,"useCaseId":0,"useCaseRoles":0}))[0]

            if useCaseName:
                return useCaseName['useCaseName'], status.HTTP_200_OK
            else:
                logging.error(f"No use case name found for useCaseId: {useCaseId}.")
                return None, status.HTTP_404_NOT_FOUND
            
        except Exception as e:
            # Log and handle unexpected errors
            logging.error(f"Error while fetching use case name for useCaseId {useCaseId}: {e}")
            return None, status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def checkUseCases(self, useCaseId: str):
        try:
            # Check if spaceId is a string
            if not isinstance(useCaseId, str):
                return status.HTTP_400_BAD_REQUEST

            useCase = self.applicationConfigDB["useCaseConfig"].find_one({"useCaseId": useCaseId})

            if useCase:
                return status.HTTP_200_OK
            else:
                return status.HTTP_404_NOT_FOUND
            
        except Exception as e:
            # Log and handle unexpected errors
            logging.error(f"Error while checking usecase for usecase id {useCaseId}: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def getAgentIds(self, useCaseId: str, org: str, position: str):
        try:
            # First, get the agent IDs for the given use case
            agent_doc = self.applicationConfigDB["useCaseConfig"].find_one(
                {"useCaseId": useCaseId},
                {"_id": 0, "useCaseConfig": 0, "useCaseId": 0, "useCaseRoles": 0, "useCaseName": 0}
            )

            if not agent_doc or 'agents' not in agent_doc:
                logging.error(f"No agent IDs found for usecase ID: {useCaseId}")
                return None, status.HTTP_404_NOT_FOUND

            if position.lower() == "demo" and org.lower() == "demo":
                # Return all agents for this use case
                return agent_doc["agents"], status.HTTP_200_OK

            agents = {}
            for key, value in agent_doc["agents"].items():
                if org.lower() in value["org"].lower() and position.lower() in [pos.lower() for pos in value["position"]]:
                    agents[key] = value

            return agents, status.HTTP_200_OK
        except Exception as e:
            print(str(e))
            logging.error(f"Error while getting agentIds: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
