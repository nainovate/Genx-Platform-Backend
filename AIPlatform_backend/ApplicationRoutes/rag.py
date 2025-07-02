import os
from fastapi import HTTPException
import logging
from AiManagement.rag import *
from Database.organizationDataBase import *
import requests


# Set up logging
projectDirectory = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
logDir = os.path.join(projectDirectory, "logs")
logBackendDir = os.path.join(logDir, "backend")
logFilePath = os.path.join(logBackendDir, "logger.log")

# Configure logging settings
logging.basicConfig(
    filename=logFilePath,  # Set the log file name
    level=logging.INFO,  # Set the desired log level (e.g., logging.DEBUG, logging.INFO)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

global answers
answers = {}

class RAG:
    def __init__(self, userId: str):
        self.userId = userId
        self.RagRetrival = None
        self.RagRetrival = Rag()
 
    def rag(self, data: dict):
        try:
            # res = self.RagRetrival.ragRetrievalResult(userId=self.userId, question=data["query"], clientApiKey= data["clientApiKey"], deployId=data["deployId"])
            # return res
            orgId = data["orgId"]
            deployId = data["deployId"]
            organizationDB = OrganizationDataBase(orgId)
            url = organizationDB.getLangflowUrl(deployId=deployId)
            data = {
                "input_value": data["query"],
                "input_type": "text",
                "output_type": "text",
            }
            response = requests.post(url, json = data)
            output = response.json()['outputs'][0]['outputs'][0]['outputs']['text']['message']
            return {"responseText":output}
        except HTTPException as http_exception:
            raise http_exception  # Re-raise HTTPException for proper response
        except Exception as e:
            print(str(e))
            logger.error(f"an error occured {str(e)}")
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
        
    def getQuestionCards(self, orgId, taskId):
        try:
            orgId = orgId
            taskId = taskId
            organizationDB = OrganizationDataBase(orgId)
            questions, status_code = organizationDB.getQuestionCards(taskId)
            if status_code == 404:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": f"Questionss Not Found for taskId: {orgId}"
                }
            elif not status_code == 200:
                return {
                    "status_code": status_code,
                    "detail": "Internal server error",
                }
            return {
                "status_code": status.HTTP_200_OK,
                "questions":{taskId:questions}
            }

        except HTTPException as http_exception:
            raise http_exception  # Re-raise HTTPException for proper response
        except Exception as e:
            print(str(e))
            logger.error(f"an error occured {str(e)}")
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
