from fastapi import APIRouter, HTTPException, Body, FastAPI
from fastapi import FastAPI, HTTPException
from ApplicationRoutes.authenticationRoutes import scheduler_instance



router = APIRouter()

app = FastAPI()




@router.post("/api/schedule_task")
async def schedule_task(request_data: dict = Body(...)):
    try:
        scheduler = scheduler_instance[request_data["sessionId"]]
        return  await scheduler.schedule_task(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
    
    

@router.post("/removeJob")
async def remove_task(request_data: dict = Body(...)):
    try:
        scheduler = scheduler_instance[request_data["sessionId"]]
        return  await scheduler.remove_task(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
    

@router.post("/api/getAllJobs")
async def getAllJobs(request_data: dict = Body(...)):
    try:
        scheduler = scheduler_instance[request_data["sessionId"]]
        return  await scheduler.getAllJobs(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
