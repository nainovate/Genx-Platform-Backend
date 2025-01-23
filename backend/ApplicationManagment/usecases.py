import os
import logging
import yaml
from fastapi import HTTPException, status
from Database.users import *
from Database.applicationSetup import *

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


def initilizeApplicationConfigDB():
    applicationDB = ApplicationSetup()
    return applicationDB

class UseCases:
    def __init__(self, userId: str, role: dict):
        self.userId = userId
        self.role = role
        self.applicationconfigDB = initilizeApplicationConfigDB()

    def getUseCases(self):
        try:
            if not "superadmin" in self.role:
                return {
                        "status_code": status.HTTP_401_UNAUTHORIZED, 
                        "detail": "Unauthorized Access"
                }
            usecases, status_code = self.applicationconfigDB.getUseCases()
            
            if status_code == status.HTTP_404_NOT_FOUND:
                return {
                        "status_code":status.HTTP_404_NOT_FOUND,
                        "detail":"No use cases found in application config database."
                }
            if not status_code == 200:
                return {
                        "status_code":status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "detail":"Internal server error occurred."
                }
            return {
                "status_code": status_code,
                "usecases": usecases
            }
        except Exception as e:
            logging.error(f"Error while retrieving use cases: {e}")
            return {
                "status_code":status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail":f"{e}"
            }

    def getUseCaseRoles(self, useCaseId: str):
        try:
            if not "admin" in self.role:
                return {
                        "status_code": status.HTTP_401_UNAUTHORIZED, 
                        "detail": "Unauthorized Access"
                }
            useCaseRoles, status_code = self.applicationconfigDB.getUseCaseRoles(useCaseId= useCaseId)
            if status_code == status.HTTP_404_NOT_FOUND:
                return status.HTTP_404_NOT_FOUND, None
            if not status_code == 200:
                return status.HTTP_500_INTERNAL_SERVER_ERROR, None
            else:
                return status.HTTP_200_OK, useCaseRoles
        except Exception as e:
            logging.error(f"Error while retrieving use cases: {e}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"{e}"
            }
        
    def getUseCaseName(self, useCaseId: str):
        try:
            # Validate input data
            if not isinstance(useCaseId, str):
                return None, status.HTTP_400_BAD_REQUEST
        
            useCaseName, status_code = self.applicationconfigDB.getUseCaseName(useCaseId= useCaseId)

            if status_code == 400:
                return status.HTTP_400_BAD_REQUEST
            
            if status_code == 404:
                return status.HTTP_404_NOT_FOUND, None
            
            if not status_code == 200:
                return status.HTTP_500_INTERNAL_SERVER_ERROR, None
            
            return status.HTTP_200_OK, useCaseName
        except Exception as e:
            logging.error(f"Error while fetching use case name for useCaseId {useCaseId}: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR, None