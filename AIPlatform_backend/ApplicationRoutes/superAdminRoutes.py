from fastapi import APIRouter, HTTPException, Body, FastAPI
from ApplicationRoutes.authenticationRoutes import authorization_instance, space_instance, organization_instance

router = APIRouter()

@router.post("/api/createOrganization")
async def createOrg(request_data: dict = Body(...)):
    try:
        org = organization_instance[request_data["sessionId"]]
        return  org.createOrganization(data = request_data['data'])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
    
@router.post("/api/getOrganizations")
async def getOrganizations(request_data: dict = Body(...)):
    try:
        org = organization_instance[request_data["sessionId"]]
        return  org.getOrganizations()
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
    
@router.post("/api/updateOrganization")
async def updateOrganization(request_data: dict = Body(...)):
    try:
        org = organization_instance[request_data["sessionId"]]
        return  org.updateOrganization(request_data['data'])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
    
@router.post("/api/removeOrganization")
async def removeOrganization(request_data: dict = Body(...)):
    try:
        org = organization_instance[request_data["sessionId"]]
        return  org.removeOrganization(request_data['data'])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))

@router.post("/api/getAdminsDetails")
async def getAdminsDetails(request_data: dict = Body(...)):
    try:
        auth = authorization_instance[request_data["sessionId"]]
        return  auth.getAdminsDetails()
    except Exception as e:
        return HTTPException(status_code=500, detail="Unauthorized access")
    
@router.post("/api/removeAdmin")
async def removeAdmin(request_data: dict = Body(...)):
    try:
        auth = authorization_instance[request_data["sessionId"]]
        return  auth.removeAdmin()
    except Exception as e:
        return HTTPException(status_code=500, detail="Unauthorized access")
    
@router.post("/api/getassignedAdmins")
async def getassignedAdmins(request_data: dict = Body(...)):
    try:
        auth = authorization_instance[request_data["sessionId"]]
        return  auth.getassignedAdmins(spaceId = request_data["spaceId"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
    
@router.post("/api/assignUsersToOrg")
async def assignAdmin(request_data: dict = Body(...)):
    try:
        org = organization_instance[request_data["sessionId"]]
        return  org.assignUsersToOrg(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
    
@router.post("/api/unassignUsersToOrg")
async def unassignAdmin(request_data: dict = Body(...)):
    try:
        org = organization_instance[request_data["sessionId"]]
        return  org.unassignUsersToOrg(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))