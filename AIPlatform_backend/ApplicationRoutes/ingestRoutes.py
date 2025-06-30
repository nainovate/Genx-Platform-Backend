from fastapi import APIRouter, Body, HTTPException
from ApplicationRoutes.authenticationRoutes import ingest_instance
router = APIRouter()


    
@router.post("/api/getingestConfig")
async def get_config_details(request_data: dict = Body(...)):
  print(f"Request Data: {request_data}")  
  try:
        session_id = request_data["sessionId"]
        print(f"Session ID: {session_id}")
        if session_id not in ingest_instance:
            raise ValueError(f"Session ID '{session_id}' not found in ingest_instance")
        ingest = ingest_instance[request_data["sessionId"]]
        print(f"Notification Instance: {ingest}")
        return await ingest.fetch_config_details()
  except Exception as e:
        return HTTPException(status_code=500, detail=str(e))

