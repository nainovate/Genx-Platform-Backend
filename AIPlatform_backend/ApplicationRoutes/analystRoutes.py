from fastapi import APIRouter, HTTPException, Body, FastAPI
from ApplicationRoutes.authenticationRoutes import authorization_instance, space_instance, organization_instance, role_instance

router = APIRouter()

@router.post("/api/getAnalystSpaces")
async def getRoles(request_data: dict = Body(...)):
    try:
        role = role_instance[request_data["sessionId"]]
        return  role.getAnalystSpaces()
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e)) 

@router.post("/api/getRolesInSpace")
async def getSpaceIdRoles(request_data: dict = Body(...)):
    try:
        role = role_instance[request_data["sessionId"]]
        return  role.getRolesInspace(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e)) 
    
@router.post("/api/getOrgIdSpaces")
async def getOrgIdSpaces(request_data: dict = Body(...)):
    try:
        role = role_instance[request_data["sessionId"]]
        return  role.getAnalystSpaces()
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e)) 
 
@router.post("/api/createRole")
async def createRole(request_data: dict = Body(...)):
    try:
        role = role_instance[request_data["sessionId"]]
        return  role.createRole(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
    
@router.post("/api/removeRole")
async def removeRole(request_data: dict = Body(...)):
    try:
        role = role_instance[request_data["sessionId"]]
        return  role.removeRole(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
    
@router.post("/api/updateRole")
async def updateRole(request_data: dict = Body(...)):
    try:
        role = role_instance[request_data["sessionId"]]
        return  role.updateRole(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
    
@router.post("/api/getSpacesInOrg")
async def getSpacesInOrg(request_data: dict = Body(...)):
    try:
        space = space_instance[request_data["sessionId"]]
        return  space.getSpacesInOrg(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
    
