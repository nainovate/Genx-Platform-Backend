from fastapi import APIRouter, HTTPException, Body, FastAPI
from ApplicationRoutes.authenticationRoutes import hierarchy_instance

router = APIRouter()

@router.post("/api/getHierarchyAndSpaceNames")
def getHierarchyAndSpaceNames(request_data: dict = Body(...)):
    try:
        hierarchy = hierarchy_instance[request_data["sessionId"]]
        return hierarchy.getHierarchyAndSpaceNames(hierarchyIds= request_data["data"])
    except Exception as e:
        return HTTPException(status_code= 500, detail=str(e))

@router.post("/api/getUseCaseId")
def getUseCaseId(request_data: dict = Body(...)):
    try:
        hierarchy = hierarchy_instance[request_data["sessionId"]]
        return hierarchy.getUseCaseId(hierarchyId= request_data["hierarchyId"])
    except Exception as e:
        return HTTPException(status_code= 500, detail=str(e))