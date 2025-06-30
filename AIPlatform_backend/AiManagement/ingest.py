import logging
import random
import string

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


def generate_hierarchy_id():
    space_id = "".join(random.choice(string.ascii_lowercase) for _ in range(4))
    return space_id 



class IngestManager:
    def __init__(self, role: dict, userId: str,orgIds:list):
        self.role = role
        self.userId = userId
        self.orgIds = orgIds

    async def fetch_config_details(self):
        try:
            result = []
    
            for org in self.orgIds:
                print(f"Fetching config for org: {org}")
                organizationDB = OrganizationDataBase(org)
                configs, status_code = organizationDB.get_ingestconfig()

                if status_code == 200 and configs:
                    result.extend(configs)
                    logger.info(f"Configs retrieved for org: {org}")
                else:
                    logger.warning(f"No configs found for org: {org}")

            if not result:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "No config data found for any org"
                }

            return {
                "status_code": status.HTTP_200_OK,
                "detail": "Config data retrieved successfully",
                "data": result
            }

        except Exception as e:
            logger.error(f"Unexpected error during config fetch: {e}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"Error fetching config data: {str(e)}"
            }

