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





class Model:
    def __init__(self, role: dict, userId: str):
        self.role = role
        self.userId = userId
        self.applicationDB = initilizeApplicationDB()

    def addModel(self, data: dict):
        try:
            # Check if the incoming data is empty or invalid
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

            # Required fields check
            required_fields = ["engine", "clientApiKey", "modelId", "mode", "modelName", "modelOrganization", "modelType"]
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                logger.error(f"Missing required fields: {', '.join(missing_fields)}")
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": f"Missing required fields: {', '.join(missing_fields)}.",
                }

            # Validate the structure of additional fields (e.g., 'engine', 'mode', etc.)
            if not isinstance(data.get("engine"), str) or not isinstance(data.get("modelName"), str):
                logger.error("Invalid value types for 'engine' or 'modelName'. Expected strings.")
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "'engine' and 'modelName' should be of type string."
                }

            if data.get("mode") not in ["private", "cloud"]:
                logger.error("Invalid 'mode' field. Expected 'train' or 'predict'.")
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "'mode' must be either 'train' or 'predict'."
                }

            # Call the database layer to add the model
            status_code, success = self.applicationDB.add_model(data)
            if success:
                logger.info("Model added successfully.")
                return {
                    "status_code": status.HTTP_200_OK,
                    "detail": "Model added successfully.",
                }
            else:
                logger.error("Failed to add model.")
                return {
                    "status_code": status_code,
                    "detail": "Failed to add model. Please check the logs.",
                }

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add model due to an unexpected internal error.",
            )

        
    def getModeldetails(self, data: dict):
        try:
            # Validate input data
            if not data or not isinstance(data, dict):
                logging.error("Invalid or empty data received.")
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Request data must be a non-empty dictionary.",
                }

            # Check for empty fields in the data
            empty_fields = [key for key, value in data.items() if not value]
            if empty_fields:
                logging.error(f"Empty values in fields: {', '.join(empty_fields)}")
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": f"Fields with empty values: {', '.join(empty_fields)}. Please provide valid values.",
                }
            # Extract model type from data
            model = data.get("model")
            if not model or not isinstance(model, str):
                logging.error("Invalid or missing 'model' field in the request.")
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "The 'model' field is required ",
                }

            # Call the database function
            model_details = self.applicationDB.get_model_details(model)

            if model_details is None:
                logging.error(f"No records found for model: {model}")
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": f"No details found for model: {model}.",
                }

            # Return successful response
            logging.info(f"Model details fetched successfully for model: {model}.")
            return {
                "status_code": status.HTTP_200_OK,
                "detail": "Model details fetched successfully.",
                "data": model_details,
            }

        except HTTPException as http_exc:
            # Log and propagate HTTP errors
            logging.error(f"HTTPException occurred: {http_exc.detail}")
            raise http_exc

        except Exception as e:
            # Handle unexpected server-side errors
            logging.error(f"Unexpected error occurred: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred while processing the request.",
            )
        
    def deleteModel(self, data: dict):
        """
        Deletes model from the database.

        :param data: Dictionary containing model data, including required fields.
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
            required_fields = ["clientApiKey", "modelId","modelType"]
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
            result = self.applicationDB.delete_model(data)

            # Handle cases based on the result
            if result["status_code"] == 404:
                logger.warning("No models found matching the provided criteria.")
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "No models found matching the provided criteria. They may already be deleted or never existed."
                }

            if result["status_code"] == 200 and result["deleted_count"] == 0:
                logger.warning("models were already deleted.")
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "The specified models were already deleted or not found."
                }

            if result["status_code"] == 200 and result["deleted_count"] > 0:
                logger.info(f"Deleted {result['deleted_count']} models(s).")
                return {
                    "status_code": status.HTTP_200_OK,
                    "detail": f"Successfully deleted {result['deleted_count']} models(s)."
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
     