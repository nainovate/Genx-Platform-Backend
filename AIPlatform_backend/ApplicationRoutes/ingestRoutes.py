from fastapi import APIRouter, Body, HTTPException
from AiManagement.ingest import IngestManager  # Adjust based on your folder structure
router = APIRouter()

ingest_instance = {}
    
@router.post("/api/get-config")
async def get_config_details(request_data: dict = Body(...)):
    session_id = request_data.get("sessionId")
    if not session_id:
        raise HTTPException(status_code=400, detail="Missing sessionId")

    if session_id not in ingest_instance:
        ingest_instance[session_id] = IngestManager()

    manager = ingest_instance[session_id]
    result = await manager.fetch_config_details(request_data)

    if result["status_code"] != 200:
        raise HTTPException(status_code=result["status_code"], detail=result["detail"])

    return result["data"]

