import asyncio
from datetime import datetime
import os
from fastapi import HTTPException, logger
from ApplicationManagment.Handlers.BenchExcel import ExcelHandler
from  ApplicationManagment.Handlers.asynctester import AsyncTester
from  ApplicationManagment.Handlers.evaluationHandler import EvaluationHandler
from utils import Payload, ModelStatus, StatusRecord
from Database.evaluationSetup import MongoDBHandler
from db_config import bench_config

# mongo_handler = MongoDBHandler(bench_config)

class BenchmarkHandler:

    def __init__(self, org_id: str):
        # Initialize the MongoDB handler with the org_id
        self.mongo_handler = MongoDBHandler(bench_config, org_id)
    task_statuses = {}
    results_path = "C:/Users/Admin/projects/Model_Evaluation/services/Evaluation/results"
        
    def __init__(self, mongoHandler: MongoDBHandler, payload: Payload):
        self.mongoHandler = mongoHandler
        self.payload = payload
        self.endpoint = bench_config['SERVER_ENDPOINT']
        # Access the payload fields like this:
        self.payload_file_path = self.payload.payload_file_path
        self.user_id = self.payload.user_id
        self.session_id = self.payload.session_id
        self.config_type = self.payload.config_type
        self.config_id = self.payload.config_id
        self.client_api_key = self.payload.client_api_key
        self.process_name = self.payload.process_name
        self.total_requests = self.payload.total_requests
        # Lists to store extracted config_id and model_name
        self.config_ids = []
        self.model_names = []

        # Extract and store config_id and model_name from the config_id list of dicts
        for config in self.config_id:
            for config_id, model_name in config.items():
                self.config_ids.append(config_id)
                self.model_names.append(model_name)

        # Now, self.config_ids contains all config_ids
        # and self.model_names contains all model_names

        print("Extracted Config IDs:", self.config_ids)
        print("Extracted Model Names:", self.model_names)

    async def background_benchmark(self, process_id: str):
        start_time = datetime.now()

        # Initialize in-memory storage for the process
        BenchmarkHandler.task_statuses[process_id] = {
            "models": {model_id: "Not Started" for model_id in self.config_ids},
            "overall_status": "In Progress",
            "start_time": start_time,
            "end_time": None,
            "async_task": None  # Placeholder for the asyncio task
        }
        
        try:
            config_data = {
                "user_id": self.user_id,
                "process_id": process_id,
                "process_name": self.process_name,
                "model_id": self.config_ids,
                "model_name": self.model_names,
                "payload_file_path": self.payload_file_path
            }
            await self.mongoHandler.insert_config_record(config_data)            
            
            status_record = {
                "user_id": self.user_id,
                
                "process_id": process_id,
                "models": [
                    {
                        "model_id": model_id,
                        "model_name": self.model_names[index],
                        "status": "Not Started"
                    }
                    for index, model_id in enumerate(self.config_ids)
                ],
                "overall_status": "In Progress",
                "start_time": start_time
            }
    

            # Insert initial status in EvalStatus using MongoDBHandler
            await self.mongoHandler.update_status_record(status_record)

            # Create the actual asyncio task and store it in task_statuses
            BenchmarkHandler.task_statuses[process_id]["async_task"] = asyncio.create_task(self.run_benchmarking_process(process_id, status_record))

            return {"status": "Benchmark started", "process_id": process_id}

        except Exception as e:
            logger.error(f"Unexpected error in evaluation: {e}")
            BenchmarkHandler.task_statuses[process_id]["overall_status"] = "Failed"
            BenchmarkHandler.task_statuses[process_id]["end_time"] = datetime.now()
            status_record.overall_status = "Failed"
            status_record.end_time = datetime.now()
            await self.mongoHandler.update_status_record(status_record)
            raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

    async def run_benchmarking_process(self, process_id: str, status_record: StatusRecord):
        # Evaluate each model sequentially
        for index, model_id in enumerate(self.config_ids):
            # Update the status of the current model
            BenchmarkHandler.task_statuses[process_id]["models"][model_id] = "In Progress"
            status_record['models'][index]['status']= "In Progress"
            print("up..status", status_record)
            await self.mongoHandler.update_status_record(status_record)

            # Perform benchmarking for the current model
            tester = AsyncTester(
                self.payload_file_path, self.user_id, self.session_id, 
                self.endpoint, self.config_type, model_id, self.client_api_key,self.total_requests
            )
            
            result = await tester.test_async_endpoint()  # Await the result of the test
            data, status_code = result
            
            if status_code == 200:
                model_name = self.model_names[index]

                # Store results immediately in results_db
                await self.mongoHandler.update_results_record(process_id, self.process_name, self.user_id, self.config_type, model_id, model_name, data)
                BenchmarkHandler.task_statuses[process_id]["models"][model_id] = "Completed"
                status_record['models'][index]['status'] = "Completed"

                await self.mongoHandler.update_status_record(status_record)

            else:
                BenchmarkHandler.task_statuses[process_id]["models"][model_id] = "Failed"
                status_record['models'][index]['status'] = "Failed"
                status_record.overall_status = "Failed"
                await self.mongoHandler.update_status_record(status_record)
                break  # Exit the loop if evaluation fails

            # Update overall status if all models are processed
            if index == len(self.config_ids) - 1:
                
                BenchmarkHandler.task_statuses[process_id]["overall_status"] = "Completed"
                status_record["overall_status"] = "Completed"
                
        await self.mongoHandler.update_status_record(status_record)
        
        # After processing all model_ids, extract results from DB
        all_results = await self.mongoHandler.get_results_by_process_id(process_id)
        
        # Pass the consolidated results to json_to_excel
        if all_results:
            
            os.makedirs(os.path.dirname(BenchmarkHandler.results_path), exist_ok=True)
            excel_handler = ExcelHandler(BenchmarkHandler.results_path)
            generated_excel_path = excel_handler.json_to_excel(all_results)  # Pass all results at once

            # Store the generated Excel file path
            await self.mongoHandler.update_results_path(process_id, generated_excel_path)

        # Update the end time after all evaluations are completed
        BenchmarkHandler.task_statuses[process_id]["end_time"] = datetime.now()
        status_record["end_time"] = datetime.now()
        await self.mongoHandler.update_status_record(status_record)

        # Return final status and results
        return {"status": BenchmarkHandler.task_statuses[process_id], "detail": "Benchmark completed", "result": all_results}

    @staticmethod
    async def get_status_details(process_id: str, service: str):
        print("details are", process_id,service)
        # Initialize the current statuses list
        model_statuses = []
        overall_status = ""

        # Check BenchmarkHandler task statuses
        if process_id in BenchmarkHandler.task_statuses:
            # Access the status details
            status_details = BenchmarkHandler.task_statuses[process_id]
            overall_status = status_details['overall_status']
            
            # Wrap in-memory statuses in a list of models with model_id and status
            model_statuses = [{"model_id": model_id, "status": status} 
                              for model_id, status in status_details['models'].items()]
            print("model_statuses", model_statuses)
            #return model_statuses, overall_status
        # Check EvaluationHandler task statuses
        elif process_id in EvaluationHandler.task_statuses:
            # Access the status details
            status_details = EvaluationHandler.task_statuses[process_id]
            overall_status = status_details['overall_status']
            
            # Wrap in-memory statuses in a list of models with model_id and status
            model_statuses = [{"model_id": model_id, "status": status} 
                              for model_id, status in status_details['models'].items()]
            #return model_statuses, overall_status
        else:
            # Get the MongoDB handler based on the service
            mongo_handler = await MongoDBHandler.get_mongo_handler(service)
            # Check for statuses in the database if not found in task_statuses
            db_status, overall_status = await mongo_handler.get_model_statuses_by_process_id(process_id)
            # Extracting overall_status
            #overall_status = db_status[0].get('overall_status')
            print("Database statuses:", db_status)
            
            if not db_status:
                return None, "Process not found"  # No status found
            
            # Format db_status to handle multiple models if needed
            if isinstance(db_status, list):
                model_statuses = db_status
            else:
                # Default case if db_status is in an unexpected format
                model_statuses = [{"model_id": process_id, "status": db_status}]

        return model_statuses, overall_status
