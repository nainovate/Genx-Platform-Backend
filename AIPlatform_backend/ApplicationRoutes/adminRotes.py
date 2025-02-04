from fastapi import APIRouter, HTTPException, Body, FastAPI
from ApplicationRoutes.authenticationRoutes import authorization_instance, space_instance, organization_instance

router = APIRouter()

@router.post("/api/getOrganizationsforUsers")
async def getOrganizationsforUsers(request_data: dict = Body(...)):
    try:
        org = organization_instance[request_data["sessionId"]]
        return  org.getOrganizationsforUsers()
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e)) 
    
@router.post("/api/createSpace")
async def createSpace(request_data: dict = Body(...)):
    try:
        space = space_instance[request_data["sessionId"]]
        return  space.createSpace(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
    
@router.post("/api/removeSpace")
async def removeSpace(request_data: dict = Body(...)):
    try:
        space = space_instance[request_data["sessionId"]]
        return  space.removeSpace(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
    
@router.post("/api/updateSpace")
async def updateSpace(request_data: dict = Body(...)):
    try:
        space = space_instance[request_data["sessionId"]]
        return  space.updateSpaceName(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
    
@router.post("/api/getSpacesInOrg")
async def getSpacesInOrg(request_data: dict = Body(...)):
    try:
        space = space_instance[request_data["sessionId"]]
        return  space.getSpacesInOrg(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
    
@router.post("/api/assignOrg")
async def assignOrg(request_data: dict = Body(...)):
    try:
        org = organization_instance[request_data["sessionId"]]
        return  org.assignUsersToOrg(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
    

@router.post("/api/unassignOrg")
async def unassignSpace(request_data: dict = Body(...)):
    try:
        org = organization_instance[request_data["sessionId"]]
        return  org.unassignUsersToOrg(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))

@router.post("/api/assignSpace")
async def assignSpace(request_data: dict = Body(...)):
    try:
        space = space_instance[request_data["sessionId"]]
        return  space.assignSpace(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
    

@router.post("/api/unassignSpace")
async def unassignSpace(request_data: dict = Body(...)):
    try:
        space = space_instance[request_data["sessionId"]]
        return  space.unassignSpace(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
    
@router.post("/api/getAllUsers")
async def getAllUsers(request_data: dict = Body(...)):
    try:
        space = space_instance[request_data["sessionId"]]
        return  space.getAllUsers()
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
   

@router.post("/api/getUsersInOrg")
async def getUsersInOrg(request_data: dict = Body(...)):
    try:
        space = space_instance[request_data["sessionId"]]
        return  space.getUsersInOrg(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))

@router.post("/api/getAdminAllSpaces")
async def getAdminAllSpaces(request_data: dict = Body(...)):
    try:
        space = space_instance[request_data["sessionId"]]
        return  space.getAdminAllSpaces()
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))

@router.post("/api/getAllAnalystsInOrg")
async def getAllAnalystsInOrg(request_data: dict = Body(...)):
    try:
        space = space_instance[request_data["sessionId"]]
        return  space.getAllAnalystsInOrg(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))

@router.post("/api/getAnalystsInOrg")
async def getAnalystsInOrg(request_data: dict = Body(...)):
    try:
        space = space_instance[request_data["sessionId"]]
        return  space.getAnalystsInOrg(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
    

@router.post("/api/deleteSpaces")
async def deleteSpaces(request_data: dict = Body(...)):
    try:
        space = space_instance[request_data["sessionId"]]
        return  space.deleteSpaces(request_data["spaceIds"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
    
@router.post("/api/createClientAPIKey")
async def createClientAPIKey(request_data: dict = Body(...)):
    try:
        auth = authorization_instance[request_data["sessionId"]]
        return  auth.createClientAPIKey(request_data['data'])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
    
@router.post("/api/getClientAPIKeys")
async def getClientAPIKeys(request_data: dict = Body(...)):
    try:
        auth = authorization_instance[request_data["sessionId"]]
        return  auth.getClientAPIKeys(request_data['data'])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
    

 