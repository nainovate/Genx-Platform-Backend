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


def generate_hierarchy_id():
    space_id = "".join(random.choice(string.ascii_lowercase) for _ in range(4))
    return space_id 





class Payload:
    def __init__(self, role: dict, userId: str):
        self.role = role
        self.userId = userId
        self.applicationDB = initilizeApplicationDB()  # Initialize the application database
    def addPayload(self, data: dict):
        
        try:
            # Check if the incoming data is empty
            
            if not data or not isinstance(data, dict):
                logger.error("Empty or invalid data received.")
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Request data cannot be empty",
                }


            # Check for empty values in the data
            empty_fields = [key for key, value in data.items() if not value]
            
            if empty_fields:
                logger.error(f"Empty values found in fields: {', '.join(empty_fields)}")
                return {
    "status_code": status.HTTP_400_BAD_REQUEST,
    "detail": f"The following fields have empty values: {', '.join(empty_fields)}. Please provide valid data for these fields.",
}

            required_fields = ["path","clientApiKey", "deployId","parsedContent"]
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                logger.error(f"Missing required fields: {', '.join(missing_fields)}")
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": f"Missing required fields: {', '.join(missing_fields)}."
                }
            # Call the database layer to add the prompt
            status_code, success = self.applicationDB.add_payload(data)

            if success:
                logger.info(f"Payload added successfully for userId {self.userId}")
                return {
                    "status_code": status.HTTP_200_OK,
                    "detail": "Payload added successfully",
                }
            else:
                logger.error(f"Failed to add payload for userId {self.userId}")
                # Map the database error code to a meaningful HTTP status
                if status_code == 400:
                    return {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "detail": "Invalid input or data",
                    }
                elif status_code == 500:
                    return {
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "detail": "Internal server error while adding payload",
                    }
                else:
                    return {
                        "status_code": status_code,
                        "detail": "Unknown error occurred",
                    }

        except HTTPException as http_exc:
            # Log and re-raise any explicit HTTP exceptions
            logger.error(f"HTTPException in addPayload: {http_exc.detail}")
            raise

        except Exception as e:
            # Log unexpected errors and raise an HTTPException
            logger.error(f"Unexpected error in addPayload method: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add payload due to an unexpected internal error",
            )
        
    def getPayloadDetails(self):
                """
                Fetches the Payloads data from the database.

                :return: A dictionary containing the status code and additional details.
                """
                try:
                    # Call the database layer method to fetch LLM prompts data
                    result = self.applicationDB.get_payload_details()

                    # Handle cases where no data is returned
                    if not result:
                        logger.warning("No payloads found in the database.")
                        return {
                            "status_code": status.HTTP_404_NOT_FOUND,
                            "detail": "No payloads found in the database."
                        }

                    # Successful data retrieval
                    logger.info(f"Successfully retrieved {len(result)} payloads from the database.")
                    return {
                        "status_code": status.HTTP_200_OK,
                        "detail": "payloads retrieved successfully.",
                        "data": result
                    }

                except ConnectionError as e:
                    # Handle connection errors
                    logger.error(f"Database connection error: {e}")
                    return {
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "detail": f"Database connection failed: {str(e)}"
                    }

                except KeyError as e:
                    # Handle missing or malformed keys
                    logger.error(f"KeyError while processing database data: {e}")
                    return {
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "detail": f"Malformed data structure: Missing key {str(e)}"
                    }

                except Exception as e:
                    # Handle any other unexpected errors
                    logger.error(f"Unexpected error occurred: {e}")
                    return {
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "detail": f"An unexpected error occurred: {str(e)}"
                    }
        
        

    def deletePayload(self, data: dict):
        """
        Deletes Payloads from the database.

        :param data: Dictionary containing payload data, including required fields.
        :return: A dictionary containing the status code and additional details.
        """
        try:
            # Validate the input data
            if not data or not isinstance(data, dict):
                logger.error("Empty or invalid data received.")
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Request data cannot be empty or invalid. Please provide a valid dictionary."
                }
            required_fields = ["clientApiKey", "payloadId"]
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                logger.error(f"Missing required fields: {', '.join(missing_fields)}")
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": f"Missing required fields: {', '.join(missing_fields)}."
                }


            # Check for empty fields
            empty_fields = [key for key, value in data.items() if not value]
            if empty_fields:
                logger.error(f"Empty values found in fields: {', '.join(empty_fields)}")
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": f"The following fields have empty values: {', '.join(empty_fields)}. Please provide valid data."
                }
            # Call the database layer to delete the prompt
            result = self.applicationDB.delete_payload(data)

            # Handle cases based on the result
            if result["status_code"] == 404:
                logger.warning("No payloads found matching the provided criteria.")
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "No payloads found matching the provided criteria. They may already be deleted or never existed."
                }

            if result["status_code"] == 200 and result["deleted_count"] == 0:
                logger.warning("Payloads were already deleted.")
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "The specified payloads were already deleted or not found."
                }

            if result["status_code"] == 200 and result["deleted_count"] > 0:
                logger.info(f"Deleted {result['deleted_count']} payload(s).")
                return {
                    "status_code": status.HTTP_200_OK,
                    "detail": f"Successfully deleted {result['deleted_count']} payload(s)."
                }

            # Handle unexpected server error from the database layer
            if result["status_code"] == 500:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": result.get("detail", "An unexpected server error occurred.")
                }

        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": "An unexpected server error occurred. Please try again later or contact support."
            }
