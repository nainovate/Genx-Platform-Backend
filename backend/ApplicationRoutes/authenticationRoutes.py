from fastapi import APIRouter, HTTPException, Body, FastAPI
from UserManagment.authorization import *
from UserManagment.authentication import *
from ApplicationManagment.usecases import *
from ApplicationManagment.spaces import *
from ApplicationManagment.hierarchy import *


router = APIRouter()

authentication_instances = {}
authorization_instance = {}
usecase_instance = {}
space_instance = {}
hierarchy_instance = {}

authentication_instances["resetPassword"] = Authentication()

    
@router.post("/api/login")
async def login(request_data: dict = Body(...)):
    try:
        auth = Authentication(username = request_data["username"])
        data =  auth.login(requestData = request_data)
        if data["status_code"] == 200:
            sessionId = request_data["sessionId"]
            if sessionId not in authentication_instances:
                userName = data["userName"]
                userId = data["userId"]
                role = data["role"]
                refreshToken = data["refreshToken"]
                authentication_instances[sessionId] = Authentication(username= userName, userId= userId, refreshToken= refreshToken)
                authorization_instance[sessionId] = Authorization(username= userName, userId= userId, role= role)
                if "superadmin" in role:
                    usecase_instance[sessionId] = UseCases(userId = userId, role= role)
                    space_instance[sessionId] = Spaces(userId= userId, role= role)
                if "admin" in role:
                    space_instance[sessionId] = Spaces(userId= userId, role= role)
                    hierarchy_instance[sessionId] = Hierarchy(userId= userId, role= role)
                    usecase_instance[sessionId] = UseCases(userId = userId, role= role)
                if "user" in role:
                    hierarchy_instance[sessionId] = Hierarchy(userId= userId, role= role)
        return data
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))

@router.post("/api/newAccessToken")
def new_access_token(request_data: dict = Body(...)):
    try:
        auth = authentication_instances[request_data["sessionId"]]  # Create an instance of Authentication
        return auth.new_access_token(requestData = request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))

@router.post("/api/logout")
async def logout(request_data: dict = Body(...)):
    try:
        auth = authentication_instances[request_data["sessionId"]] 
        return auth.logout(deviceHash = request_data["deviceHash"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
    
@router.post("/api/register")
def register(request_data: dict = Body(...)):
    try:
        auth = authorization_instance[request_data["sessionId"]]
        return auth.createUser(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
    
@router.post("/api/resetPassword")
async def resetPassword(request_data: dict = Body(...)):
    try:
        auth = authentication_instances["resetPassword"]
        return await auth.resetPassword(emailId = request_data["emailId"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))

@router.post("/api/verifyOtp")
def verifyOtp(request_data: dict = Body(...)):
    try:
        auth = authentication_instances["resetPassword"]
        return auth.verifyOtp(requestData = request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))

@router.post("/api/updatePassword")
def updatePassword(request_data: dict = Body(...)):
    try:
        auth = authentication_instances["resetPassword"]
        return auth.updatePassword(requestData = request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))