from fastapi import APIRouter, HTTPException, Body, status
from ApplicationRoutes.rag import *
from ApplicationRoutes.authenticationRoutes import task_instance
router = APIRouter()

rag_instance = {}
application_instance = {}

@router.post("/chatbot/initializeInstances")
def initializeInstances(request_data: dict = Body(...)):
    try:
        sessionId = request_data["sessionId"]
        deployId = request_data["data"].get("deployId","")
        userId = request_data["data"].get("userId","")
        key = f"{sessionId}_{deployId}"
        rag_instance[key] = RAG(userId=userId)
        return{
            "status_code": status.HTTP_200_OK
        }
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))

@router.post("/chatbot/getTaskIds")
def getAgentIds(request_data: dict = Body(...)):
    try:
        sessionId = request_data["sessionId"]
        tasks = task_instance[sessionId]
        return tasks.getTaskIds()
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))

@router.post("/chatbot/getQuestionCards")
def getQuestionCards(request_data: dict = Body(...)):
    try:
        sessionId = request_data["sessionId"]
        orgId = request_data["data"].get("orgId","")
        deployId = request_data["data"].get("deployId","")
        taskId = request_data["data"].get("taskId","")
        key = f"{sessionId}_{deployId}"
        rag= rag_instance[key]
        return rag.getQuestionCards(orgId=orgId, taskId=taskId)
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))

@router.post("/chatbot/rag")
def rag(request_data: dict = Body(...)):
    try:
        sessionId = request_data["sessionId"]
        deployId = request_data["data"].get("deployId","")
        key = f"{sessionId}_{deployId}"
        Rag = rag_instance[key]
        return Rag.rag(data = request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
    
