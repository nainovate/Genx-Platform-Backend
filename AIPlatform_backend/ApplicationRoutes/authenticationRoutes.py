from fastapi import APIRouter, HTTPException, Body, FastAPI
from UserManagment.authorization import *
from UserManagment.authentication import *
from ApplicationManagment.usecases import *
from ApplicationManagment.spaces import *
from ApplicationManagment.roles import *
from ApplicationManagment.organization import *
from ApplicationManagment.evaluation import *
from AiManagement.prompts import *
from AiManagement.payloads import *
from AiManagement.models import*


router = APIRouter()

authentication_instances = {}
authorization_instance = {}
usecase_instance = {}
space_instance = {}
organization_instance = {}
role_instance = {}
prompts_instance = {}
payload_instance = {}
model_instance = {}
evaluation_instance = {}



# authentication_instances["resetPassword"] = Authentication()

    
@router.post("/api/login")
async def login(request_data: dict = Body(...)):
    try:
        auth = Authentication(username=request_data["username"])
        data = auth.login(requestData=request_data)
        if data["status_code"] == 200:
            sessionId = request_data["sessionId"]
            
            # Check if sessionId already exists
            if sessionId not in authentication_instances:
                userName = data["userName"]
                userId = data["userId"]
                role = data["role"]
                refreshToken = data["refreshToken"]
                
                # Populate the instances
                authentication_instances[sessionId] = Authentication(username=userName, userId=userId, refreshToken=refreshToken)
                authorization_instance[sessionId] = Authorization(username=userName, userId=userId, role=role)
                
                # # Populating prompts_instance with the sessionId
                prompts_instance[sessionId] = Prompts(userId=userId, role=role)
                payload_instance[sessionId] = Payload(userId=userId, role=role)  
                model_instance[sessionId] = Model(userId=userId, role=role)      
                         
                # Role-based instance creation
                if "superadmin" in role:
                    organization_instance[sessionId] = Organization(userId=userId, role=role)
                if "admin" in role:
                    orgIds = role["admin"]
                    organization_instance[sessionId] = Organization(userId=userId, role=role)
                    space_instance[sessionId] = Spaces(userId=userId, role=role, orgIds=orgIds)
                if "analyst" in role:
                    orgIds = data["orgIds"]
                    spaceIds = role["analyst"]
                    space_instance[sessionId] = Spaces(userId=userId, role=role, orgIds=orgIds)
                    role_instance[sessionId] = Role(userId=userId, orgIds=orgIds, role=role, spaceIds=spaceIds)
                if "aiengineer" in role:
                    orgIds = data["orgIds"]
                    organization_instance[sessionId] = Organization(userId=userId, role=role)
                    evaluation_instance[sessionId] = Evaluation(userId=userId, role=role, orgIds=orgIds) 

            # Convert ObjectId to string for userId in the response data
            if isinstance(data["userId"], ObjectId):
                data["userId"] = str(data["userId"])

            return data
        else:
            raise HTTPException(status_code=401, detail="Invalid login credentials")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    
@router.post("/api/register")
async def register(request_data: dict = Body(...)):
    try:
        auth = authorization_instance[request_data["sessionId"]]
        return  auth.createUser(request_data['data'])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))

@router.post("/api/getProfile")
async def getProfile(request_data: dict = Body(...)):
    try:
        auth = authorization_instance[request_data["sessionId"]]
        return  auth.getProfile()
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))  
    
@router.post("/api/updateProfile")
async def updateProfile(request_data: dict = Body(...)):
    try:
        auth = authorization_instance[request_data["sessionId"]]
        return  auth.updateProfile(request_data['data'])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
    
@router.post("/api/updateUserDetails")
async def updateUserDetails(request_data: dict = Body(...)):
    try:
        auth = authorization_instance[request_data["sessionId"]]
        return  auth.updateUserDetails(request_data['data'])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
