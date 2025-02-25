
from ApplicationRoutes.authenticationRoutes import finetuning_instance
from fastapi import APIRouter, Body,HTTPException,status


router = APIRouter()


@router.post("/api/finetune")
async def view_result(request_data: dict = Body(...)):
    try:
        session_id = request_data.get("sessionId")
        if not session_id:
            return{
                "status_code":status.HTTP_400_BAD_REQUEST,
                "detail":"Missing required 'sessionId' in the request data."
            }
        
        # Check if the sessionId exists in prompts_instance
        if session_id not in finetuning_instance:
            return{
                "status_code":status.HTTP_403_FORBIDDEN,
                "detail":f"unauthorized access , Session expired"
            }
        required_fields = ["sessionId","data"]
        missing_fields = [field for field in required_fields if field not in request_data]
        if missing_fields:
            
            return {
                "status_code": status.HTTP_400_BAD_REQUEST,
                "detail": f"Missing required fields: {', '.join(missing_fields)}."
            }
        finetune = finetuning_instance[session_id]
        data = request_data.get("data")
        return await finetune.fine_tune_model(data)
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))  


@router.post("/api/getmetricresult")
def view_result(request_data: dict = Body(...)):
    try:
        session_id = request_data.get("sessionId")
        if not session_id:
            return{
                "status_code":400,
                "detail":"Missing required 'sessionId' in the request data."
            }
        
        # Check if the sessionId exists in prompts_instance
        if session_id not in finetuning_instance:
            return{
                "status_code":403,
                "detail":f"unauthorized access , Session expired"
            }
        required_fields = ["sessionId","data"]
        missing_fields = [field for field in required_fields if field not in request_data]
        if missing_fields:
            
            return {
                "status_code": 400,
                "detail": f"Missing required fields: {', '.join(missing_fields)}."
            }
        finetune = finetuning_instance[session_id]
        data = request_data.get("data")
        return finetune.view_metricresult(data)
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))  
    


@router.post("/api/getAllmetricresult")
def view_result(request_data: dict = Body(...)):
    try:
        session_id = request_data.get("sessionId")
        if not session_id:
            return{
                "status_code":400,
                "detail":"Missing required 'sessionId' in the request data."
            }
        
        # Check if the sessionId exists in prompts_instance
        if session_id not in finetuning_instance:
            return{
                "status_code":403,
                "detail":f"unauthorized access , Session expired"
            }
        required_fields = ["sessionId","data"]
        missing_fields = [field for field in required_fields if field not in request_data]
        if missing_fields:
            
            return {
                "status_code": 400,
                "detail": f"Missing required fields: {', '.join(missing_fields)}."
            }
        finetune = finetuning_instance[session_id]
        data = request_data.get("data")
        
        # Call the function to fetch metrics by user_Id
        return finetune.view_allmetricresult(data)
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))  
    



@router.post("/api/getstatus")
def get_status(request_data: dict = Body(...)):
    try:
        session_id = request_data.get("sessionId")
        if not session_id:
            return{
                "status_code":400,
                "detail":"Missing required 'sessionId' in the request data."
            }
        
        # Check if the sessionId exists in prompts_instance
        if session_id not in finetuning_instance:
            return{
                "status_code":403,
                "detail":f"unauthorized access , Session expired"
            }
        required_fields = ["sessionId","data"]
        missing_fields = [field for field in required_fields if field not in request_data]
        if missing_fields:
            
            return {
                "status_code": 400,
                "detail": f"Missing required fields: {', '.join(missing_fields)}."
            }
        finetune = finetuning_instance[session_id]
        data = request_data.get("data")
        
        # Call the function to fetch metrics by user_Id
        return finetune.get_status(data)
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e)) 




@router.post("/api/stopfinetune")
def get_status(request_data: dict = Body(...)):
    try:
        session_id = request_data.get("sessionId")
        if not session_id:
            return{
                "status_code":400,
                "detail":"Missing required 'sessionId' in the request data."
            }
        
        # Check if the sessionId exists in prompts_instance
        if session_id not in finetuning_instance:
            return{
                "status_code":403,
                "detail":f"unauthorized access , Session expired"
            }
        required_fields = ["sessionId","data"]
        missing_fields = [field for field in required_fields if field not in request_data]
        if missing_fields:
            
            return {
                "status_code": 400,
                "detail": f"Missing required fields: {', '.join(missing_fields)}."
            }
        finetune = finetuning_instance[session_id]
        data = request_data.get("data")
        
        # Call the function to fetch metrics by user_Id
        return finetune.cancel_fine_tune(data)
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e)) 