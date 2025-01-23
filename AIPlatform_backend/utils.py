# models.py
from datetime import datetime
from pydantic import BaseModel, validator
from typing import Any, Dict, List, Union

class Payload(BaseModel):
    payload_file_path: str
    # payload_path:str
    process_name: str
    user_id: str
    session_id: str
    config_type: str
    config_id: List[Dict[str, str]]
    client_api_key: str

class BenchPayload(BaseModel):
    payload_file_path: str
    process_name: str
    user_id: str
    session_id: str
    config_type: str
    config_id: List[Dict[str, str]]
    client_api_key: str
    total_requests: int
    
class ScheduleDetails(BaseModel):
    service: str
    user_id: str
    session_id: str
    schedule_time: datetime
   
class LoginDetails(BaseModel):
    service: str
    user_id: str
    login_time: datetime
    
class MetricsPayload(BaseModel):
    payload_file_path: Union[str,Dict[str,Any]]
    user_id: str
    process_id: str
    metrics: List[str]
    process_name : str

class ModelStatus(BaseModel):
    metric_id : str
    model_id: str
    model_name : str
    status: str
class MetricStatus(BaseModel):
    model_id: str
    status: str
    

class RequestDetails(BaseModel):
    process_id : str
    service : str
class MetricRequest(BaseModel):
    metric_id: str
class viewDetails(BaseModel):
    model_id: str
    process_id: str
    service:str
class ResultDetails(BaseModel):
    service : str
    user_id: str
    
class Pagination(BaseModel):
    service : str
    user_id: str
    page : int
    page_size : int
    orgId:str

class metric(BaseModel):
    user_id: str
    page : int
    page_size : int

class RangeUpdateRequest(BaseModel):
    metric_id: str
    metric_name: str
    new_ranges: Dict[str, Any]


class StatusRecord(BaseModel):
    user_id: str
    process_id: str
    models: List[ModelStatus]
    overall_status: str
    start_time: datetime
    end_time: datetime = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

class MetricStatusRecord(BaseModel):
    user_id: str
    process_id: str
    metric_id : str
    models: List[MetricStatus]
    overall_status : str
    start_time: datetime
    end_time: datetime = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()