from http import HTTPStatus
import os
import json
from datetime import datetime
import asyncio
import re
import statistics
from typing import Any, Dict, List
import uuid
import httpx
import numpy as np
import yaml
import psutil

class AsyncTester:
    def __init__(self, payload_file_path, user_id, session_id, endpoint, config_type, config_id, client_api_key, total_requests,concurrency_limit=50):
        self.payload_file_path = payload_file_path
        self.user_id = user_id
        self.endpoint = endpoint
        self.config_type = config_type
        self.config_id = config_id
        self.concurrency_limit = concurrency_limit
        self.query_list = []
        self.results = []
        self.latencies = []
        self.session_id = session_id
        self.task_queue = asyncio.Queue()
        self.client_api_key = client_api_key
        self.total_requests = total_requests
        self.execution_timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        self.distributor_map = {}
        self.prompt_counts = {}

    async def fetch_async(self, client, url, data, semaphore):
        async with semaphore:
            start_time = asyncio.get_event_loop().time()
            print(f"Request {data['request_id']} is running...")

            try:
                response = await client.post(url, json=data, timeout=3000)
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                error_message = (
                    f"Server error '{exc.response.status_code} {exc.response.reason_phrase}' for URL '{exc.request.url}'"
                )
                print(error_message)
                print(f"Request data: {json.dumps(data, indent=2)}")
                try:
                    error_response = exc.response.json()
                    print(f"Error response: {json.dumps(error_response, indent=2)}")
                except json.JSONDecodeError:
                    print(f"Error response (non-JSON): {exc.response.text}")
                return None
            except httpx.RequestError as exc:
                print(f"Request error: {exc}")
                if hasattr(exc, 'request'):
                    print(f"Request data: {json.dumps(data, indent=2)}")
                return None
            except Exception as exc:
                print(f"Unexpected error: {exc}")
                return None

            end_time = asyncio.get_event_loop().time()
            latency = end_time - start_time
            print(f"Request {data['request_id']} completed. Status: {response.status_code}. Time taken: {latency:.2f} seconds")
            self.latencies.append(latency)
            result = "Error processing response"
            try:
                if data["service"] == "stt":
                    response_text = response.text
                    try:
                        response_json = json.loads(response_text)
                        result = response_json.get("response", response_text)
                    except json.JSONDecodeError:
                        result = response_text
                elif data["service"] == "LLM":
                    if response.status_code == 200:
                        response_text = response.text
                        print("LLM raw response:", response_text)
                        try:
                            response_json = json.loads(response_text)
                            assistant_response = response_json.get("response", "")
                            print("Assistant response:", assistant_response)
                            result = "\n".join(re.findall(r'<ASSISTANT>:\s*(.*?)\n', assistant_response))
                            print("Processed LLM response text:", result)
                        except json.JSONDecodeError:
                            print("Error decoding JSON response.")
                            result = "Error processing response."
                else:
                    response_json = response.json()
                    result = response_json.get("response", {}).get("result", "No result")
            except Exception as err:
                print(f"Error processing response: {err}")  # Get the query content based on service type
            query_content = (
                data['input_file'] if data["service"] == "stt" 
                else data['inputData']["question"] if data["service"] == "LLM" 
                else data.get("query", "default_value")
            )

            self.results.append({
                "Test ID": data['test_id'],
                "request_id": data['request_id'],
                "Question Number": data['index'],
                "distributor(%)": self.distributor_map.get(query_content, 0),  # Add distributor percentage
                "prompt_count": self.prompt_counts.get(query_content, 0),  # Add prompt count
                "User ID": data['userId'],
                "Session ID": data['uniqueId'],
                "Query": data['input_file'] if data["service"] == "stt" else data['inputData']["question"] if data["service"] == "LLM" else data.get("query", "default_value"),
                "Latency (seconds)": latency,
                "Response": result,
                "Status Code": f"{response.status_code} {HTTPStatus(response.status_code).phrase}"
            })

            await self.task_queue.put(data['request_id'])
            return response, 200


    async def print_status(self):
        total_requests = len(self.query_list)
        completed_requests = 0
        while completed_requests < total_requests:
            await self.task_queue.get()
            completed_requests += 1
            print(f"Completed {completed_requests}/{total_requests} requests")
            self.task_queue.task_done()

    async def load_yaml_data(self):
        try:
            with open(self.payload_file_path, "r") as file:
                yaml_data = yaml.safe_load(file)

            if isinstance(yaml_data, dict):
                payloads = {key: value for key, value in yaml_data.items() if key.startswith("Payload")}
                return payloads
            else:
                print(f"Unexpected type for YAML data: {type(yaml_data)}")
                return {}
        except FileNotFoundError as e:
            print(f"Payload file not found: {e}")
            return {}
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file: {e}")
            return {}


    async def generate_query_list(self, payload_set):
        """
        Generate a list of queries based on the payload set and service configuration.
        """
        try:
            # Initial setup
            service = self.config_type
            deploy_id = self.config_id
            request_id = 1

            if not isinstance(payload_set, list):
                print(f"Invalid format for payload_set: {type(payload_set)}")
                return {"status": 400, "error": "Payload set must be a list"}

            # Update distributor map and initialize prompt counts
            try:
                self.distributor_map = {item['prompt']: item['distributor'] for item in payload_set}
                self.prompt_counts = {item['prompt']: 0 for item in payload_set}
            except KeyError as e:
                print(f"KeyError during distributor map update: {e}")
                return {"status": 400, "error": f"Missing key in payload: {e}"}

            # Generate distributed requests
            try:
                distributed_questions = self.calculate_distributed_requests(payload_set)
            except ValueError as e:
                print(f"Error in calculate_distributed_requests: {e}")
                return {"status": 500, "error": str(e)}

            # Count prompts in distributed questions
            for question in distributed_questions:
                if isinstance(question, dict) and "prompt" in question:
                    self.prompt_counts[question['prompt']] = self.prompt_counts.get(question['prompt'], 0) + 1

            question_count = len(payload_set)
            total_requests = len(distributed_questions)
            print("Number of distributed requests:", total_requests)

            # Generate a unique test ID
            test_id = f"{uuid.uuid4().hex[:6]}(input={question_count}, deploy_id={deploy_id}, service={service}, total_requests={total_requests})"
            print("Test ID:", test_id)

            # Process each question in distributed questions
            for question in distributed_questions:
                try:
                    if isinstance(question, dict) and "index" in question and "prompt" in question:
                        index = question.get("index", 0)
                        prompt = question.get("prompt", "")
                        print("Index:", index, "Prompt:", prompt)
                        inputData = {"question": prompt}
                        query_content = prompt
                        query = {
                            "index": index,
                            "clientApiKey": self.client_api_key,
                            "deployId": deploy_id,
                            "userId": str(self.user_id),
                            "uniqueId": str(self.session_id),
                            "request_id": request_id,
                            "test_id": test_id,
                            "service": service
                        }

                        if service == "stt":
                            query["input_file"] = query_content
                        elif service == "LLM":
                            query["inputData"] = inputData
                        else:
                            query["query"] = query_content

                        self.query_list.append(query)
                        request_id += 1
                    else:
                        print(f"Invalid question format: {question}")
                except Exception as e:
                    print(f"Error processing question: {e}")
                    return {"status": 500, "error": f"Error processing question: {str(e)}"}

            return {"status": 200, "message": "Query list generated successfully"}

        except Exception as e:
            print(f"Unexpected error: {e}")
            return {"status": 500, "error": f"Unexpected error occurred: {str(e)}"}

        

    async def test_async_endpoint(self):
        try:
            payloads = await self.load_yaml_data()
            total_start_time = asyncio.get_event_loop().time()
            all_throughputs = []
            all_latency_data = {}

            for payload_key, payload_set in payloads.items():
                set_start_time = asyncio.get_event_loop().time()
                await self.generate_query_list(payload_set)
                
                # Print the actual distribution of requests
                self.print_request_distribution(self.query_list)

                async with httpx.AsyncClient() as client:
                    semaphore = asyncio.Semaphore(self.concurrency_limit)
                    tasks = [self.fetch_async(client, self.endpoint, query_data, semaphore) 
                            for query_data in self.query_list]
                    status_task = asyncio.create_task(self.print_status())
                    cpu_task = asyncio.create_task(self.monitor_cpu())

                    await asyncio.gather(*tasks)
                    await self.task_queue.join()
                    status_task.cancel()
                    cpu_task.cancel()
                    try:
                        await status_task
                    except asyncio.CancelledError:
                        pass
                    try:
                        await cpu_task
                    except asyncio.CancelledError:
                        pass

                set_end_time = asyncio.get_event_loop().time()
                set_total_time = set_end_time - set_start_time
                set_throughput = len(self.query_list) / set_total_time if set_total_time > 0 else float('inf')
                all_throughputs.append(set_throughput)
                all_latency_data[payload_key] = self.latencies.copy()

                print(f"Total time for set {payload_key}: {set_total_time:.2f} seconds")
                print(f"Throughput for set {payload_key}: {set_throughput:.2f} requests/second")

                self.latencies.clear()
                self.query_list.clear()

            total_end_time = asyncio.get_event_loop().time()
            total_time = total_end_time - total_start_time
            print(f"Total time taken for all sets: {total_time:.2f} seconds")

            percentiles_to_calculate = [50, 75, 90.5, 95, 99]
            latency_percentiles = {}
            for key, latencies in all_latency_data.items():
                latency_percentiles[key] = self.calculate_latency_percentiles(latencies, percentiles_to_calculate)
                print(f"Latency Percentiles for {key}: {latency_percentiles[key]}")

            self.format_results(all_throughputs, latency_percentiles)
            return self.results, 200

        except Exception as e:
            print(f"An error occurred in test_async_endpoint: {e}")
            raise e

    from typing import List, Dict, Any

    def calculate_distributed_requests(self, payload_set: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Calculate the number of requests for each prompt based on its distributor percentage
        """
        distributed_queries = []

        try:
            # Validate that distributors sum to 100
            total_distribution = sum(item.get('distributor', 0) for item in payload_set)
            if total_distribution != 100:
                raise ValueError(f"Distributors must sum to 100, got {total_distribution}")

            for item in payload_set:
                # Calculate number of requests for this prompt
                num_requests = int((item['distributor'] / 100) * self.total_requests)

                # Create multiple copies of the same prompt based on distribution
                for _ in range(num_requests):
                    distributed_queries.append({
                        'index': item['index'],
                        'prompt': item['prompt'],
                        'distributor': item['distributor']
                    })

            # Shuffle the queries to avoid clustering
            import random
            random.shuffle(distributed_queries)
            return distributed_queries

        except ValueError as e:
            # Log the error message if needed
            print(f"Error: {e}")
            # Return a 500 status code with an error message
            return {"status": 500, "error": str(e)}

    def print_request_distribution(self, query_list: List[Dict[str, Any]]):
        """
        Print the actual distribution of requests for verification
        """
        distribution_count = {}
        for query in query_list:
            prompt = query['inputData']["question"] if self.config_type == "LLM" else query.get("query", "")
            distribution_count[prompt] = distribution_count.get(prompt, 0) + 1
        
        print("\nActual Request Distribution:")
        for prompt, count in distribution_count.items():
            percentage = (count / len(query_list)) * 100
            print(f"Prompt: {prompt}")
            print(f"Count: {count} ({percentage:.1f}%)\n")

    async def monitor_cpu(self):
        try:
            while True:
                cpu_percent = psutil.cpu_percent(interval=1)
                print(f"Current CPU usage: {cpu_percent}%")
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            print("CPU monitoring task was cancelled.")
    '''def calculate_average_latency(self):
        if not self.latencies:
            return 0.0
        return statistics.mean(self.latencies)'''

    def calculate_latency_percentiles(self, latencies, percentiles=None):
        if not latencies:
            return {}
        sorted_latencies = sorted(latencies)
        percentile_values = {p: np.percentile(sorted_latencies, p) for p in percentiles}
        return percentile_values
    
    def format_results(self, throughput, percentile_values):
        # Print throughput values
        for value in throughput:
            print(f"{value:.15f}\n")

        # Group results by Test ID
        grouped_results = {}
        for result in self.results:
            test_id = result.get("Test ID")
            if test_id not in grouped_results:
                grouped_results[test_id] = {"query_list": [], "count": 0}
            grouped_results[test_id]["query_list"].append(result)
            grouped_results[test_id]["count"] += 1

        # Format the updated results
        updated_results = {"timestamp": self.execution_timestamp}
        for i, (test_id, data) in enumerate(grouped_results.items()):
            # Check if we still have throughput values to assign
            throughput_value = throughput[i] if i < len(throughput) else ""

            # Build dynamic percentile latency string
            percentile_latency_str = ""
            for p, latency in percentile_values.get(f"Payload{i+1}", {}).items():
                percentile_latency_str += f"{p}th percentile: {latency:.2f} seconds\n"
            
            # Initialize payload list if not already done
            payload_key = f"Payload{i+1}"
            updated_results[payload_key] = []

            for entry in data["query_list"]:
                updated_results[payload_key].append({
                    "Test ID": test_id,  
                    "request_id": entry.get("request_id", ""),
                    "Question Number": entry.get("Question Number", ""),
                    "distributor(%)": entry.get("distributor(%)", 0),
                    "prompt_count": entry.get("prompt_count", 0),
                    "User ID": entry.get("User ID", ""),
                    "Session ID": entry.get("Session ID", ""),
                    "Input": entry.get("Query", ""),
                    "Latency (seconds)": entry.get("Latency (seconds)", ""),
                    "Response": entry.get("Response", ""),
                    "Throughput (requests/second)": throughput_value,  
                    "Percentile Latency (seconds)": percentile_latency_str,  
                    "Status Code": entry.get("Status Code", ""),
                })

        # Update the final results list
        self.results = updated_results
