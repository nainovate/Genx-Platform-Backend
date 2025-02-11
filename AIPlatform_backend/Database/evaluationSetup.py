from datetime import datetime
import json
import logging
from fastapi import HTTPException
from flask import request
from pymongo import MongoClient, UpdateOne
from motor.motor_asyncio import AsyncIOMotorClient
from utils import StatusRecord
from db_config import bench_config, config, eval_config

logger = logging.getLogger(__name__)
mongo_ip = config['mongoip']
mongo_port = config['mongoport']
class MongoDBHandler:
    def __init__(self, config, org_id: str):
        # Initialize the organization database first
        # self.org_db = OrganizationDataBase(org_id)
        db_uri = f"mongodb://{mongo_ip}:{mongo_port}/"
        self.client = MongoClient(db_uri)
        self.orgIds = org_id
        # Now use the organization's database for evaluation collections
        #self.db = self.client[config['DB_NAME']]
        self.organizationDB = self._get_organization_db(org_id)
        self.results_collection = self.organizationDB[config['RESULTS_COLLECTION']]
        self.status_collection = self.organizationDB[config['STATUS_COLLECTION']]
        self.config_collection = self.organizationDB[config['CONFIG_COLLECTION']]
        self.metrics_collection = self.organizationDB[config['METRICS_COLLECTION']]
        self.connect()
    def connect(self):
        """Establish a connection to the MongoDB server."""
        try:
            self.client = self.client
            self.db = self.db
        except Exception as e:
            logger.error(f"An error occurred while connecting to MongoDB: {e}")
            if self.client:
                self.client.close()

    def _get_organization_db(self, orgId):
        try:
            if self.client is None:
                logging.error("MongoClient is not initialized.")
                self.status_code = 500
                return None
            
            # Check if the database already exists
            existing_dbs = self.client.list_database_names()
            if orgId in existing_dbs:
                logging.info(f"Database '{orgId}' already exists.")
                return self.client[orgId]

            # If the database does not exist, create it by accessing it
            logging.info(f"Creating new database '{orgId}'.")
            org_db = self.client[orgId]
            
            return org_db
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            self.status_code = 500
            return None
    async def get_mongo_handler(service: str, org_id: str):
        if service == "evaluation":
            return MongoDBHandler(eval_config, org_id)  # Evaluation-specific handler
        elif service == "benchmarking":
            return MongoDBHandler(bench_config, org_id)  # Benchmarking-specific handler
        else:
            raise HTTPException(status_code=400, detail="Invalid service")

    

    
    
    async def update_model_status(self, process_id: str, model_id: str, new_status: str, overall_status: str):
        await self.status_collection.update_one(
            {
                "process_id": process_id,  # Find the process by its ID
                "models.model_id": model_id  # Match the specific model within the array
            },
            
            {
                "$set": {
                    "models.$.status": new_status,  # Update the status of the matched model
                    "overall_status": overall_status
                }
            }
        )
    
    
    


    async def update_metric_status(self, process_id: str, model_id: str, new_status: str, overall_status: str):
        await self.status_collection.update_one(
            {
                "process_id": process_id,  # Find the process by its ID
                "metrics.models.model_id": model_id  # Match the specific model within the models array by model_id
            },
            {
                "$set": {
                    "models.$.status": new_status,  # Update the status of the matched model
                    "metric_overall_status": overall_status  # Update the overall status for the metric
                }
            }
        )

    async def update_overall_status(self, process_id: str, overall_status: str):
        """Update the status of a specific model within a process in the database."""
        
        await self.status_collection.update_one(
            {
                "process_id": process_id,  # Find the process by its ID
            },
            {
                "$set": {
                    "overall_status": overall_status
                }
            }
        )
    
    async def update_metric_ranges(self, metric_id, metric_name, new_ranges):
        try:
            from Database.organizationDataBase import OrganizationDataBase
            for orgId in self.orgIds:
                organizationDB = OrganizationDataBase(orgId)

                # Find the document with the provided metric_id in the organization's metrics collection
                document = await organizationDB.metrics_collection.find_one({"metric_id": metric_id})

                if document:
                    # Check if the provided metric_name exists in 'ranges'
                    if metric_name in document.get("ranges", {}):
                        # Update the range value for the given metric_name
                        document["ranges"][metric_name] = new_ranges

                        # Update the document in the collection
                        result = await organizationDB.metrics_collection.update_one(
                            {"metric_id": metric_id},
                            {"$set": {"ranges": document["ranges"]}}
                        )

                        # Return the number of modified documents and organization ID
                        return {"modified_count": result.modified_count, "organization_id": orgId}

            # If the metric_id is not found in any organization, raise 404 error
            raise HTTPException(status_code=404, detail="Metric ID not found in any organization.")

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating metric ranges: {e}")
        

    
    async def fetch_metrics_by_id(self, metric_id: str):
        try:
            from Database.organizationDataBase import OrganizationDataBase
            for orgId in self.orgIds:
                organizationDB = OrganizationDataBase(orgId)

                # Search for the metric_id in the organization's metrics collection
                document = await organizationDB.metrics_collection.find_one({"metric_id": metric_id})

                if document:
                    return {
                        "organization_id": orgId,  # Include organization ID
                        "ranges": document.get("ranges", {}),  # Common ranges
                        "models": [
                            {
                                "model_id": model["model_id"],
                                "metrics_results": model["metrics_results"]
                            }
                            for model in document.get("models", [])
                        ]
                    }

            # If no document is found across all organizations, raise 404 error
            raise HTTPException(status_code=404, detail="Metric ID not found in any organization.")

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving metric data: {e}")

    
    async def update_model_status_to_cancelled(self, process_id):
        
        # Fetch the document by process_id
        document = await self.get_status_document_by_process_id(process_id)
        if not document:
            raise HTTPException(status_code=404, detail="Process not found")

        # Prepare the updates for models and overall status
        updates = []
        overall_status_updated = False

        for model in document['models']:
            if model['status'] != "Completed":
                # Prepare the update operation to change status to "Cancelled"
                updates.append(
                    UpdateOne(
                        {"_id": document["_id"], "models.model_id": model["model_id"]},
                        {"$set": {"models.$.status": "Cancelled"}}
                    )
                )
                overall_status_updated = True  # Set flag if we update any model

        # Update overall status if any model status was updated
        if overall_status_updated:
            updates.append(
                UpdateOne(
                    {"_id": document["_id"]},  # Target the same document
                    {"$set": {"overall_status": "Cancelled"}}
                )
            )

        # Execute the bulk updates if there are any changes
        if updates:
            result = await self.status_collection.bulk_write(updates)
              # Print update result for debugging

        return {"status": "All non-completed model statuses updated to 'Cancelled'"}

        
    async def insert_schedule_record(self, schedule_data: dict):
        # Check if a record with the given user_id exists
        existing_record = await self.config_collection.find_one({"user_id": schedule_data['user_id']})

        if existing_record:
            # If record exists, push the new schedule_time to the array
            await self.config_collection.update_one(
                {"user_id": schedule_data['user_id']},  # Filter to find the document by user_id
                {
                    "$push": {
                        "schedule_time": schedule_data['schedule_time']  # Append the new schedule_time to the array
                    }
                }
            )
        else:
            # If no existing record, insert a new record
            await self.config_collection.insert_one({
                "user_id": schedule_data['user_id'],        # Insert user_id
                "session_id": schedule_data['session_id'],  # Insert session_id
                "schedule_time": [schedule_data['schedule_time']]  # Store schedule_time as an array from the beginning
            })
    
    async def get_status_document_by_process_id(self, process_id: str):
        """Get the status of a specific process."""
        document = await self.status_collection.find_one({"process_id": process_id})
        return document if document else None

    async def get_model_statuses_by_process_id(self, process_id: str):
        # Fetch the document associated with the given process_id
        result = await self.status_collection.find_one({"process_id": process_id})
        overall_status = result.get("overall_status", None)
        if not result or "models" not in result:
            # If no result or models array not found, return an empty list
            return []

        # Extract model_id and status from the models array
        model_statuses = []
        for model in result["models"]:
            model_statuses.append({
                "model_id": model.get("model_id"),
                "status": model.get("status")
                #"overall_status": overall_status 
            })

        return model_statuses, overall_status
    async def get_config_document_by_process_id(self, process_id: str):
        """Get the status of a specific process."""
        document = await self.config_collection.find_one({"process_id": process_id})
        return document if document else None
    
    
    
    async def get_process_status(self, process_id: str):
        """Get the status of a specific process."""
        document = await self.status_collection.find_one({"process_id": process_id})
        return document.get("overall_status") if document else None
    
    
    async def get_process_status_by_userid(self, user_id: str):
        try:
            status_list = []
            from Database.organizationDataBase import OrganizationDataBase
            for orgId in self.orgIds:
                organizationDB = OrganizationDataBase(orgId)

                # Fetch all documents for the specific user_id from the organization's status collection
                documents = await organizationDB.status_collection.find(
                    {"user_id": user_id}  # Query by user_id
                ).sort("start_time", -1).to_list(length=None)  # Sort by start_time in descending order

                for doc in documents:
                    process_id = doc.get("process_id")
                    overall_status = doc.get("overall_status")
                    models = [
                        {
                            "model_id": model.get("model_id"),
                            "model_name": model.get("model_name"),
                            "status": model.get("status")
                        }
                        for model in doc.get("models", [])
                    ]

                    status_list.append({
                        "process_id": process_id,
                        "models": models,
                        "overall_status": overall_status,
                        "organization_id": orgId  # Include the organization ID
                    })

            # Return status list if available, otherwise raise 404
            if status_list:
                return {"statuses": status_list}

            raise HTTPException(status_code=404, detail="No status records found for the given user_id.")

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving process statuses: {e}")

    # async def get_process_results(self, process_id: str):
    #     document = await self.results_collection.find_one(
    #     {"process_id": process_id},
    #     projection={"models": 0, "user_id": 0,"_id":0}  # Exclude fields
    # )
    #     return document if document else None
    
    
    
    async def get_metric_results(self, user_id: str, page: int, page_size: int):
        try:
            skip = (page - 1) * page_size
            total_metrics = 0
            flattened_metrics = []
            from Database.organizationDataBase import OrganizationDataBase
            for orgId in self.orgIds:
                organizationDB = OrganizationDataBase(orgId)

                # Step 1: Calculate the total metrics count across all organizations
                async for document in organizationDB.status_collection.find(
                    {"user_id": user_id, "metrics": {"$exists": True, "$ne": []}}
                ):
                    if "metrics" in document:
                        total_metrics += len(document["metrics"])

                # Step 2: Fetch metrics with pagination logic
                cursor = organizationDB.status_collection.find(
                    {"user_id": user_id, "metrics": {"$exists": True, "$ne": []}}
                ).sort("timestamp", -1)

                async for document in cursor:
                    process_name = document.get("process_name")
                    timestamp = document.get("timestamp")

                    if "metrics" in document:
                        for metric in document["metrics"]:
                            metric_info = {
                                "metric_id": metric.get("metric_id"),
                                "models": metric.get("models"),
                                "overall_status": metric.get("metric_overall_status"),
                                "process_name": process_name,
                                "timestamp": timestamp,
                                "organization_id": orgId  # Include organization ID
                            }
                            flattened_metrics.append(metric_info)

                    if len(flattened_metrics) >= (skip + page_size):
                        break

            # Apply pagination to the flattened metrics
            paginated_metrics = flattened_metrics[skip:skip + page_size]

            # Return the paginated results and the total count of metric_id
            return paginated_metrics, total_metrics

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving metric results: {e}")


    async def get_results_by_process_id(self, process_id: str):
        try:
            models = None  # To store the models once found
            from Database.organizationDataBase import OrganizationDataBase
            for orgId in self.orgIds:
                organizationDB = OrganizationDataBase(orgId)

                # Find the document with the specified process_id in the organization's database
                document = await organizationDB.results_collection.find_one({"process_id": process_id})

                if document:
                    models = document.get("models")
                    if models is not None:
                        return models  # Return immediately when models are found

            # If no models are found across all organizations, raise a 404 error
            if models is None:
                raise HTTPException(status_code=404, detail="'models' object not found in any organization.")

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving results: {e}")
        

    async def get_results_file_path(self, process_id: str):
        """Get the file path for results."""
        document = await self.results_collection.find_one({"process_id": process_id})
        return document['results_path'] if document and 'results_path' in document else None
    
    async def get_results_by_model_id(self, process_id, model_id):
        # Query to find the document by process_id
        process_doc = await self.results_collection.find_one({"process_id": process_id})

        if process_doc:
            # Iterate through the models array to find the specific model_id
            for model in process_doc['models']:
                if model['model_id'] == model_id:
                    # Extract and return the results for the specific model_id
                    return model.get('results', None)
        
        # Return None if no document or results found
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.client:
            self.client.close()
