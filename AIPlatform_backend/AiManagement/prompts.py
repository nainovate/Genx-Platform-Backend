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





class Prompts:
    def __init__(self, role: dict, userId: str,orgIds:list):
        self.role = role
        self.userId = userId
        self.orgIds = orgIds
    
    def addPrompt(self, data: dict):
        print("dataa  dghfd--",data)
        """
        Adds a prompt to the database.

        :param data: A dictionary containing the prompt details.
        :return: A dictionary containing the status code and additional details.
        """
        try:
            if not data or not isinstance(data, dict):
                logger.error("Empty or invalid data received.")
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Request data cannot be empty or invalid. Please provide valid data.",
                }

            # Define required keys
            required_keys = {
                "promptName", "taskType",
                "systemMessage", "aiMessage", "humanMessage", "inputData"  # Ensure inputData is included
            }

            # Check for missing keys (but allow empty values)
            missing_keys = required_keys - data.keys()
            if missing_keys:
                logger.error(f"Missing required keys: {', '.join(missing_keys)}")
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": f"Missing required keys: {', '.join(missing_keys)}. Please include them in your request.",
                }

            # Allow inputData to be empty, but check other required fields for missing values
            empty_fields = [
                key for key in required_keys
                if key not in {"inputData", "humanMessage", "aiMessage"} and not data.get(key)
            ] 
            if empty_fields:
                logger.error(f"Empty values found in fields: {', '.join(empty_fields)}")
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": f"The following fields have empty values: {', '.join(empty_fields)}. Please provide valid data for these fields.",
                }
            orgId = data["orgId"]
            print("org id", orgId)
            organizationDB = OrganizationDataBase(orgId)
            # Call the database layer to add the prompt
            status_code, success, detail_message = organizationDB.addPrompt(data)
            
            if success:
                return {
                    "status_code": status.HTTP_200_OK,
                    "detail": "Prompt added successfully",
                }
            else:
                return {
                    "status_code": status_code,
                    "detail": detail_message,
                }

        except HTTPException as http_exc:
            logger.error(f"HTTPException in addPrompt: {http_exc.detail}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error in addPrompt method: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add prompt due to an unexpected internal error",
            )

    def getPromptsData(self,):
        """
        Fetches the LLM Prompts data from the database.

        :return: A dictionary containing the status code and additional details.
        """
        try:

            result = []
            for org in self.orgIds:
           
                organizationDB = OrganizationDataBase(org)
                prompts, status_code = organizationDB.get_prompts_data()
                if prompts:
                    result.extend(prompts)
            
                # Handle cases where no data is returned
            if not result:
                logger.warning("No prompts found in the database.")
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "No LLM prompts found in the database."
                }

            # Successful data retrieval
            logger.info(f"Successfully retrieved {len(result)} prompts from the database.")
            return {
                "status_code": status.HTTP_200_OK,
                "detail": "LLM prompts retrieved successfully.",
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


    def updatePrompt(self, data: dict):
        """
        Fetches the LLM Prompts data from the database.

        :return: A dictionary containing the status code and additional details.
            """
        try:

                # Call the database layer method to fetch LLM prompts data
                if not data or not isinstance(data, dict):
                    logger.error("Empty or invalid data received.")
                    return {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "detail": "Request data cannot be empty",
                    }
                empty_fields = [key for key, value in data.items() if not value]
                if empty_fields:
                    logger.error(f"Empty values found in fields: {', '.join(empty_fields)}")
                    return {
        "status_code": status.HTTP_400_BAD_REQUEST,
        "detail": f"The following fields have empty values: {', '.join(empty_fields)}. Please provide valid data for these fields.",
    }

                result = self.applicationDB.update_prompt(data)

                # Handle cases where no data is returned
                if not result:
                    logger.warning("No prompts found in the database.")
                    return {
                        "status_code": status.HTTP_404_NOT_FOUND,
                        "detail": "No LLM prompts found in the database."
                    }

                # Successful data retrieval
                return {
                    "status_code": status.HTTP_200_OK,
                    "detail": "LLM prompt updated successfully."
                }

        except ValueError as ve:
                logger.error(f"Invalid input: {ve}")
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. Required fields are missing or incorrect."
                }

        except Exception as e:
                logger.error(f"An error occurred: {e}")
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "An error occurred while updating the LLM prompt."
                }

    def deletePrompt(self, data: dict):
        """
        Deletes LLM Prompts from the database.

        :param data: Dictionary containing prompt data, including required fields.
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

            # Validate required fields
            required_fields = ["clientApiKey", "promptId"]
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
            result = self.applicationDB.delete_prompt(data)

            # Handle cases based on the result
            if "status_code" not in result:
                logger.error("Unexpected response format from the database layer.")
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Unexpected server response. Please try again later."
                }

            if result["status_code"] == 404:
                logger.warning("No prompts found matching the provided criteria.")
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "No prompts found matching the provided criteria. They may already be deleted or never existed."
                }

            if result["status_code"] == 400:
                logger.warning("Invalid input detected.")
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Missing 'clientApiKey' or 'promptId'."
                }

            if result["status_code"] == 200:
                if result.get("deleted_count", 0) == 0:
                    logger.warning("Prompts were already deleted.")
                    return {
                        "status_code": status.HTTP_404_NOT_FOUND,
                        "detail": "The specified prompts were already deleted or not found."
                    }
                else:
                    logger.info(f"Deleted {result['deleted_count']} prompt(s).")
                    return {
                        "status_code": status.HTTP_200_OK,
                        "detail": f"Successfully deleted {result['deleted_count']} prompt(s)."
                    }

            # Handle unexpected server error from the database layer
            if result["status_code"] == 500:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": result.get("detail", "An unexpected server error occurred.")
                }

        except KeyError as e:
            logger.error(f"Key error: {e}")
            return {
                "status_code": status.HTTP_400_BAD_REQUEST,
                "detail": "Invalid input data. Please check the field names and try again."
            }
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": "An unexpected server error occurred. Please try again later or contact support."
            }
