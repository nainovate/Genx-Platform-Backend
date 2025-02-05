import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import os
from fastapi import FastAPI, HTTPException
import logging
import random
import re
from typing import List
import uuid
import requests

import yaml
from flask import jsonify
from utils import Payload, ModelStatus, StatusRecord
from Database.evaluationSetup import MongoDBHandler
from ApplicationManagment.Handlers.storeExcel import JSONToExcelConverter
from db_config import eval_config

logger = logging.getLogger(__name__)

class EvaluationHandler:
    task_statuses = {}
    results_path = "C:/Users/Admin/projects/Model_Evaluation/services/Evaluation/results"
    def __init__(self, mongoHandler: MongoDBHandler, payload: Payload):
        self.mongoHandler = mongoHandler
        self.payload = payload
        self.endpoint = eval_config['SERVER_ENDPOINT']
        self.status_endpoint = eval_config['STATUS_ENDPOINT']
        # Access the payload fields like this:
        self.payload_file_path = self.payload.payload_file_path
        self.user_id = self.payload.user_id
        self.session_id = self.payload.session_id
        self.config_type = self.payload.config_type
        self.config_id = self.payload.config_id
        self.client_api_key = self.payload.client_api_key
        self.process_name = self.payload.process_name
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
        
    async def background_evaluation(self, process_id: str):
        start_time = datetime.now()

        # Initialize in-memory storage for the process
        EvaluationHandler.task_statuses[process_id] = {
            "models": {model_id: "Not Started" for model_id in self.config_ids},
            "overall_status": "In Progress",
            "start_time": start_time,
            "end_time": None,
            "async_task": asyncio.current_task()
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

            # Create initial status record in the database
            # Create initial status record in the database
            status_record = {
                "user_id": self.user_id,
                "process_name": self.process_name,
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

            # Evaluate each model concurrently
            async def evaluate_model(index, model_id):
                try:
                    print("id", model_id)
                    # Update the status of the current model
                    EvaluationHandler.task_statuses[process_id]["models"][model_id] = "In Progress"
                    status_record['models'][index]['status'] = "In Progress"
                    await self.mongoHandler.update_status_record(status_record)

                    # Perform evaluation for the current model
                    eval_results = await self.select_config_type(model_id)  # Await here
                    if eval_results.get('status_code') == 200:
                        # Store results immediately in results_db
                        model_name = self.model_names[index]
                        await self.mongoHandler.update_results_record(
                            process_id, self.process_name, self.user_id, self.config_type, model_id, model_name, eval_results['data']
                        )
                        EvaluationHandler.task_statuses[process_id]["models"][model_id] = "Completed"
                        status_record['models'][index]['status'] = "Completed"

                        #status_record["status_details"][0]["overall_status"] = "Completed"
                        await self.mongoHandler.update_status_record(status_record)
                    else:
                        EvaluationHandler.task_statuses[process_id]["models"][model_id] = "Failed"
                        status_record['models'][index]['status'] = "Failed"
                        #status_record["status_details"][0]["overall_status"] = "Failed"
                        await self.mongoHandler.update_status_record(status_record)
                        raise Exception("Evaluation failed for model")
                        

                except Exception as e:
                    logger.error(f"Error during evaluation of model {model_id}: {e}")
                    EvaluationHandler.task_statuses[process_id]["models"][model_id] = "Failed"
                    status_record['models'][index]['status'] = "Failed"
                    print("task_statuses", EvaluationHandler.task_statuses)
                    print("status_record", status_record)
                    #status_record["status_details"][0]["overall_status"] = "Failed"
                    await self.mongoHandler.update_status_record(status_record)
                    raise

                
                    
            for index, model_id in enumerate(self.config_ids):
                try:
                    # Attempt to run evaluate_model for the current config_id
                    await evaluate_model(index, model_id)
                except Exception as e:
                    # Log or handle the error if evaluate_model fails
                    print(f"Error evaluating model {model_id} at index {index}: {e}")
                        
            # Check if all model statuses are "Completed"
            if all(status == "Completed" for status in EvaluationHandler.task_statuses[process_id]["models"].values()):
                EvaluationHandler.task_statuses[process_id]["overall_status"] = "Completed"
                status_record["overall_status"] = "Completed"
            else:
                print("overall status failed")
                # If any model is not "Completed", set the overall status to "Failed"
                EvaluationHandler.task_statuses[process_id]["overall_status"] = "Failed"
                status_record["overall_status"] = "Failed"

            # Update the status record in the database
            await self.mongoHandler.update_status_record(status_record)

            # Extract results from DB
            all_results = await self.mongoHandler.get_results(process_id)
            if all_results:
                os.makedirs(os.path.dirname(EvaluationHandler.results_path), exist_ok=True)
                excelConverter = JSONToExcelConverter()
                resultpath = excelConverter.convert_json_to_excel(all_results, EvaluationHandler.results_path, self.config_type)
                await self.mongoHandler.update_results_path(process_id, resultpath["path"])

            # Update end time
            end_time = datetime.now()
            EvaluationHandler.task_statuses[process_id]["end_time"] = end_time
            status_record["end_time"] = end_time
            await self.mongoHandler.update_status_record(status_record)

            return {"status": EvaluationHandler.task_statuses, "detail": "Evaluation completed"}

        except Exception as e:
            logger.error(f"Unexpected error in evaluation: {e}")
            EvaluationHandler.task_statuses[process_id]["overall_status"] = "Failed"
            EvaluationHandler.task_statuses[process_id]["end_time"] = datetime.now()
            status_record["overall_status"] = "Failed"
            await self.mongoHandler.update_status_record(status_record)
            raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

    async def select_config_type(self, deploy_id):
        try:
            if self.config_type == "STT":
                return await self.evaluate_stt()  # Await here
            elif self.config_type in ["LLM", "RAG"]:
                return await self.evaluate_config_type(deploy_id)  # Await here
            else:
                raise ValueError('Invalid config_type type')
        except ValueError as e:
            logger.error(f"config_type error: {e}")
            return {"error": str(e), "status_code": 400}  # Adjust to return dict

    async def evaluate_config_type(self, deploy_id):
        """Handles both LLM and RAG evaluations"""
        try:
            payload_file_path = self.payload_file_path
            # Check if payload is a file path or direct data
            if isinstance(payload_file_path, str) and os.path.isfile(payload_file_path):
                collection = self.load_yaml_data(payload_file_path)
            elif isinstance(payload_file_path, dict):
                collection = payload_file_path
            else:
                raise ValueError('Invalid payload format provided')
            if not collection:
                raise ValueError('No questions provided')

            final_result = {"timestamp": datetime.now().strftime("%d%m%Y_%H%M")}
            for key, value in collection.items():
                payload_questions = [{"query": q.get("question", "")} for q in value]
                responses = await self.fetch_responses(payload_questions, deploy_id) 
                print("responses", responses) # Await here
                if responses['status_code'] == 200:
                    final_result[f"{key}"] = self.process_responses(responses['response'], value)                    
                else:
                    raise HTTPException(status_code=500, detail="Response failed")
            return {"status_code": 200, "data": final_result}
        
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return {"status_code": 500, "detail": str(e)}

    async def fetch_responses(self, payload_questions, deploy_id):
        try:
            test_id = str(uuid.uuid4())
            user_responses = {"responses": []}

            loop = asyncio.get_running_loop()
            
            # Prepare tasks for each question using run_in_executor
            response_tasks = [
                loop.run_in_executor(None, self._post_request, self._prepare_request_data(q.get("query", ""), deploy_id))
                for q in payload_questions
            ]
            
            # Gather results
            responses = await asyncio.gather(*response_tasks, return_exceptions=True)

            for question_data, response in zip(payload_questions, responses):
                if isinstance(response, Exception):
                    logger.error(f"Request failed: {response}")
                    raise HTTPException(status_code=500, detail="Request failed")

                print("res", response)
                if response.status_code == 200:
                    formatted_response = self.format_responses(
                        question_data.get("query", ""), response.json(), test_id, response.status_code
                    )
                    user_responses['responses'].append(formatted_response)
                else:
                    logger.error(f"Request failed with status {response.status_code}")
                    raise HTTPException(status_code=500, detail="Request failed")

            return {"status_code": 200, "response": user_responses}

        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return {"status_code": 500, "detail": str(e)}



    def _prepare_request_data(self, question, deploy_id):

        if self.config_type == "LLM":
            inputData = {"question": question}
            return {
            "userId": self.user_id,
            "clientApiKey": self.client_api_key,
            "deployId": deploy_id,
            "inputData": inputData,
            "uniqueId": self.session_id
        }
        else:
            """Prepares the request payload based on input data."""
            return {
                "userId": self.user_id,
                "clientApiKey": self.client_api_key,
                "deployId": deploy_id,
                "query": question,
                "uniqueId": self.session_id
            }

    executor = ThreadPoolExecutor()

    def _post_request(self, data):
    
        try:
            response = requests.post(f"{self.endpoint}", json=data)
            print("response", response)

            response.raise_for_status()

            #Get job ID from response
            job_data = response.json()
            job_id = job_data['job_id']

            while True:
                status_response = requests.get(f"{self.status_endpoint}/{job_id}")
                status_response.raise_for_status()

                status_data = status_response.json()
                current_status = status_data["status"]

                if current_status == "completed":
                    print(status_data)
                    return(status_response)
                    break
                elif current_status == "failed":
                    raise Exception(f"Transcription failed: {status_data.get('error', 'Unkown error')}")
                elif current_status == "cancelled":
                    raise Exception("Job was cancelled")

            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"RequestException: {e}")
            raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")
    def format_responses(self, question, data, test_id, status_code):
        """Formats the response received from the endpoint."""
        try:
            result = data.get('result', '')
            response_text = "\n".join(re.findall(r'<ASSISTANT>:\s*(.*?)(?=\n<|\Z)', result, re.DOTALL))

            return {
                "test_id": test_id,
                "user_id": self.user_id,
                "uniqueId": self.session_id,
                "query": question,
                "response": response_text,
                "status_code": status_code
            }
        except Exception as e:
            logger.error(f"Error formatting response: {e}")
            return {
                "status_code": 500
            }

    def evaluate_stt(self):
        """Handles STT evaluation"""
        try:
            collection = self.load_yaml_data(self.payload_file_path)
            if not collection:
                raise ValueError('No data found in YAML file')

            final_result = {"timestamp": datetime.now().strftime("%d%m%Y_%H%M")}
            payload_questions = [{"input_file": q.get("input_file", "")} for q in collection.get('payload', [])]
            final_result["data"] = self.send_audio_to_stt(self.endpoint, payload_questions, self.config_id, self.client_api_key, self.user_ids)
            return jsonify(final_result), 200

        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return jsonify({"status_code": 500, "detail": str(e)}), 500
        
    def send_audio_to_stt(self, endpoint, payload_questions, config_id, clientApiKey, user_ids):
        """Handles sending audio to STT model for processing."""
        responses = []
        try:
            for question_data in payload_questions:
                question = question_data[1] if isinstance(question_data, tuple) else question_data.get("query", "")
                data = self._prepare_request_data(random.randint(1000, 9999), clientApiKey, config_id, question, random.randint(100, 9999))
                response = self._post_request(endpoint, data)
                

                if response.status_code == 200:
                    responses.append(response.json())
                else:
                    self._handle_request_error(responses, question, response)

            return responses
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {'status_code': 500, 'detail': f"Unexpected error: {str(e)}"}

    def load_yaml_data(self, payload_file_path):
        """Load data from the YAML file"""
        try:
            with open(payload_file_path, 'r') as file:
                return yaml.safe_load(file)
        except (IOError, yaml.YAMLError) as e:
            logger.error(f"Error loading YAML file: {e}")
            raise


    def process_responses(self, responses_data, value):
        """Process and score responses"""
        result = []
        
        for response in responses_data.get('responses', []):
            question = response.get("query", "")
            
            # Ensure 'value' is a list of dictionaries, and use 'next' safely
            if isinstance(value, list):
                payload_answer = next((q.get('answer', '') for q in value if q.get('question') == question), None)
            else:
                logger.error("Value should be a list of dictionaries")
                raise ValueError("Expected 'value' to be a list of dictionaries")
            
            response['answer'] = payload_answer or "Answer not found"
            
            result.append(response)
        
        return result

    
