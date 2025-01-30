from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import status
import logging
from pymongo import DESCENDING
from db_config import finetuning_config
from datetime import datetime
import os
import random
from fastapi import HTTPException,status





class dataset:
    def __init__(self, role: dict, userId: str):
        self.role = role
        self.userId = userId
        self.client = AsyncIOMotorClient(finetuning_config['MONGO_URI'])
        self.db = self.client[finetuning_config['DB_NAME']]
        self.response = self.db[finetuning_config['response']]
        self.dataset_collection = self.db[finetuning_config['dataset_collection']]
        self.status_collection = self.db[finetuning_config['status_collection']]
        self.finetune_config = self.db[finetuning_config['finetune_config']]

    async def add_dataset(self, data: dict):
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

            required_fields = ["path","clientApiKey", "datasetContent","dataset_type"]
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
            dataset_type = data["dataset_type"]
            data_dict = {
                "clientApiKey": client_api_key,
                "datasetContent": [qa_item for qa_item in parsed_content],
                "path": path,
                "dataset_type" : dataset_type
            }

            status_code, response = await self.insertdataset(data_dict)
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
            

    async def insertdataset(self, document):
        try:
            if not self.client:
                raise Exception("Database client is not connected.")
            
            client_api_key = document.get("clientApiKey")
            dataset_content = document.get("datasetContent")
            path = document.get("path")
            dataset_type = document.get("dataset_type")

            if not client_api_key or not dataset_content or not path or not dataset_type:
                missing_fields = [
                    field for field in ["clientApiKey", "datasetContent", "path","dataset_type"]
                    if not document.get(field)
                ]
                return(f"statuscode:422, detail:Missing required fields: {', '.join(missing_fields)}")


            if not os.path.exists(path):
                raise FileNotFoundError(f"Path does not exist: {path}")
            if not os.access(path, os.R_OK):
                raise PermissionError(f"Path is not readable: {path}")

            dataset_id = self.generate_id(4)
            timestamp = self.generate_timestamp()
            payload_document = {
                "type": dataset_type,
                "dataset_id": dataset_id,
                "clientApiKey": client_api_key,
                "dataset_path": path,
                "dataset": dataset_content,
                "timestamp": timestamp,
                
            }

            insert_result = await self.dataset_collection.insert_one(payload_document)
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
    
    def generate_timestamp(self):
        return str(int(datetime.utcnow().timestamp()))

    async def get_dataset_Details(self):
        """
        Fetches the datasets data from the database based on the provided request data.

        :param data: Data containing filters or attributes for querying datasets.
        :return: A dictionary containing the status code and additional details.
        """
        try:
            
            # Fetch dataset details
            result = await self.dataset_details()

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


    async def dataset_details(self):
        """
        Fetches datasets details from the MongoDB collection for the given organisation.

        :return: Dictionary containing success status and dataset details or an error message.
        """
        try:
            # Query the collection for dataset details, excluding the "_id" field
            datasets = await self.dataset_collection.find({}, {"_id": 0, "dataset": 0}).sort("timestamp", DESCENDING).to_list(length=None)

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