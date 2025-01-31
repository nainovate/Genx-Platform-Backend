import asyncio
from datetime import datetime, timedelta
import json
import logging
import os
import uuid
from fastapi import APIRouter, BackgroundTasks, FastAPI, HTTPException, Query, status, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import ValidationError
from pymongo import MongoClient
from Database.applicationDataBase import ApplicationDataBase
from ApplicationManagment.Handlers.evaluationHandler import EvaluationHandler
from Database.evaluationSetup import MongoDBHandler
from ApplicationManagment.Handlers.MetricsCalculator import MetricsCalculator
from ApplicationManagment.Handlers.benchmarkingHandler import BenchmarkHandler
from ApplicationManagment.Handlers.BenchExcel import ExcelHandler
from ApplicationManagment.Handlers.storeExcel import JSONToExcelConverter
from utils import BenchPayload, LoginDetails, MetricRequest, MetricsPayload, Pagination, Payload, RequestDetails, ResultDetails, ScheduleDetails, metric, viewDetails,RangeUpdateRequest
from db_config import eval_config, bench_config

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

            # Check for unique process_name
            #if mongo_handler.config_collection.find_one({"process_name": payload.process_name}):
                #raise HTTPException(status_code=400, detail="Process name must be unique")

            # Check for ongoing tasks
            if await mongo_handler.check_ongoing_task(payload.user_id):
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

        # Initialize evaluation handler
        evaluation_handler = EvaluationHandler(mongo_handler, payload)
        # Add task to background tasks
        if background_tasks:
            background_tasks.add_task(evaluation_handler.background_evaluation, process_id)
        else:
            asyncio.create_task(evaluation_handler.background_evaluation(process_id))

        logger.info(f"Evaluation task started with process ID: {process_id}")

        return {
            "status_code": 200,
            "process_id": process_id,
            "message": "Evaluation has been started in the background"
        }

    def calculate_metrics(self, payload, background_tasks):
        # Generate a unique metric_id
        metric_id = str(uuid.uuid4())[:8]
        # Log the payload and metric_id
        org_id = payload.get("org_id")
        # Create the MongoDB handler and metrics calculator
        mongo_handler = MongoDBHandler(eval_config, org_id)
        eval = MetricsCalculator(mongo_handler, payload)

        # Add the metrics calculation task to the background
        background_tasks.add_task(eval.do_metrics, metric_id)  # Pass metric_id to the task if needed

        # Return the metric_id for tracking purposes
        return {
            "status": "Metrics calculation started",
            "metric_id": metric_id,
            "detail": "You can check the status via the status endpoint."
        }



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
                process_id=request["process_id"]
                service=request["service"]
                org_id=request["orgId"]
                while True:
                    # Fetch the status details for the process
                    model_statuses, overall_status = await BenchmarkHandler.get_status_details(
                    process_id, 
                        service, org_id
                    )

                    if model_statuses is None:
                        # Send an error message and keep checking
                        yield f"data: {json.dumps({'error': overall_status})}\n\n"
                        await asyncio.sleep(2)
                        continue

                    # Prepare and send response data as SSE
                    response_data = {
                        "models": model_statuses,
                        "overall_status": overall_status
                    }
                    yield f"data: {json.dumps(response_data)}\n\n"

                    # Check if all models have a final status
                    all_tasks_complete = all(
                        model["status"] in ["Completed", "Failed"]
                        for model in model_statuses
                    )

                    if all_tasks_complete:
                        break  # Exit the loop when all tasks are done

                    # Heartbeat to keep the connection alive
                    await asyncio.sleep(2)

            except Exception as e:
                # Send any encountered errors back to the client
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                
        # Return the streaming response with SSE-compatible headers
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Access-Control-Allow-Origin": "*"
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
            mongo_handler = MongoDBHandler(eval_config, Pagination["orgId"])
            # Fetch the process results using the user_id from MongoDB
            result, doc_count = await mongo_handler.get_process_results(Pagination["user_id"], Pagination["page"], Pagination["page_size"])
            
            # Return a successful response with a 200 status code
            return {"result": result, "doc_count": doc_count}

        except Exception as e:
            # Handle any errors and return a 500 status code with error details
            return JSONResponse(
                status_code=500,
                content={"message": "Error fetching process results", "detail": str(e)}
            )
        
    async def view_result(self,request):
        try:
            
            service = request["service"]
            orgId = request["orgId"]
            process_id = request["process_id"]
            mongo_handler = await MongoDBHandler.get_mongo_handler(service, orgId)
            # Get results by process_id using the method defined earlier
            result =  await mongo_handler.get_results_by_process_id(process_id)
            return result

        except Exception as e:
            # Generic exception handling
            return JSONResponse(
                status_code=500,
                content={"message": "Error Retreiving results", "detail": str(e)})


    async def view_status_by_userid(self, RequestDetails):
        try:
            
            service = RequestDetails["service"]
            orgId = RequestDetails["orgId"]
            user_id = RequestDetails["user_id"]
            mongo_handler = await MongoDBHandler.get_mongo_handler(service, orgId)
            # Get results by process_id using the method defined earlier
            
            result = await mongo_handler.get_process_status_by_userid(user_id)
            return self.validation_error_response(status_code=200, detail= result)

        except Exception as e:
            # Generic exception handling
            return self.validation_error_response(
                status_code=500,
                detail={"message": "Error Retreiving results", "detail": str(e)})
        
    async def download_excel(self, RequestDetails, background_tasks):
        try:
            service = RequestDetails["service"]
            process_id = RequestDetails["process_id"]
            
            orgId = RequestDetails.get("orgId")
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
            org_id = request["orgId"]
            mongo_handler = MongoDBHandler(eval_config, org_id)
            result = await mongo_handler.fetch_metrics_by_id(metric_id)
            return result

        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def check_metric_results(self, request):
        try:
            user_id = request["user_id"]
            page = request["page"]
            page_size = request["page_size"]
            org_id = request["orgId"]
            # Get the MongoDB handler based on the service
            mongo_handler = MongoDBHandler(eval_config,org_id)
            # Fetch the process results using the user_id from MongoDB
            result, doc_count = await mongo_handler.get_metric_results(user_id, page, page_size)
            
            # Return a successful response with a 200 status code
            return {"result": result, "doc_count": doc_count}

        except Exception as e:
            # Handle any errors and return a 500 status code with error details
            return JSONResponse(
                status_code=500,
                content={"message": "Error fetching process results", "detail": str(e)}
            )       
        
    async def update_ranges(self, request):
        """
        Updates metric ranges in the database.

        Args:
            request (RangeUpdateRequest): The request containing the metric details and new ranges.
            db_handler: The database handler with an `update_metric_ranges` method.

        Returns:
            dict: Success message if updated, else raises an HTTPException.

        Raises:
            HTTPException: On validation errors, missing fields, or update failures.
        """
        metric_id = request["metric_id"]
        metric_name = request["metric_name"]
        new_ranges = request["new_ranges"]
        org_id = request["orgId"]
        try:
            # Validate the request (Pydantic already ensures this for required fields)
            if not metric_id or not metric_name or not new_ranges:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="All fields (metric_id, metric_name, new_ranges) are required."
                )
            # Ensure the new_ranges is a dictionary with valid entries
            if not isinstance(new_ranges, dict) or not new_ranges:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="The 'new_ranges' field must be a non-empty dictionary."
                )
            mongo_handler = MongoDBHandler(eval_config,org_id)
            # Call the database function to update metric ranges
            result = await mongo_handler.update_metric_ranges(
                metric_id=metric_id,
                metric_name=metric_name,
                new_ranges=new_ranges
            )
            # Check the result from the database
            if result is not None and result > 0:
                return {"message": f"{result} document(s) updated successfully."}
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Metric or document not found, or metric name does not match existing ranges."
                )
        except ValidationError as e:
            # Handle validation errors from Pydantic
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Validation error: {e.errors()}"
            )
        except Exception as e:
            # Catch all other unexpected exceptions
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred: {str(e)}"
            )