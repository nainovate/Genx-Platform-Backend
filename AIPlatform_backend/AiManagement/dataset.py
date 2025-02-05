from fastapi import status
import logging
from pymongo import DESCENDING
from datetime import datetime
import os
import random
from fastapi import HTTPException,status
from Database.applicationDataBase import ApplicationDataBase
from Database.organizationDataBase import OrganizationDataBase




class dataset:
    def __init__(self, role: dict, userId: str,orgIds:list):
        self.role = role
        self.userId = userId
        

    def add_dataset(self, data: dict):
        try:
            if not data or not isinstance(data, dict):
                logging.error("Empty or invalid data received.")
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Request data cannot be empty",
                }


            # Check for empty values in the data
            empty_fields = [key for key, value in data.items() if not value]
            
            if empty_fields:
                logging.error(f"Empty values found in fields: {', '.join(empty_fields)}")
                return {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "detail": f"The following fields have empty values: {', '.join(empty_fields)}. Please provide valid data for these fields.",
                    }

            required_fields = ["path","clientApiKey", "datasetContent","dataset_name"]
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                logging.error(f"Missing required fields: {', '.join(missing_fields)}")
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": f"Missing required fields: {', '.join(missing_fields)}."
                }
            client_api_key = data["clientApiKey"]
            parsed_content = data["datasetContent"]
            path = data["path"]
            orgId = data["orgId"]
            dataset_type = data["dataset_name"]
            document = {
                "clientApiKey": client_api_key,
                "datasetContent": [qa_item for qa_item in parsed_content],
                "path": path,
                "dataset_name" : dataset_type
            }
            organizationDB = OrganizationDataBase(orgId)
            # Check if organizationDB is initialized successfully
            if organizationDB.status_code != 200:
                return {
                    "status_code": organizationDB.status_code,
                    "detail": "Error initializing the organization database"
                }
            status_code, response = organizationDB.insertdataset(document)
            if response["success"]:
                return {
                    "status_code": status.HTTP_200_OK,
                    "detail": f"Dataset added successfully with ID: {response['dataset_id']}",
                }
            else:
                return {
                    "status_code": status_code,
                    "detail": response["error"],
                }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to add dataset due to an unexpected error: {str(e)}",
            )
            


        

    def generate_id(self,length):
        result = ''
        characters = '0123456789'
        for i in range(length):
            result += random.choice(characters)
        return result
    
    def generate_timestamp(self):
        return str(int(datetime.utcnow().timestamp()))

    def get_dataset_Details(self,data):
        """
        Fetches the datasets data from the database based on the provided request data.

        :param data: Data containing filters or attributes for querying datasets.
        :return: A dictionary containing the status code and additional details.
        """
        try:


            orgId = data["orgId"]
            organizationDB = OrganizationDataBase(orgId)
            # Check if organizationDB is initialized successfully
            if organizationDB.status_code != 200:
                return {
                    "status_code": organizationDB.status_code,
                    "detail": "Error initializing the organization database"
                }
            # Fetch dataset details
            result = organizationDB.dataset_details()

            # Ensure response is structured correctly
            if not result or not isinstance(result, dict) or "success" not in result:
                logging.error("Invalid response structure from dataset_details method.")
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Unexpected response structure from database query."
                }

            # Handle when no data is found
            if not result["success"] or not result.get("data"):
                logging.warning("No datasets found in the database.")
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "No datasets found in the database."
                }

            # Successful data retrieval
            logging.info(f"Successfully retrieved {len(result['data'])} datasets from the database.")
            return {
                "status_code": status.HTTP_200_OK,
                "detail": "Datasets retrieved successfully.",
                "data": result["data"]
            }

        except ConnectionError as e:
            logging.error(f"Database connection error: {e}")
            return {
                "status_code": status.HTTP_503_SERVICE_UNAVAILABLE,
                "detail": f"Database connection failed: {str(e)}"
            }

        except KeyError as e:
            logging.error(f"KeyError while processing database data: {e}")
            return {
                "status_code": status.HTTP_400_BAD_REQUEST,
                "detail": f"Malformed request data: Missing key {str(e)}"
            }

        except Exception as e:
            logging.error(f"Unexpected error occurred: {e}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"An unexpected error occurred: {str(e)}"
            }


 
    

    def deletedataset(self, data: dict):
        """
        Deletes dataset_Id from the database.

        :param data: Dictionary containing payload data, including required fields.
        :return: A dictionary containing the status code and additional details.
        """
        try:
            if not data or not isinstance(data, dict):
                logging.error("Empty or invalid data received.")
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Request data cannot be empty",
                }
            required_fields = ["dataset_Ids","clientApiKey","orgId"]
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                logging.error(f"Missing required fields: {', '.join(missing_fields)}")
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": f"Missing required fields: {', '.join(missing_fields)}."
                }

            # Check for empty values in the data
            empty_fields = [key for key, value in data.items() if not value]
            
            if empty_fields:
                logging.error(f"Empty values found in fields: {', '.join(empty_fields)}")
                return {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "detail": f"The following fields have empty values: {', '.join(empty_fields)}. Please provide valid data for these fields.",
                    }

            orgId = data["orgId"]
            organizationDB = OrganizationDataBase(orgId)
            # Check if organizationDB is initialized successfully
            if organizationDB.status_code != 200:
                return {
                    "status_code": organizationDB.status_code,
                    "detail": "Error initializing the organization database"
                }
            # Call the database layer to delete the prompt
            result =  organizationDB.delete_dataset(data)

            # Handle cases based on the result
            if result["status_code"] == 404:
                logging.warning("No dataset found matching the provided criteria.")
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "No datasets found matching the provided datasetID {dataset}. They may already be deleted or never existed."
                }

            if result["status_code"] == 200 and result["deleted_count"] == 0:
                logging.warning("datasets were already deleted.")
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "The specified dataset were already deleted or not found."
                }

            if result["status_code"] == 200 and result["deleted_count"] > 0:
                logging.info(f"Deleted {result['deleted_count']} dataset_Id(s).")
                return {
                    "status_code": status.HTTP_200_OK,
                    "detail": f"Successfully deleted {result['deleted_count']} dataset_Id(s)."
                }

            # Handle unexpected server error from the database layer
            if result["status_code"] == 500:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": result.get("detail", "An unexpected server error occurred.")
                }

        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": "An unexpected server error occurred. Please try again later or contact support."
            }
    




    