from fastapi import APIRouter, HTTPException, Body, FastAPI
from ApplicationRoutes.authenticationRoutes import (
    authorization_instance,
    hierarchy_instance,
    space_instance,
    usecase_instance,
)

router = APIRouter()


@router.post("/api/getAssignedSpaces")
def getAssignedSpaces(request_data: dict = Body(...)):
    try:
        spaces = space_instance[request_data["sessionId"]]
        return spaces.getAssignedSpaces()
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
    
@router.post("/api/getSpaceUseCases")
def get_use_cases(request_data: dict = Body(...)):
    try:
        spaces = space_instance[request_data["sessionId"]]
        instance = usecase_instance[request_data["sessionId"]]
        return spaces.getSpaceUseCases(instance, request_data["spaceId"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))


@router.post("/api/createHierarchy")
def create_space(request_data: dict = Body(...)):
    try:
        hierarchy = hierarchy_instance[request_data["sessionId"]]
        instance = usecase_instance[request_data["sessionId"]]
        return hierarchy.createHierarchy(instance, request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))


@router.post("/api/getUnassignedUsers")
def register(request_data: dict = Body(...)):
    try:
        auth = authorization_instance[request_data["sessionId"]]
        return auth.getUnassignedUsers(hierarchyId=request_data["hierarchyId"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))


@router.post("/api/assignHierarchy")
def register(request_data: dict = Body(...)):
    try:
        hierarchy = hierarchy_instance[request_data["sessionId"]]
        return hierarchy.assignHierarchy(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))


@router.post("/api/getassignedUsers")
def register(request_data: dict = Body(...)):
    try:
        auth = authorization_instance[request_data["sessionId"]]
        return auth.getassignedUsers(
            hierarchyId=request_data["hierarchyId"],
            useCaseRole=request_data["useCaseRole"],
        )
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))


@router.post("/api/unassignHierarchy")
def register(request_data: dict = Body(...)):
    try:
        hierarchy = hierarchy_instance[request_data["sessionId"]]
        return hierarchy.unassignHierarchy(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))


@router.post("/api/getCreatedHierarchy")
def getCreatedHierarchy(request_data: dict = Body(...)):
    try:
        hierarchy = hierarchy_instance[request_data["sessionId"]]
        return hierarchy.getCreatedHierarchy(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))


@router.post("/api/getHierarchyRoles")
def getHierarchyRoles(request_data: dict = Body(...)):
    try:
        hierarchy = hierarchy_instance[request_data["sessionId"]]
        return hierarchy.getHierarchyRoles(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))


@router.post("/api/getHierarchyDetails")
def getHierarchyDetails(request_data: dict = Body(...)):
    try:
        hierarchy = hierarchy_instance[request_data["sessionId"]]
        return hierarchy.getHierarchyDetails()
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
    
@router.post("/api/deleteHierarchy")
def deleteHierarchy(request_data: dict = Body(...)):
    try:
        hierarchy = hierarchy_instance[request_data["sessionId"]]
        return hierarchy.deleteHierarchy(request_data["hierarchyIds"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))

@router.post("/api/updateHierarchyName")
def updateHierarchyName(request_data: dict = Body(...)):
    try:
        hierarchy = hierarchy_instance[request_data["sessionId"]]
        return hierarchy.updateHierarchyName(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))

@router.post("/api/getUserDetails")
def getUserDetails(request_data: dict = Body(...)):
    try:
        auth = authorization_instance[request_data["sessionId"]]
        return auth.getUserDetails()
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))

@router.post("/api/updateUserDetails")
def updateUserDetails(request_data: dict = Body(...)):
    try:
        auth = authorization_instance[request_data["sessionId"]]
        return auth.updateUserDetails(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))

@router.post("/api/addHierarchyConfig")
def addHierarchyConfig(request_data: dict = Body(...)):
    try:
        hierarchy = hierarchy_instance[request_data["sessionId"]]
        return hierarchy.addHierarchyConfig(request_data["hierarchyId"], request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))