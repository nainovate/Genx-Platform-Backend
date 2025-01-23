import os
import logging
from pymongo import UpdateOne
from pymongo.errors import BulkWriteError
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

class HierarchyDataBase:
    def __init__(self, hierarchyId: str):
        self.status_code = None  # Default status code

        try:
            db_uri = "mongodb://"+mongo_ip+":"+mongo_port+"/"
            self.client = MongoClient(db_uri)
            self.hierarchyId = hierarchyId
            self.hierarchyDB = self._get_hierarchy_db()
            self.status_code = 200
        except OperationFailure as op_err:
            logging.error(f"Error connecting to the database: {op_err}")
            self.status_code = 500
            return False, self.status_code
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            self.status_code = 500
            return False, self.status_code

    def _get_hierarchy_db(self):
        try:
            if self.client is None:
                logging.error("MongoClient is not initialized.")
                self.status_code = 500
                return None
            return self.client[self.hierarchyId]
        except OperationFailure as op_err:
            logging.error(f"Error accessing database: {op_err}")
            self.status_code = 500
            return None
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            self.status_code = 500
            return None
        
    def removeHierarchyDB(self):
        try:
            self.client.drop_database(self.hierarchyId)
            return status.HTTP_200_OK
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def addHierarchyConfig(self, data: dict):
        try:
            tabel = "config"
            bulk_operations = []

            agentId = data["agentId"]
            service_data = {service_name: details for service_name, details in data.items() if service_name != "agentId"}

            for service_name, details in service_data.items():
                update_operation = UpdateOne({"serviceName": service_name, "agentId": agentId}, {"$set": details}, upsert=True)
                bulk_operations.append(update_operation)


            if bulk_operations:
                self.hierarchyDB[tabel].bulk_write(bulk_operations)
            return status.HTTP_200_OK

        except BulkWriteError as bwe:
            logging.error(f"Bulk write error occurred: {bwe.details}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR

        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR

