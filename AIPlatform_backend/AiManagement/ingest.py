import os
import logging
from fastapi import status
from Database.organizationDataBase import OrganizationDB  # Adjust based on your folder structure                   # Your MongoDB connection method


projectDirectory = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
logDir = os.path.join(projectDirectory, "logs")
logBackendDir = os.path.join(logDir, "backend")
logFilePath = os.path.join(logBackendDir, "logger.log")

logger = logging.getLogger(__name__)


class IngestManager:
    def __init__(self):
        self.organizationDB = OrganizationDB()

    async def fetch_config_details(self, data: dict):
        if "sessionId" not in data:
            logger.warning("Missing sessionId in request data")
            return {
                "status_code": status.HTTP_400_BAD_REQUEST,
                "detail": "Missing sessionId"
            }

        session_id = data["sessionId"]
        logger.info(f"Fetching config for sessionId: {session_id}")
        return self.organizationDB.get_config_by_session_id(session_id)

