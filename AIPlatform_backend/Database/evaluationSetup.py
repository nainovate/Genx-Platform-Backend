from datetime import datetime
import json
import logging
from fastapi import HTTPException
from flask import request
from pymongo import MongoClient, UpdateOne
from motor.motor_asyncio import AsyncIOMotorClient
from utils import StatusRecord
from Database.organizationDataBase import OrganizationDataBase
from db_config import bench_config, eval_config

logger = logging.getLogger(__name__)

class MongoDBHandler:
    def __init__(self, config, org_id: str):
        # Initialize the organization database first
        # self.org_db = OrganizationDataBase(org_id)
        self.client = AsyncIOMotorClient(config['MONGO_URI'])
        # Now use the organization's database for evaluation collections
        self.db = self.client[config['DB_NAME']]
        self.results_collection = self.db[config['RESULTS_COLLECTION']]
        self.status_collection = self.db[config['STATUS_COLLECTION']]
        self.config_collection = self.db[config['CONFIG_COLLECTION']]
        self.metrics_collection = self.db[config['METRICS_COLLECTION']]
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

    
    async def get_mongo_handler(service: str, org_id: str):
        if service == "evaluation":
            return MongoDBHandler(eval_config, org_id)  # Evaluation-specific handler
        elif service == "benchmarking":
            return MongoDBHandler(bench_config, org_id)  # Benchmarking-specific handler
        else:
            raise HTTPException(status_code=400, detail="Invalid service")

    async def update_results_path(self, process_id, results_path):
        try:
            result = await self.results_collection.update_one(
                {"process_id": process_id,},
                {"$set": {"results_path": results_path}},
                upsert=True
            )
            if result.matched_count > 0:
                logger.info(f"Process {process_id} updated in DB")
            else:
                logger.info(f"Process {process_id} inserted in DB")
        except Exception as e:
            logger.error(f"An error occurred while inserting/updating data for process_id {process_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def update_status_record(self, status_record: dict):
    
        await self.status_collection.update_one(
            {"process_id": status_record["process_id"]},
            {
                "$set": {
                    "user_id": status_record["user_id"],
                    "process_name": status_record["process_name"],
                    "models": status_record["models"],  # Assuming models is already a list of dictionaries
                    "overall_status": status_record["overall_status"],
                    "start_time": status_record["start_time"],
                    "end_time": status_record.get("end_time", None)  # Ensure that end_time can be optional
                }
            },
            upsert=True
        )
    
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
    
    async def update_metric_model_status(self, process_id: str, model_id: str, new_status: str, metric_id: str, overall_status: str):
        # Check if the metric_id already exists in the metrics array
        existing_metric = await self.status_collection.find_one(
            {
                "process_id": process_id,
                "metrics.metric_id": metric_id
            },
            {"metrics.$": 1}  # Only fetch the specific metric array for efficiency
        )
        
        if existing_metric:
            # If the metric exists, update the existing model status in that metric
            await self.status_collection.update_one(
                {
                    "process_id": process_id,  # Match the process by ID
                    "metrics.metric_id": metric_id  # Match the specific metric by ID
                },
                {
                    "$set": {
                        "metrics.$.models.$[model].status": new_status,  # Update the model's status within the existing metric
                        "metrics.$.metric_overall_status": overall_status  # Update the overall status for the matched metric
                    }
                },
                array_filters=[
                    {"model.model_id": model_id}  # Filter for the correct model inside metrics' models
                ]
            )
        else:
            # If the metric does not exist, add a new metric to the metrics array
            new_metric = {
                "metric_id": metric_id,
                "models": [
                    {
                        "model_id": model_id,
                        "status": new_status  # Add the model status to the new metric
                    }
                ],
                "metric_overall_status": overall_status  # Add the overall status to the new metric
            }

            await self.status_collection.update_one(
                {
                    "process_id": process_id  # Match the process by ID
                },
                {
                    "$push": {
                        "metrics": new_metric  # Push the new metric to the metrics array
                    }
                }
            )


    async def update_metric_status_record(self, status_record: StatusRecord, process_name):
        # Prepare the metrics object to add to the database
        metrics_data = {
            "metric_id": status_record.metric_id,  # Add the metric_id
            "models": [model_status.dict() for model_status in status_record.models],  # Convert models to dictionaries
            "metric_overall_status": status_record.overall_status  # Add the overall_status
        }
        timestamp = int(datetime.utcnow().timestamp())
        # Ensure the metric_id does not already exist in the metrics array
        await self.status_collection.update_one(
            {
                "process_id": status_record.process_id,  # Match the process_id
                "metrics.metric_id": {"$ne": status_record.metric_id}  # Ensure the metric_id is not already in the array
            },
            {
                "$push": {
                    "metrics": metrics_data  # Add the new metric record to the array
                },
                "$set": {
                    "user_id": status_record.user_id,  # Update the user_id
                    "start_time": status_record.start_time,  # Update the start_time
                    "end_time": status_record.end_time,  # Update the end_time
                    "process_name": process_name,  # Add or update the process_name
                    "timestamp": timestamp  # Add or update the timestamp
                }
            },
            upsert=True  # Create the document if it does not exist
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
    async def update_metric_overall_status(self, process_id: str, metric_id: str, overall_status: str):
    
        await self.status_collection.update_one(
            {
                "process_id": process_id,  # Match the process
                "metrics.metric_id": metric_id  # Match the specific metric in the array
            },
            {
                "$set": {
                    "metrics.$.metric_overall_status": overall_status  # Update the matched array element
                }
            }
        )

    async def update_results_record(self, process_id: str,process_name: str, user_id: str, config_type: str, model_id: str,model_name:str, results: dict):
        """Update the status of a specific process in the database."""
        timestamp = datetime.utcnow()
        await self.results_collection.update_one(
                {"user_id": user_id, "process_id": process_id, "process_name": process_name, "config_type": config_type},
                {"$push": {"models": {"model_id": model_id, "model_name": model_name, "results": results}}},
                upsert=True
        )

    async def update_metric_ranges(self, metric_id, metric_name, new_ranges):
            # Find the document with the provided metric_id
            document = await self.metrics_collection.find_one({"metric_id": metric_id})
            if document:
                # Check if the provided metric_name matches any range field in the document
                if metric_name in document.get('ranges', {}):
                    # Update the ranges directly in the document at the root level
                    document['ranges'][metric_name] = new_ranges
                    
                    # After updating the ranges, update the document in the collection
                    result = await self.metrics_collection.update_one(
                        {"metric_id": metric_id},
                        {"$set": {"ranges": document['ranges']}}
                    )
                    # Return the number of modified documents (should be 1 if the document exists)
                    return result.modified_count
                else:
                    # If the metric_name doesn't exist in 'ranges', return None
                    return None
            else:
                # If the document is not found, return None
                return None
        # If no document is found with the provided metric_id
    

    async def update_metrics_results_record(
        self, process_id, user_id, config_type, object_id, metric_id, 
        process_name, model_id, metrics_results
        ):
            # Define the ranges for each metric
            metric_ranges = {
                "MRR": {
                    "Excellent": "0.8 - 1.0",
                    "Moderate": "0.5 - 0.8",
                    "Poor": "0 - 0.5"
                },
                "ROUGE_score": {
                    "ROUGE-1": {
                        "Excellent": "0.45 - 1.0",
                        "Moderate": "0.30 - 0.45",
                        "Poor": "0 - 0.30"
                    },
                    "ROUGE-2": {
                        "Excellent": "0.25 - 1.0",
                        "Moderate": "0.15 - 0.25",
                        "Poor": "0 - 0.15"
                    },
                    "ROUGE-L": {
                        "Excellent": "0.40 - 1.0",
                        "Moderate": "0.25 - 0.40",
                        "Poor": "0 - 0.25"
                    }
                },
                "BERT_score": {
                    "Excellent": "0.8 - 1.0",
                    "Moderate": "0.5 - 0.8",
                    "Poor": "0 - 0.5"
                }
            }

            # Format metrics_results to retain only the scores
            for metric, values in metrics_results.items():
                if metric == "ROUGE_score":
                    for rouge_type, rouge_score in values.items():
                        values[rouge_type] = rouge_score
                else:
                    metrics_results[metric] = values

            # Get the current timestamp as Unix time
            current_timestamp = int(datetime.utcnow().timestamp())

            # Check if the document exists for the given process_id and user_id
            existing_document = await self.metrics_collection.find_one(
                {
                    "user_id": user_id,
                    "process_id": process_id,
                    "process_name": process_name,
                    "config_type": config_type,
                    "eval_id": object_id,
                    "metric_id": metric_id
                }
            )

            if existing_document:
                # Update the existing document
                await self.metrics_collection.update_one(
                    {
                        "user_id": user_id,
                        "process_id": process_id,
                        "config_type": config_type,
                        "eval_id": object_id,
                        "metric_id": metric_id
                    },
                    {
                        "$push": {
                            "models": {
                                "model_id": model_id,
                                "metrics_results": metrics_results
                            }
                        },
                        "$set": {
                            "timestamp": current_timestamp
                        }
                    }
                )
            else:
                # Create a new document
                await self.metrics_collection.insert_one(
                    {
                        "user_id": user_id,
                        "process_id": process_id,
                        "process_name": process_name,
                        "config_type": config_type,
                        "eval_id": object_id,
                        "metric_id": metric_id,
                        "timestamp": current_timestamp,
                        "ranges": metric_ranges,
                        "models": [
                            {
                                "model_id": model_id,
                                "metrics_results": metrics_results
                            }
                        ]
                    }
                )
    async def fetch_metrics_by_id(self, metric_id: str):
        document = await self.metrics_collection.find_one({"metric_id": metric_id})
        if not document:
            raise HTTPException(status_code=404, detail="Metric ID not found")

        # Common ranges for all models
        ranges = document.get("ranges", {})
        
        # Return structure with common ranges and model results
        return {
            "ranges": ranges,
            "models": [{
                "model_id": model["model_id"],
                "metrics_results": model["metrics_results"]
            } for model in document.get("models", [])]
        }

    
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



    async def insert_config_record(self, config_data: dict):
        
        # Check if a record with the given user_id exists, and update it if found, else insert a new one
       # Insert a new record every time, without checking for an existing user_id
        await self.config_collection.insert_one({
            "user_id": config_data['user_id'],  # Set the user_id
            "process_id": config_data['process_id'],  # Set the process_id
            "process_name": config_data["process_name"],  # Set the process_name
            "model_id": config_data["model_id"],  # Set the model_id
            "model_name": config_data["model_name"],  # Set the model_name
            "payload_file_path": config_data["payload_file_path"],
            "timestamp": int(datetime.utcnow().timestamp())  # Set the payload_file_path
        })
        
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
    async def check_ongoing_task(self, user_id: str):
        """Check if the user already has an ongoing evaluation task."""
        return await self.status_collection.find_one({"user_id": user_id, "overall_status": "In Progress"}) is not None

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
    
    async def get_result_document_by_process_id(self, process_id: str):
        """Get the status of a specific process."""
        document = await self.results_collection.find_one({"process_id": process_id})
        return document if document else None
    
    async def get_process_status(self, process_id: str):
        """Get the status of a specific process."""
        document = await self.status_collection.find_one({"process_id": process_id})
        return document.get("overall_status") if document else None
    
    async def check_model_completed_status(self, process_id: str):
        # Fetch the existing record
        existing_record = await self.status_collection.find_one({"process_id": process_id})        
        if existing_record:
            # Check if any model's status is "Completed"
            return any(model['status'] == "Completed" for model in existing_record['models']) is not None
    
    async def get_process_status_by_userid(self, user_id: str):
        # Fetch all documents for the specific user_id from the status collection
        documents = await self.status_collection.find(
            {"user_id": user_id}  # Query by user_id
        ).sort("start_time", -1).to_list(length=None)  # Sort by start_time in descending order

        # Prepare the result list with process_id, models, and overall_status
        status_list = []
        for doc in documents:
            process_id = doc.get("process_id")
            overall_status = doc.get("overall_status")
            models = [
                {
                    "model_id": model.get("model_id"),
                    # Extract the required fields from the document
                    "model_name": model.get("model_name"),
                    "status": model.get("status")
                }
                for model in doc.get("models", [])  # Create a list of dictionaries for models
            ]
                
            status_list.append({
                "process_id": process_id,
                "models": models,            # Add models to the result
                "overall_status": overall_status  # Fetch the 'overall_status'
            })
        
        # Return status list if available, otherwise return None
        if status_list:
            return {"statuses": status_list}
        
        return None  # If no documents found

    # async def get_process_results(self, process_id: str):
    #     document = await self.results_collection.find_one(
    #     {"process_id": process_id},
    #     projection={"models": 0, "user_id": 0,"_id":0}  # Exclude fields
    # )
    #     return document if document else None
    
    async def get_process_results(self, user_id: str, page: int, page_size: int):
    # Calculate the number of documents to skip
        skip = (page - 1) * page_size
        # Find documents for the specific user_id with pagination and sort by timestamp in descending order
        cursor = self.config_collection.find({"user_id": user_id}).sort("timestamp", -1).skip(skip).limit(page_size)
        # Prepare the result list to store task details
        results = []
        # Iterate over each document in the paginated cursor
        async for document in cursor:
            process_id = document.get("process_id")
            # Fetch the overall_status for the process_id from the status_collection
            status_document = await self.status_collection.find_one({"process_id": str(process_id)})
            overall_status = status_document.get("overall_status") if status_document else None
            
            # Append the task details directly from each document's fields
            results.append({
                "process_id": process_id,
                "process_name": document.get("process_name"),
                "model_id": document.get("model_id"),
                "model_name": document.get("model_name"),
                "payload_path": document.get("payload_file_path"),
                "timestamp": document.get("timestamp"),
                "overall_status": overall_status

            })
        
        # Fetch the total count of documents for this user_id
        total_count = await self.config_collection.count_documents({"user_id": user_id})
        
        # Calculate the total number of pages
        total_pages = (total_count + page_size - 1) // page_size
        
        # Return paginated results and metadata
        return results,total_count
    
    async def get_metric_results(self, user_id: str, page: int, page_size: int):
        # Calculate the number of documents to skip for pagination
        skip = (page - 1) * page_size
      
        # Step 1: Calculate the total doc_count (total metrics available)
        total_metrics = 0
        async for document in self.status_collection.find(
            {"user_id": user_id, "metrics": {"$exists": True, "$ne": []}}
        ):
            if "metrics" in document:
                total_metrics += len(document["metrics"])
        # Step 2: Fetch metrics with pagination logic
        flattened_metrics = []
        cursor = (
            self.status_collection.find(
                {"user_id": user_id, "metrics": {"$exists": True, "$ne": []}}
            )
            .sort("timestamp", -1)
        )

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
                        "timestamp": timestamp
                    }
                    flattened_metrics.append(metric_info)
            if len(flattened_metrics) >= (skip + page_size):
                break

        # Apply pagination to the flattened metrics
        paginated_metrics = flattened_metrics[skip:skip + page_size]
        
        doc_count = total_metrics
        # Return the paginated results and the total count of metric_id
        return paginated_metrics, doc_count


    async def get_results_by_process_id(self, process_id: str):
        try:
            # Find the document with the specified process_id
            document = await self.results_collection.find_one({"process_id": process_id})
            
            # Check if the document exists
            if not document:
                raise HTTPException(status_code=404, detail="Document not found.")
            # Extract the 'models' array from the document
            models = document.get("models")
            # Check if 'models' is not found in the document
            if models is None:
                raise HTTPException(status_code=404, detail="'models' object not found in the document.")
            
            # Find the model with the matching model_id
            #model = next((m for m in models if m.get("model_id") == model_id), None)
            
            # Check if the model with the specified model_id exists
            #if model is None:
                #raise HTTPException(status_code=404, detail=f"Model with model_id {model_id} not found.")
            
            # Assuming 'model' is the dictionary that contains the 'results'
            #results = models.get("results", {})
           
            # Remove the 'timestamp' key if it exists
            #if "timestamp" in results:
                #del results["timestamp"]

            # Now, the 'results' variable contains the results without the timestamp
            return models
        
        except Exception as e:
            # Handle any unexpected exceptions
            raise HTTPException(status_code=500, detail=str(e))


        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving results: {e}")
    async def get_results(self, process_id: str):
        try:
            # Find the document with the specified process_id
            document = await self.results_collection.find_one({"process_id": process_id})
            
            # Check if the document exists
            if not document:
                raise HTTPException(status_code=404, detail="Document not found.")
            
            # Extract the 'results' object from the document
            results = document.get("models")
           
            # Check if 'results' is not found in the document
            if results is None:
                raise HTTPException(status_code=404, detail="'results' object not found in the document.")
            
            # Return the 'results' object
            return results
        except Exception as e:
            # Handle any unexpected exceptions
            raise HTTPException(status_code=500, detail=str(e))


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
