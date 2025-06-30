from fastapi import APIRouter, Body, HTTPException, logger
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
  

@router.post("/api/getVectorConfig")
async def get_vector_config(request_data: dict = Body(...)):
    print(f"Request Data: {request_data}")
    try:
        session_id = request_data["sessionId"]
        print(f"Session ID: {session_id}")
        if session_id not in ingest_instance:
            raise ValueError(f"Session ID '{session_id}' not found in ingest_instance")

        ingest = ingest_instance[session_id]
        print(f"Ingest Instance: {ingest}")
        return await ingest.fetch_vector_config()

    except Exception as e:
        logger.error(f"Error in get_vector_config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    

@router.post("/api/getEmbeddingModels")
async def get_embedding_models(request_data: dict = Body(...)):
    print(f"Request Data: {request_data}")
    try:
        session_id = request_data["sessionId"]
        print(f"Session ID: {session_id}")
        if session_id not in ingest_instance:
            raise ValueError(f"Session ID '{session_id}' not found in ingest_instance")

        ingest = ingest_instance[session_id]
        print(f"Ingest Instance: {ingest}")
        return await ingest.fetch_embedding_models()

    except Exception as e:
        logger.error(f"Error in get_embedding_models: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@router.post("/api/getSplitterConfig")
async def get_splitter_config(request_data: dict = Body(...)):
    print(f"Request Data: {request_data}")
    try:
        session_id = request_data["sessionId"]
        print(f"Session ID: {session_id}")
        if session_id not in ingest_instance:
            raise ValueError(f"Session ID '{session_id}' not found in ingest_instance")

        ingest = ingest_instance[session_id]
        print(f"Ingest Instance: {ingest}")
        return await ingest.fetch_splitter_config()

    except Exception as e:
        logger.error(f"Error in get_splitter_config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
