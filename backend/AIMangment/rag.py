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

class Rag:
    def __init__(self, clientApiKey, deployId):
        self.AIServicesIp = os.getenv("AIServicesIp")
        self.AIServerPort = os.getenv("AIServerPort")
        self.endpoint = "http://"+self.AIServicesIp+":"+self.AIServerPort
        self.clientApiKey = clientApiKey
        self.deployId = deployId

    def ragRetrievalResult(self, userId, question, uniqueId):
        try:
            customer_data = {
                "user_id": userId,
                "client_api_key": self.clientApiKey,
                "deployId": self.deployId,
                "query": question,
                "uniqueId": uniqueId
            }
            response = requests.post(self.endpoint + "/aiService/rag", json = customer_data)

            if response.status_code == 200:
                result = response.json()["response"]
            else:
                result = ""
            return result
        except requests.exceptions.RequestException as e:
            print(f"Error occurred while making the request: {e}")
        except Exception as e:
            print(f"An error occurred in rag_retrival_result: {e}")

        return None

