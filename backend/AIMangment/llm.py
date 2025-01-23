import requests
from fastapi import FastAPI, Request, Depends, HTTPException, Body
import os
import logging
import yaml

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

class LLM:
    def __init__(self, clientApiKey, deployId):
        self.AIServicesIp = os.getenv("AIServicesIp")
        self.AIServerPort = os.getenv("AIServerPort")
        self.endpoint = "http://"+self.AIServicesIp+":"+self.AIServerPort
        self.clientApiKey = clientApiKey
        self.deployId = deployId

    def llmAcceleratorResult(self, userId, inputData: dict):
        try:
            customer_data = {
                "userId": userId,
                "clientApiKey": self.clientApiKey,
                "deployId": self.deployId,
                "inputData": inputData
            }

            response = requests.post(self.endpoint + "/accelerator/server", json = customer_data)

            # response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
            if response.status_code == 200:
                result = response.json()["response"]
            else:
                result = ""
            return result
            

        except requests.exceptions.RequestException as e:
            print(f"Error occurred while making the request: {e}")
        except Exception as e:
            print(f"An error occurred in llm_accelerator_result: {e}")

        return None
    
    def chatReset(self, user):
        try:
            data = {"clientApiKey": self.clientApiKey, "userId": user, "deployId": self.deployId} 
            if not user:
                raise HTTPException(status_code=400, detail="Invalid request data")
            response = requests.post(self.endpoint + "/accelerator/server", json=data)
            if response.status_code == 200:
                return response.status_code
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")