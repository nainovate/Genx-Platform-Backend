import requests
from fastapi import FastAPI, Request, Depends, HTTPException, Body
import os
import logging
import yaml
import time

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

class Rag:
    def __init__(self):
        self.AIServicesIp = os.getenv("AIServicesIp")
        self.AIServerPort = os.getenv("AIServerPort")
        self.endpoint = "http://"+self.AIServicesIp+":"+self.AIServerPort

    def ragRetrievalResult(self, userId, question, clientApiKey, deployId):
        try:
            customer_data = {
                "user_id": userId,
                "client_api_key": clientApiKey,
                "deployId": deployId,
                "query": question,
            }
            response = requests.post(self.endpoint + "/aiService/rag", json = customer_data)

            response.raise_for_status()
                
            # Get job ID from response
            job_data = response.json()
            job_id = job_data['job_id']


            while True:
                # Get job status
                status_response = requests.get(f"{self.endpoint}/job/{job_id}")
                status_response.raise_for_status()
                
                status_data = status_response.json()
                current_status = status_data['status']

                # Check if job is completed or failed
                if current_status == "completed":
                    result = status_data["result"]["response"]
                    return {
                        "status":200,
                        "responseText":result.get("response_txt",""),
                        }
                elif current_status == "failed":
                    result = ""
                    return {
                        "status":400,
                        "responseText":result,
                        }
                elif current_status == "cancelled":
                    result = ""
                    raise Exception("Job was cancelled")                
                # Wait before polling again
                time.sleep(5)
        except requests.exceptions.RequestException as e:
            print(f"Error occurred while making the request: {e}")
        except Exception as e:
            print(f"An error occurred in rag_retrival_result: {e}")

        return None