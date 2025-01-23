from fastapi import APIRouter, HTTPException, Body, FastAPI
from ApplicationRoutes.authenticationRoutes import authorization_instance, usecase_instance, space_instance

router = APIRouter()
@router.post("/api/getUseCases")
def getUseCases(request_data: dict = Body(...)):
    try:
        usecases = usecase_instance[request_data["sessionId"]]
        return usecases.getUseCases()
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))

@router.post("/api/createSpace")
def createSpace(request_data: dict = Body(...)):
    try:
        space = space_instance[request_data["sessionId"]]
        return space.createSpace(data = request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
    
@router.post("/api/getSpaces")
def getSpaces(request_data: dict = Body(...)):
    try:
        space = space_instance[request_data["sessionId"]]
        return space.getSpaces()
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
                
@router.post("/api/getUnassignedAdmins")
def getUnassignedAdmins(request_data: dict = Body(...)):
    try:
        auth = authorization_instance[request_data["sessionId"]]
        return auth.getUnassignedAdmins(spaceId = request_data["spaceId"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
    
@router.post("/api/assignSpace")
def assignSpace(request_data: dict = Body(...)):
    try:
        space = space_instance[request_data["sessionId"]]
        return space.assignSpace(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
    
@router.post("/api/getassignedAdmins")
def getassignedAdmins(request_data: dict = Body(...)):
    try:
        auth = authorization_instance[request_data["sessionId"]]
        return auth.getassignedAdmins(spaceId = request_data["spaceId"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))

@router.post("/api/unassignSpace")
def unassignSpace(request_data: dict = Body(...)):
    try:
        space = space_instance[request_data["sessionId"]]
        return space.unassignSpace(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))

@router.post("/api/unassignSpace")
def unassignSpace(request_data: dict = Body(...)):
    try:
        space = space_instance[request_data["sessionId"]]
        return space.unassignSpace(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))

@router.post("/api/getUnassignedUseCases")
def getUnassignedUseCases(request_data: dict = Body(...)):
    try:
        space = space_instance[request_data["sessionId"]]
        return space.getUnassignedUseCases(request_data["spaceId"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
    
@router.post("/api/getAssignedUseCases")
def getAssignedUseCases(request_data: dict = Body(...)):
    try:
        space = space_instance[request_data["sessionId"]]
        return space.getAssignedUseCases(request_data["spaceId"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))

@router.post("/api/assignUseCase")
def assignUseCase(request_data: dict = Body(...)):
    try:
        space = space_instance[request_data["sessionId"]]
        return space.assignUseCase(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))

@router.post("/api/unassignUseCase")
def unassignUseCase(request_data: dict = Body(...)):
    try:
        space = space_instance[request_data["sessionId"]]
        return space.unassignUseCase(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
    
@router.post("/api/deleteSpaces")
def deleteSpaces(request_data: dict = Body(...)):
    try:
        space = space_instance[request_data["sessionId"]]
        return space.deleteSpaces(request_data["spaceIds"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
 
@router.post("/api/updateSpaceName")
def updateSpaceName(request_data: dict = Body(...)):
    try:
        space = space_instance[request_data["sessionId"]]
        return space.updateSpaceName(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))

@router.post("/api/getAdminDetails")
def getAdminDetails(request_data: dict = Body(...)):
    try:
        auth = authorization_instance[request_data["sessionId"]]
        return auth.getAdminDetails()
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))

@router.post("/api/updateAdminDetails")
def updateAdminDetails(request_data: dict = Body(...)):
    try:
        auth = authorization_instance[request_data["sessionId"]]
        return auth.updateAdminDetails(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))