import asyncio
from datetime import datetime, timedelta
import json
import logging
import os
from typing import Dict
import uuid
from fastapi import APIRouter, BackgroundTasks, FastAPI, HTTPException, Query, status, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import ValidationError
from pymongo import MongoClient
from Database.organizationDataBase import OrganizationDataBase
from Database.applicationDataBase import ApplicationDataBase
from ApplicationManagment.Handlers.evaluationHandler import EvaluationHandler
from Database.evaluationSetup import MongoDBHandler
from ApplicationManagment.Handlers.MetricsCalculator import MetricsCalculator
from ApplicationManagment.Handlers.benchmarkingHandler import BenchmarkHandler
from ApplicationManagment.Handlers.BenchExcel import ExcelHandler
from ApplicationManagment.Handlers.storeExcel import JSONToExcelConverter
from utils import BenchPayload, LoginDetails, MetricRequest, MetricsPayload, Pagination, Payload, RequestDetails, ResultDetails, ScheduleDetails, metric, viewDetails,RangeUpdateRequest
from db_config import eval_config, bench_config

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

# Global dictionary to store process_id -> orgId mapping
process_org_mapping: Dict[str, str] = {}
    
def initilizeApplicationDB():
    applicationDB = ApplicationDataBase()
    return applicationDB

class Evaluation:
    def __init__(self, userId: str, role: dict, orgIds: list):
        self.role = role
        self.userId = userId
        self.orgIds = orgIds
        self.applicationDB = initilizeApplicationDB()
        

    async def get_evaluation_results(self, data: dict):
        try:
            # Validate input data
            if not isinstance(data, dict) or "orgId" not in data or "payload" not in data:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. Expected a dictionary with 'orgId' and 'payload' keys."
                }

            orgId = data["orgId"]
            background_tasks = data.get("background_tasks")  # Optional
            # Parse payload into the Payload model
            try:

                payload = Payload(**data["payload"])
            except ValidationError as e:
                return {
                    "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                    "detail": f"Payload validation error: {e.errors()}"
                }

            # Initialize MongoDB Handler
            mongo_handler = MongoDBHandler(eval_config, orgId)
            logger.info(f"MongoDBHandler initialized for orgId: {orgId}")

            # Initialize the organization database
            organizationDB = OrganizationDataBase(orgId)
            
            # Check if organizationDB is initialized successfully
            if organizationDB.status_code != 200:
                return {
                    "status_code": organizationDB.status_code,
                    "detail": "Error initializing the organization database"
                }

            # Check for unique process_name
            #if mongo_handler.config_collection.find_one({"process_name": payload.process_name}):
                #raise HTTPException(status_code=400, detail="Process name must be unique")

            # Check for ongoing tasks
            if await organizationDB.check_ongoing_task(payload.user_id):
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "User already has an ongoing benchmarking task."
                }

        except ConnectionError as e:
            logger.error(f"Database connection error: {str(e)}")
            return {
                "status_code": status.HTTP_503_SERVICE_UNAVAILABLE,
                "detail": "Failed to connect to the database. Please try again later."
            }
        except Exception as e:
            logger.exception(f"Unexpected error: {str(e)}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"Unexpected error occurred: {str(e)}"
            }

        # Generate process ID
        process_id = str(uuid.uuid4()).replace("-", "")[:8]
        logger.info(f"Generated process ID: {process_id}")
        # Store mapping in the global dictionary
        process_org_mapping[process_id] = orgId
        logger.info(f"Stored mapping: {process_id} -> {orgId}")

        # Initialize evaluation handler
        evaluation_handler = EvaluationHandler(mongo_handler, payload)
        # Add task to background tasks
        if background_tasks:
            background_tasks.add_task(evaluation_handler.background_evaluation, process_id, orgId)
        else:
            asyncio.create_task(evaluation_handler.background_evaluation(process_id, orgId))

        logger.info(f"Evaluation task started with process ID: {process_id}")

        return {
            "status_code": 200,
            "process_id": process_id,
            "message": "Evaluation has been started in the background"
        }

    def calculate_metrics(self, payload, background_tasks):
        """
        Initiates metrics calculation for the organization where the process_id exists.

        Args:
            payload (dict): The input data for metrics calculation.
            background_tasks: Background task handler for async execution.

        Returns:
            dict: Response containing metric_id and status message.
        """
        print("Payload:", payload)
        
        # Generate a unique metric_id
        metric_id = str(uuid.uuid4())[:8]
        
        # Extract process_id from payload
        process_id = payload.get("process_id")
        
        if not process_id:
            raise HTTPException(
                status_code=400,
                detail="process_id is required in the payload."
            )

        print("Searching for process_id in orgIds:", self.orgIds)

        # Ensure MongoDB connection is managed properly
        selected_org_id = None
        mongo_handler = None  # Initialize outside loop to persist connection

        try:
            selected_org_id = None  # Ensure selected_org_id is initialized

            for orgId in self.orgIds:
                print("Checking orgId:", orgId)
                
                # Create a MongoDB handler for the organization
                mongo_handler = MongoDBHandler(eval_config, orgId)  # Reuse mongo_handler
                print("MongoDB Handler initialized for orgId:", orgId)

                # Check if process_id exists in this organization's database, and get the process name
                process_data = mongo_handler.check_process_exists(process_id)

                if process_data:  # If process exists
                    process_name = process_data.get("process_name")
                    selected_org_id = orgId
                    print(f"process_id {process_id} (process_name: {process_name}) found in orgId: {selected_org_id}")
                    break  # Stop searching once we find the matching orgId

            if not selected_org_id:
                raise HTTPException(
                    status_code=404,
                    detail=f"process_id {process_id} not found in any organization."
                )

            # Initialize MetricsCalculator with process_name
            eval = MetricsCalculator(payload, process_name, selected_org_id)  # Pass process_name along with orgId

            # Add metrics calculation as a background task
            background_tasks.add_task(eval.do_metrics, metric_id)

            # Return the metric_id for tracking purposes
            return {
                "status": "Metrics calculation started",
                "metric_id": metric_id,
                "detail": "You can check the status via the status endpoint."
            }

        except Exception as e:
            print(f"Error in calculate_metrics: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

        finally:
            # Ensure MongoDB connection is not closed prematurely
            if mongo_handler:
                mongo_handler.__exit__  # Implement this method in MongoDBHandler if not already



    def validation_error_response(self, status_code, detail):
        """Helper function to return validation errors with status code and detail."""
        return JSONResponse(
            status_code=status_code,
            content={"status_code": status_code, "detail": detail}
        )

    async def start_benchmark_task(self,background_tasks: BackgroundTasks, payload: BenchPayload):
        process_id = str(uuid.uuid4()).replace('-', '')[:8]
        payload_dict = payload.dict()
        missing_fields = [field for field, value in payload_dict.items() if value is None or value == ""]
        
        if missing_fields:
            return self.validation_error_response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Missing or empty fields: {', '.join(missing_fields)}"
            )

        try:
            mongo_handler = MongoDBHandler(bench_config)
            if await mongo_handler.check_ongoing_task(payload.user_id):
                return self.validation_error_response(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User already has an ongoing benchmarking task."
                )
        except ConnectionError:
            return self.validation_error_response(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to connect to the database. Please try again later."
            )
        except Exception as e:
            return self.validation_error_response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error occurred while checking ongoing tasks: {str(e)}"
            )

        # Start background task
        try:
            benchmark_handler = BenchmarkHandler(mongo_handler, payload)
            background_tasks.add_task(benchmark_handler.background_benchmark, process_id)
        except AttributeError as e:
            return self.validation_error_response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"BenchmarkHandler initialization failed: {str(e)}"
            )
        except Exception as e:
            return self.validation_error_response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error starting background task: {str(e)}"
            )

        # Return success response
        return {
            "status_code": 200,
            "process_id": process_id,
            "message": "Benchmarking has been started in the background"
        }


    async def check_process_status(self, request):
        async def event_generator():
            try:
                process_id = request["process_id"]
                service = request["service"]
                org_ids = process_org_mapping.get(process_id, [])  # Get all org IDs associated with the process

                while True:
                    all_model_statuses = []
                    overall_statuses = []

                    # Loop over each org_id and fetch status details
                    for org_id in org_ids:
                        model_statuses, overall_status = await BenchmarkHandler.get_status_details(
                            process_id, service, org_id
                        )

                        if model_statuses is None:
                            yield f"data: {json.dumps({'error': f'Error fetching data for org {org_id}: {overall_status}'})}\n\n"
                            await asyncio.sleep(2)  # Poll every 2 seconds
                            continue

                        all_model_statuses.extend(model_statuses)
                        overall_statuses.append(overall_status)

                    # Determine the combined overall status
                    final_overall_status = "Completed" if all(status == "Completed" for status in overall_statuses) else "In Progress"

                    # Prepare and send response data as SSE
                    response_data = {
                        "models": all_model_statuses,
                        "overall_status": final_overall_status
                    }
                    yield f"data: {json.dumps(response_data)}\n\n"

                    # Check if all models across orgs have a final status
                    all_tasks_complete = all(
                        model["status"] in ["Completed", "Failed"]
                        for model in all_model_statuses
                    )

                    if all_tasks_complete:
                        break  # Exit the loop when all tasks are done

                    # Heartbeat to keep the connection alive
                    await asyncio.sleep(2)  # Poll every 2 seconds

            except Exception as e:
                # Send any encountered errors back to the client
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        # Return the streaming response with SSE-compatible headers
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Access-Control-Allow-Origin": "*",
                "Connection": "keep-alive"  # Ensure the connection remains open
            }
        )

    async def check_process_results(self, Pagination: Pagination):
        try:

            # required_fields = ["service", "user_id", "orgId"]
            # missing_fields = [field for field in required_fields if not getattr(Pagination, field, None)]

            # if missing_fields:
            #     # Raise an error if any required fields are missing
            #     return validation_error_response(
            #         status_code=status.HTTP_400_BAD_REQUEST,
            #         detail=f"Missing required fields: {', '.join(missing_fields)}"
            #     )
            # Get the MongoDB handler based on the service
            # mongo_handler = MongoDBHandler.get_mongo_handler(Pagination["service"], Pagination["orgId"])
            # Initialize the organization database
            orgId = self.orgIds
            organizationDB = OrganizationDataBase(orgId)
            # Fetch the process results using the user_id from MongoDB
            result, doc_count = await organizationDB.get_process_results(Pagination["user_id"], Pagination["page"], Pagination["page_size"])
            # Return a successful response with a 200 status code
            return {"result": result, "doc_count": doc_count}

        except Exception as e:
            # Handle any errors and return a 500 status code with error details
            return JSONResponse(
                status_code=500,
                content={"message": "Error fetching process results", "detail": str(e)}
            )
        
    async def view_result(self, request):
        try:
            print("request", request)
            service = request["service"]
            process_id = request["process_id"]

            result = []  # Initialize an empty list to store results

            print("The orgIds are", self.orgIds)

            for orgId in self.orgIds:
                print("Processing orgId:", orgId)

                mongo_handler = await MongoDBHandler.get_mongo_handler(service, orgId)
                org_results = await mongo_handler.get_results_by_process_id(process_id, orgId)

                if org_results:  # Ensure there are results before adding
                    result.extend(org_results)

            print("Final result:", result)
            return result

        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"message": "Error retrieving results", "detail": str(e)}
            )


    async def view_status_by_userid(self, RequestDetails):
        try:
            service = RequestDetails["service"]
            user_id = RequestDetails["user_id"]
            orgIds = self.orgIds  # Assuming orgIds is a list

            all_results = []  # To store results from multiple orgs

            for orgId in orgIds:
                try:
                    mongo_handler = await MongoDBHandler.get_mongo_handler(service, orgId)
                    result = await mongo_handler.get_process_status_by_userid(user_id, orgId)

                    if result:  # Only add if result is not empty
                        all_results.append(result)
                        print("result", all_results)
                        return all_results
                        
                    return []
                    
                except Exception as org_error:
                    # Log error for a specific org but continue for others
                    print(f"Error fetching results for org {orgId}: {org_error}")

            return self.validation_error_response(status_code=200, detail=all_results)

        except Exception as e:
            return self.validation_error_response(
                status_code=500,
                detail={"message": "Error Retrieving results", "detail": str(e)}
            )

        
    async def download_excel(self, RequestDetails, background_tasks):
        try:
            service = RequestDetails["service"]
            process_id = RequestDetails["process_id"]
            
            orgId = process_org_mapping.get(process_id) if process_id else None
            # Get the MongoDB handler based on the service
            mongo_handler = await MongoDBHandler.get_mongo_handler(service, orgId)
            results_doc = await mongo_handler.get_result_document_by_process_id(process_id)
            results_path = results_doc.get('results_path')

            # Check if the file exists
            if not results_path or not os.path.exists(results_path):
                # Retrieve results from the database
                all_results = await mongo_handler.get_results_by_process_id(process_id)
                if all_results:
                    if service == 'benchmarking':
                        os.makedirs(os.path.dirname(BenchmarkHandler.results_path), exist_ok=True)
                        excel_handler = ExcelHandler(BenchmarkHandler.results_path)
                        generated_excel_path = excel_handler.json_to_excel(all_results)

                        await mongo_handler.update_results_path(process_id, generated_excel_path)
                        results_path = generated_excel_path
                    
                    elif service == 'evaluation':
                        os.makedirs(os.path.dirname(EvaluationHandler.results_path), exist_ok=True)
                        excel_converter = JSONToExcelConverter()
                        resultpath = excel_converter.convert_json_to_excel(all_results, EvaluationHandler.results_path, config_type=None)
                        path = resultpath.get("path")
                        await mongo_handler.update_results_path(process_id, path)
                        results_path = path

            # Check again if the results file was successfully generated
            if not os.path.exists(results_path):
                raise HTTPException(status_code=404, detail="File not found")

            # Schedule the file deletion after the response is sent
            background_tasks.add_task(self.remove_file, results_path)

            # Prepare the file for download
            return FileResponse(
                    results_path,
                    media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # Excel MIME type
                    filename=os.path.basename(results_path),  # Extract file name from path
                    status_code=200  # Explicitly set the status code to 200
                )
        except Exception as e:
            # In case of any error, return a 500 status code with error message
            return JSONResponse(
                status_code=500,
                content={"message": "Error retrieving the file", "detail": str(e)}
            )

    # Helper function to remove the file
    def remove_file(self, file_path: str):
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logger.info(f"Error deleting the file: {e}")


    async def stop_task(self, RequestDetails: RequestDetails):
        try:
            # Get the appropriate task entry based on the service
            if RequestDetails.service == "benchmarking":
                task_entry = BenchmarkHandler.task_statuses.get(RequestDetails.process_id)
            elif RequestDetails.service == "evaluation":
                task_entry = EvaluationHandler.task_statuses.get(RequestDetails.process_id)
            else:
                raise HTTPException(status_code=400, detail="Invalid service")
            
            # Check if the task entry is valid
            if not task_entry:
                raise HTTPException(status_code=404, detail="Task not found for cancellation")

            overall_status = task_entry['overall_status']
            if overall_status != "In Progress":
                raise HTTPException(status_code=400, detail="Task is not in progress or already completed.")

            if 'async_task' in task_entry:
                task = task_entry['async_task']
                
                # Cancel the asyncio task
                task.cancel()

                # Wait for the task to finish cancelling
                try:
                    await task
                except asyncio.CancelledError:
                    logger.info(f"Task {RequestDetails.process_id} cancelled successfully.")
            else:
                raise HTTPException(status_code=404, detail="Task not found for cancellation")

            # Update the task status in memory
            task_entry['overall_status'] = "Failed"  # Update overall status

            # Update model statuses
            # Since task_entry['models'] is a dictionary, we can iterate over its items
            if 'models' in task_entry:
                for model_id in task_entry['models']:  # Iterate over keys (model IDs)
                    task_entry['models'][model_id] = "Failed"  # Update the status for each model

            mongo_handler = await MongoDBHandler.get_mongo_handler(RequestDetails.service)# Ensure this is correctly instantiated
            await mongo_handler.update_model_status_to_cancelled(RequestDetails.process_id)

            logger.info(f"Task {RequestDetails.process_id} status updated to Cancelled in MongoDB.")

        except Exception as e:
            logger.error(f"Error stopping task: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"message": "Error stopping task", "detail": str(e)}
            )
        
    async def get_metrics(self, request):
        try:
            metric_id = request["metric_id"]
            result = []  # Initialize an empty list to store results

            print("The orgIds are", self.orgIds)

            for orgId in self.orgIds:
                print("Processing orgId:", orgId)

                mongo_handler = MongoDBHandler(eval_config, orgId)
                metrics =  await mongo_handler.fetch_metrics_by_id(metric_id)
                print("metrics", metrics)

                if metrics:  # Ensure there are results before adding
                    result.append(metrics)

            print("Final result:", result)
            return result

        except HTTPException as e:
            raise e
        except Exception as e:
            print("Error retrieving metrics:", e)
            raise HTTPException(status_code=500, detail=str(e))


    async def check_metric_results(self, request):
        try:
            user_id = request["user_id"]
            page = request["page"]
            page_size = request["page_size"]

            result = []  # Initialize an empty list to store results
            total_doc_count = 0  # To track total document count

            print("The orgIds are", self.orgIds)

            for orgId in self.orgIds:
                print("Processing orgId:", orgId)

                mongo_handler = MongoDBHandler(eval_config, orgId)
                org_results, doc_count = await mongo_handler.get_metric_results(user_id, page, page_size)

                if org_results:  # Ensure there are results before adding
                    result.extend(org_results)

                total_doc_count += doc_count  # Sum up document counts

            print("Final result:", result)
            return {"result": result, "doc_count": total_doc_count}

        except Exception as e:
            print("Error fetching process results:", e)
            return JSONResponse(
                status_code=500,
                content={"message": "Error fetching process results", "detail": str(e)}
            )

        
    async def update_ranges(self, request):
        """
        Updates metric ranges in the database for multiple organizations.

        Args:
            request (dict): The request containing metric details and new ranges.

        Returns:
            dict: Success message if updated, else raises an HTTPException.

        Raises:
            HTTPException: On validation errors, missing fields, or update failures.
        """
        metric_id = request["metric_id"]
        metric_name = request["metric_name"]
        new_ranges = request["new_ranges"]

        try:
            # Validate input
            if not metric_id or not metric_name or not new_ranges:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="All fields (metric_id, metric_name, new_ranges) are required."
                )

            if not isinstance(new_ranges, dict) or not new_ranges:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="The 'new_ranges' field must be a non-empty dictionary."
                )

            total_updates = 0  # Track total updates

            print("The orgIds are", self.orgIds)

            for orgId in self.orgIds:
                print("Processing orgId:", orgId)

                mongo_handler = MongoDBHandler(eval_config, orgId)
                updated_count = await mongo_handler.update_metric_ranges(
                    metric_id=metric_id,
                    metric_name=metric_name,
                    new_ranges=new_ranges
                )

                if updated_count:
                    total_updates += updated_count

            if total_updates > 0:
                return {"message": f"{total_updates} document(s) updated successfully."}
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Metric or document not found, or metric name does not match existing ranges."
                )

        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Validation error: {e.errors()}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred: {str(e)}"
            )
    async def check_process_name(self, request):
        process_name = request["process_name"]
        orgId = request["orgId"]
        organizationDB = OrganizationDataBase(orgId)
        
        # Call the second check_process_name function
        result = await organizationDB.check_process_name(process_name)
        
        # You can now use the result from the second check_process_name
        if result["exists"]:
            return result
        else:
            # Your other logic, if process name doesn't exist
            return {"message": "Process name is available", "status": "success"}
