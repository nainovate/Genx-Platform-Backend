from datetime import datetime, timedelta
from ApplicationRoutes.authenticationRoutes import authorization_instance, evaluation_instance
from fastapi import APIRouter, BackgroundTasks, Body, FastAPI, HTTPException, Query, status, Request
from pydantic import ValidationError
from pymongo import MongoClient
from ApplicationManagment.evaluation import Evaluation


# API router instance
router = APIRouter()
    
@router.post("/api/evaluation")
async def get_evaluation_results(request_data: dict = Body(...)):
    try:
        evaluation = evaluation_instance[request_data["sessionId"]]
        return await evaluation.get_evaluation_results(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))

@router.post("/api/metrics")
async def calculate_metrics(request_data: dict, background_tasks: BackgroundTasks):
    try:
        evaluation = evaluation_instance[request_data["sessionId"]]
        return   evaluation.calculate_metrics(request_data["data"], background_tasks)
    except Exception as e:
        print("error route", e)
        return HTTPException(status_code=500, detail=str(e))    
    
@router.post("/api/benchmark/start")
async def start_benchmark_task(request_data: dict = Body(...)):
    try:
        evaluation = evaluation_instance[request_data["sessionId"]]
        return await evaluation.start_benchmark_task(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))        

    
@router.get("/api/status/fetch")
async def check_process_status(
    process_id: str = Query(...), 
    service: str = Query(...), 
    sessionId: str = Query(...)
):
    try:
        # Retrieve the evaluation instance using sessionId
        evaluation = evaluation_instance[sessionId]
        
        # Create the request_data structure as expected by the check_process_status method
        request_data = {
            "process_id": process_id,
            "service": service
        }
        
        # Call the method with the required data
        return await evaluation.check_process_status(request_data)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@router.post("/api/results/fetch")
async def check_process_results(request_data: dict = Body(...)):
    try:
        evaluation = evaluation_instance[request_data["sessionId"]]
        return await evaluation.check_process_results(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))         

@router.post("/api/view/result")
async def view_result(request_data: dict = Body(...)):
    try:
        print("request data route", request_data["data"])
        evaluation = evaluation_instance[request_data["sessionId"]]
        return await evaluation.view_result(request_data["data"])
    except Exception as e:
        print("error", e)
        return HTTPException(status_code=500, detail=str(e))      
    
@router.post("/api/view/status")
async def view_status_by_userid(request_data: dict = Body(...)):
    try:
        evaluation = evaluation_instance[request_data["sessionId"]]
        return await  evaluation.view_status_by_userid(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))     
    
@router.post("/api/results/download")
async def download_excel(request_data: dict, background_tasks: BackgroundTasks):
    try:
        evaluation = evaluation_instance[request_data["sessionId"]]
        return await evaluation.download_excel(request_data["data"],  background_tasks)
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))     
    
@router.post("/api/reset")
async def stop_task(request_data: dict = Body(...)):
    try:
        evaluation = evaluation_instance[request_data["sessionId"]]
        return await evaluation.stop_task(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))      

@router.post("/api/metric/results")
async def get_metrics(request_data: dict = Body(...)):
    try:
        evaluation = evaluation_instance[request_data["sessionId"]]
        return await  evaluation.get_metrics(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))              
    
@router.post("/api/metric/fetch")
async def check_metric_results(request_data: dict = Body(...)):
    try:
        evaluation = evaluation_instance[request_data["sessionId"]]
        return await evaluation.check_metric_results(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))    
    
@router.post("/api/update-metric-ranges")
async def update_ranges(request_data: dict = Body(...)):
    try:
        evaluation = evaluation_instance[request_data["sessionId"]]
        return await  evaluation.update_ranges(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))    
    
@router.post("/api/check/processName")
async def check_process_name(request_data: dict = Body(...)):
    try:
        evaluation = evaluation_instance[request_data["sessionId"]]
        return await  evaluation.check_process_name(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))     

