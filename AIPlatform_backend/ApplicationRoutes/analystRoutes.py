from fastapi import APIRouter, HTTPException, Body, FastAPI
from ApplicationRoutes.authenticationRoutes import authorization_instance, space_instance, organization_instance, role_instance,task_instance

router = APIRouter()

@router.post("/api/getAnalystSpaces")
async def getSpaces(request_data: dict = Body(...)):
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
    
@router.post("/api/getRoleTasks")
async def getRoleTasks(request_data: dict = Body(...)):
    try:
        task = task_instance[request_data["sessionId"]]
        return task.getRoleTasks(request_data["data"])
    except KeyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.post("/api/getAgents")
async def getAgents(request_data: dict = Body(...)):
    try:
        task = task_instance[request_data["sessionId"]]
        return task.getAgents(request_data["data"])
    except KeyError as e:
       raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/createTask")
async def createTask(request_data: dict = Body(...)):
    try:
        task = task_instance[request_data["sessionId"]]
        return task.createTask(request_data["data"])
    except KeyError as e:
       raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/getAnalystRoles")
async def getAnalystRoles(request_data: dict = Body(...)):
    try:
        role = role_instance[request_data["sessionId"]]
        return  role.getAnalystRoles()
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e)) 

@router.post("/api/updateTask")
async def updateTask(request_data: dict = Body(...)):
    try:
        task = task_instance[request_data["sessionId"]]
        return task.updateTask(request_data["data"])
    except KeyError as e:
       raise HTTPException(status_code=500, detail=str(e))
    


@router.post("/api/deleteTask")
async def deleteTask(request_data: dict = Body(...)):
    try:
        task = task_instance[request_data["sessionId"]]
        return task.deleteTask(request_data["data"])
    except KeyError as e:
        raise HTTPException(status_code=500, detail=str(e))
