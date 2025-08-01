import asyncio
from datetime import datetime, timedelta
import json
import logging
import os
import uuid
from ApplicationRoutes.authenticationRoutes import authorization_instance, evaluation_instance
from fastapi import APIRouter, BackgroundTasks, Body, FastAPI, HTTPException, Query, status, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import ValidationError
from pymongo import MongoClient
from ApplicationManagment.evaluation import Evaluation
from utils import BenchPayload, LoginDetails, MetricRequest, MetricsPayload, Pagination, Payload, RequestDetails, ResultDetails, ScheduleDetails, metric, viewDetails

# API router instance
router = APIRouter()
    
@router.post("/api/evaluation")
async def get_evaluation_results(request_data: dict = Body(...)):
    try:
        print("request_data", request_data)
        evaluation = evaluation_instance[request_data["sessionId"]]
        print("111")
        print("evaluation", evaluation)
        return await evaluation.get_evaluation_results(request_data["data"])
    except Exception as e:
        print("error ", e)
        return HTTPException(status_code=500, detail=str(e))

@router.post("/api/metrics")
async def calculate_metrics(request_data: dict, background_tasks: BackgroundTasks):
    try:
        evaluation = evaluation_instance[request_data["sessionId"]]
        return  await evaluation.calculate_metrics(request_data["data"], background_tasks)
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))    
    
@router.post("/api/benchmark/start")
async def start_benchmark_task(request_data: dict = Body(...)):
    try:
        evaluation = evaluation_instance[request_data["sessionId"]]
        return await evaluation.start_benchmark_task(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))        

    
@router.post("/api/status/fetch")
async def check_process_status(request_data: dict = Body(...)):
    try:
        evaluation = evaluation_instance[request_data["sessionId"]]
        return await evaluation.check_process_status(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))      
    
@router.post("/api/results/fetch")
async def check_process_results(request_data: dict = Body(...)):
    try:
        evaluation = evaluation_instance[request_data["sessionId"]]
        print("evaluation", evaluation)
        return await evaluation.check_process_results(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))         

@router.post("/api/view/result")
async def view_result(request_data: dict = Body(...)):
    try:
        print("request_data", request_data)
        evaluation = evaluation_instance[request_data["sessionId"]]
        return await evaluation.view_result(request_data["data"])
    except Exception as e:
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

