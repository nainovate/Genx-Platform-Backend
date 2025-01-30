from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import status
import logging
from pymongo import DESCENDING
from db_config import finetuning_config





class dataset:
    def __init__(self, role: dict, userId: str):
        self.role = role
        self.userId = userId
        self.client = AsyncIOMotorClient(finetuning_config['MONGO_URI'])
        self.db = self.client[finetuning_config['DB_NAME']]
        self.response = self.db[finetuning_config['response']]
        self.dataset_collection = self.db[finetuning_config['dataset_collection']]


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
