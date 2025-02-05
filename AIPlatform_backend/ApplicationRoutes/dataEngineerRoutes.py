from fastapi import APIRouter, HTTPException, Body, FastAPI
from ApplicationRoutes.authenticationRoutes import prompts_instance,payload_instance,model_instance,dataset_instance, task_instance

router = APIRouter()


# authentication_instances["resetPassword"] = Authentication()
@router.post("/api/getAllTasks")
async def getRoleTasks(request_data: dict = Body(...)):
    try:
        task = task_instance[request_data["sessionId"]]
        return task.getTasks(request_data["data"])
    except KeyError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/addPrompt")
async def addPrompt(request_data: dict = Body(...)):
    try:
        # Get the sessionId from the request
        session_id = request_data["sessionId"]
        data = request_data["data"]
        print("data",data)
        print("session ID",session_id)
        
        # Check if the sessionId exists in prompts_instance
        if session_id not in prompts_instance: 
            raise HTTPException(status_code=404, detail=f"Session ID '{session_id}' not found.")
        
        # Remove sessionId from the request data to pass the rest to the addPrompt function
        request_data.pop("sessionId", None)  # Remove sessionId if exists
        
        # Access the corresponding Prompts instance
        prompts = prompts_instance[session_id]
        print("data",data)
        # Pass the filtered data (excluding sessionId) to addPrompt
        return prompts.addPrompt(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/getPrompts")
async def getPrompts(request_data: dict = Body(...)):
    """
    Fetches prompts data for the given session ID.

    :param request_data: A dictionary containing the sessionId and additional data.
    :return: The response from the `getPromptsData` method or an error message.
    """
    try:
        # Ensure 'sessionId' is provided in the request data
        session_id = request_data.get("sessionId")
        if not session_id:
            raise HTTPException(
                status_code=400,
                detail="Missing required 'sessionId' in the request data."
            )
        
        # Check if the sessionId exists in prompts_instance
        if session_id not in prompts_instance:
            raise HTTPException(
                status_code=404,
                detail=f"Session ID '{session_id}' not found."
            )
        
        # Access the corresponding Prompts instance
        prompts = prompts_instance[session_id]
        
        # Remove sessionId from the request data before passing it to getPromptsData
        request_data.pop("sessionId", None)
        
        # Call the `getPromptsData` method of the corresponding instance
        response = prompts.getPromptsData()
        return response

    except KeyError as e:
        # Handle missing keys in the data
        raise HTTPException(
            status_code=400,
            detail=f"Missing or invalid data: {str(e)}"
        )

    except HTTPException as e:
        # Re-raise HTTP exceptions to preserve status code and detail
        raise e

    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.post("/api/updatePrompt")
async def updatePrompt(request_data: dict = Body(...)):
    """
    Fetches prompts data for the given session ID.

    :param request_data: A dictionary containing the sessionId and additional data.
    :return: The response from the `getPromptsData` method or an error message.
    """
    try:
        # Ensure 'sessionId' is provided in the request data
        session_id = request_data.get("sessionId")
        if not session_id:
            raise HTTPException(
                status_code=400,
                detail="Missing required 'sessionId' in the request data."
            )
        
        # Check if the sessionId exists in prompts_instance
        if session_id not in prompts_instance:
            raise HTTPException(
                status_code=404,
                detail=f"Session ID '{session_id}' not found."
            )
        
        # Access the corresponding Prompts instance
        prompts = prompts_instance[session_id]
        
        # Remove sessionId from the request data before passing it to getPromptsData
        request_data.pop("sessionId", None)
        
        # Call the `getPromptsData` method of the corresponding instance
        response = prompts.updatePrompt(data=request_data)
        return response

    except KeyError as e:
        # Handle missing keys in the data
        raise HTTPException(
            status_code=400,
            detail=f"Missing or invalid data: {str(e)}"
        )

    except HTTPException as e:
        # Re-raise HTTP exceptions to preserve status code and detail
        raise e

    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )    
@router.post("/api/deletePrompt")
async def deletePrompt(request_data: dict = Body(...)):
    
    try:
        # Ensure 'sessionId' is provided in the request data
        session_id = request_data.get("sessionId")
        if not session_id:
            raise HTTPException(
                status_code=400,
                detail="Missing required 'sessionId' in the request data."
            )
        
        # Check if the sessionId exists in prompts_instance
        if session_id not in prompts_instance:
            raise HTTPException(
                status_code=404,
                detail=f"Session ID '{session_id}' not found."
            )
        
        # Access the corresponding Prompts instance
        prompts = prompts_instance[session_id]
        
        # Remove sessionId from the request data before passing it to getPromptsData
        request_data.pop("sessionId", None)
        data = request_data.get("data")
        
        # Call the `getPromptsData` method of the corresponding instance
        response = prompts.deletePrompt(data)
        return response

    except KeyError as e:
        # Handle missing keys in the data
        raise HTTPException(
            status_code=400,
            detail=f"Missing or invalid data: {str(e)}"
        )

    except HTTPException as e:
        # Re-raise HTTP exceptions to preserve status code and detail
        raise e

    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )       

@router.post("/api/addPayload")
async def addPayload(request_data: dict = Body(...)):
   
    try:
        # Ensure 'sessionId' is provided in the request data
        session_id = request_data.get("sessionId")
        if not session_id:
            raise HTTPException(
                status_code=400,
                detail="Missing required 'sessionId' in the request data."
            )
        
        # Check if the sessionId exists in prompts_instance
        if session_id not in payload_instance:
            raise HTTPException(
                status_code=404,
                detail=f"Session ID '{session_id}' not found."
            )
        
        # Access the corresponding Prompts instance
        payload = payload_instance[session_id]
        
        # Remove sessionId from the request data before passing it to getPromptsData
        request_data.pop("sessionId", None)
        data = request_data.get("data")
        
        # Call the `getPromptsData` method of the corresponding instance
        response = payload.addPayload(data)
        return response

    except KeyError as e:
        # Handle missing keys in the data
        raise HTTPException(
            status_code=400,
            detail=f"Missing or invalid data: {str(e)}"
        )

    except HTTPException as e:
        # Re-raise HTTP exceptions to preserve status code and detail
        raise e

    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )       
@router.post("/api/getPayloaddetails")
async def getPayloadDetails(request_data: dict = Body(...)):
   
    try:
        # Ensure 'sessionId' is provided in the request data
        session_id = request_data.get("sessionId")
        if not session_id:
            raise HTTPException(
                status_code=400,
                detail="Missing required 'sessionId' in the request data."
            )
        
        # Check if the sessionId exists in prompts_instance
        if session_id not in payload_instance:
            raise HTTPException(
                status_code=404,
                detail=f"Session ID '{session_id}' not found."
            )
        
        # Access the corresponding Prompts instance
        payload = payload_instance[session_id]
        
        # Remove sessionId from the request data before passing it to getPromptsData
        request_data.pop("sessionId", None)
        
        # Call the `getPromptsData` method of the corresponding instance
        response = payload.getPayloadDetails()
        return response

    except KeyError as e:
        # Handle missing keys in the data
        raise HTTPException(
            status_code=400,
            detail=f"Missing or invalid data: {str(e)}"
        )

    except HTTPException as e:
        # Re-raise HTTP exceptions to preserve status code and detail
        raise e

    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )    

@router.post("/api/deletePayload")
async def deletePayload(request_data: dict = Body(...)):
    try:
        # Ensure 'sessionId' is provided in the request data
        session_id = request_data.get("sessionId")
        if not session_id:
            raise HTTPException(
                status_code=400,
                detail="Missing required 'sessionId' in the request data."
            )
        
        # Check if the sessionId exists in prompts_instance
        if session_id not in payload_instance:
            raise HTTPException(
                status_code=404,
                detail=f"Session ID '{session_id}' not found."
            )
        # Access the corresponding Prompts instance
        payloads = payload_instance[session_id]
        # Remove sessionId from the request data before passing it to getPromptsData
        request_data.pop("sessionId", None)
        data = request_data.get("data")
        # Call the `getPromptsData` method of the corresponding instance
        response = payloads.deletePayload(data)
        return response

    except KeyError as e:
        # Handle missing keys in the data
        raise HTTPException(
            status_code=400,
            detail=f"Missing or invalid data: {str(e)}"
        )

    except HTTPException as e:
        # Re-raise HTTP exceptions to preserve status code and detail
        raise e

    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )             


@router.post("/api/addModel")
async def addModel(request_data: dict = Body(...)):
   
    try:
        # Ensure 'sessionId' is provided in the request data
        session_id = request_data.get("sessionId")
        if not session_id:
            raise HTTPException(
                status_code=400,
                detail="Missing required 'sessionId' in the request data."
            )
        
        # Check if the sessionId exists in prompts_instance
        if session_id not in payload_instance:
            raise HTTPException(
                status_code=404,
                detail=f"Session ID '{session_id}' not found."
            )
        
        # Access the corresponding Prompts instance
        model = model_instance[session_id]
        
        # Remove sessionId from the request data before passing it to getPromptsData
        request_data.pop("sessionId", None)
        data =request_data.get("data")
        
        # Call the `getPromptsData` method of the corresponding instance
        response = model.addModel(data)
        return response

    except KeyError as e:
        # Handle missing keys in the data
        raise HTTPException(
            status_code=400,
            detail=f"Missing or invalid data: {str(e)}"
        )

    except HTTPException as e:
        # Re-raise HTTP exceptions to preserve status code and detail
        raise e

    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )       
    
@router.post("/api/getModeldetails")
async def getModeldetails(request_data: dict = Body(...)):
   
    try:
        print("request data", request_data)
        # Ensure 'sessionId' is provided in the request data
        session_id = request_data.get("sessionId")
        if not session_id:
            raise HTTPException(
                status_code=400,
                detail="Missing required 'sessionId' in the request data."
            )
        
        # Check if the sessionId exists in prompts_instance
        if session_id not in payload_instance:
            raise HTTPException(
                status_code=403,
                detail=f"Unauthorized access, session expired."
            )
        
        # Access the corresponding Prompts instance
        model = model_instance[session_id]
        
        # Remove sessionId from the request data before passing it to getPromptsData
        request_data.pop("sessionId", None)
        data=request_data.get("data")
        # Call the `getPromptsData` method of the corresponding instance
        response = model.getModeldetails(data)
        print("response", response)
        return response

    except KeyError as e:
        # Handle missing keys in the data
        raise HTTPException(
            status_code=400,
            detail=f"Missing or invalid data: {str(e)}"
        )

    except HTTPException as e:
        # Re-raise HTTP exceptions to preserve status code and detail
        raise e

    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )          
    
  
@router.post("/api/deleteModel")
async def deleteModel(request_data: dict = Body(...)):
    try:
        # Ensure 'sessionId' is provided in the request data
        session_id = request_data.get("sessionId")
        if not session_id:
            raise HTTPException(
                status_code=400,
                detail="Missing required 'SessionId' in the request data."
            )
        
        # Check if the sessionId exists in prompts_instance
        if session_id not in payload_instance:
            raise HTTPException(
                status_code=403,
                detail=f"Unauthorized access, Session expired."
            )
        # Access the corresponding Prompts instance
        models = model_instance[session_id]
        # Remove sessionId from the request data before passing it to getPromptsData
        request_data.pop("sessionId", None)
        data = request_data.get("data")
        # Call the `getPromptsData` method of the corresponding instance
        response = models.deleteModel(data)
        return response

    except KeyError as e:
        # Handle missing keys in the data
        raise HTTPException(
            status_code=400,
            detail=f"Missing or invalid data: {str(e)}"
        )

    except HTTPException as e:
        # Re-raise HTTP exceptions to preserve status code and detail
        raise e

    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )             
  

@router.post("/api/get_datasets")
def get_dataset_Details(request_data: dict):
    try:
        session_id = request_data.get("sessionId")
        if not session_id:
            return {
                "status_code": 400,
                "detail": "Missing required 'sessionId' in the request data."
            }

        if session_id not in dataset_instance:
            return {
                "status_code": 403,
                "detail": f"Unauthorized access, Session expired."
            }
        required_fields = ["sessionId","data"]
        missing_fields = [field for field in required_fields if field not in request_data]
        if missing_fields:
            
            return {
                "status_code": 400,
                "detail": f"Missing required fields: {', '.join(missing_fields)}."
            }
        dataset = dataset_instance[session_id]
        # Call the `get_dataset_Details` method of the corresponding instance
        return dataset.get_dataset_Details(request_data["data"])

    except Exception as e:
        return {
            "status_code": 500,
            "detail": f"Internal server error: {str(e)}"
        }

@router.post("/api/addDataset")
def addDataset(request_data: dict):
    try:
        session_id = request_data.get("sessionId")
        if not session_id :
            return {
                "status_code": 400,
                "detail": "Missing required 'sessionId' in the request data."
            }

        if session_id not in dataset_instance:
            return {
                "status_code": 403,
                "detail": f"Unauthorized access, session expired."
            }
        required_fields = ["sessionId","data"]
        missing_fields = [field for field in required_fields if field not in request_data]
        if missing_fields:
            
            return {
                "status_code": 400,
                "detail": f"Missing required fields: {', '.join(missing_fields)}."
            }
        dataset = dataset_instance[session_id]
        # Call the `add_dataset` method of the corresponding instance
        return dataset.add_dataset(request_data["data"])

    except Exception as e:
        return {
            "status_code": 500,
            "detail": f"Internal server error: {str(e)}"
        }

@router.post("/api/deletedataset")
def deletedataset(request_data: dict):
    try:
        session_id = request_data.get("sessionId")
        if not session_id :
            return {
                "status_code": 400,
                "detail": "Missing required 'sessionId' in the request data."
            }

        if session_id not in dataset_instance:
            return {
                "status_code": 403,
                "detail": f"Unauthorized access, session expired."
            }
        required_fields = ["sessionId","data"]
        missing_fields = [field for field in required_fields if field not in request_data]
        if missing_fields:
            
            return {
                "status_code": 400,
                "detail": f"Missing required fields: {', '.join(missing_fields)}."
            }
        dataset = dataset_instance[session_id]
        
        request_data.pop("sessionId", None)
        data = request_data.get("data")
        # Call the `deletedataset` method of the corresponding instance
        return dataset.deletedataset(data)

    except Exception as e:
        return {
            "status_code": 500,
            "detail": f"Internal server error: {str(e)}"
        }



