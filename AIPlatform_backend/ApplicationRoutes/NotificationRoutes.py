from fastapi import APIRouter, HTTPException, Body
from ApplicationRoutes.authenticationRoutes import notification_instance

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.post("/api/create")
async def create_notification(request_data: dict = Body(...)):
    try:
        session_id = request_data["sessionId"]
        if session_id not in notification_instance:
            raise ValueError(f"Session ID '{session_id}' not found in notification_instance")
        
        notification = notification_instance[session_id]
        print(f"Notification Instance: {notification}")
        return await notification.create_notification(request_data["data"])
    except Exception as e:
        print(f"[ERROR]: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/read_unread-notifications")
async def get_unread_notifications(request_data: dict = Body(...)):
    try:
        notification = notification_instance[request_data["sessionId"]]
        return await notification.get_unread_notifications(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))

@router.post("/api/get_all-notifications")
async def get_all_notifications(request_data: dict = Body(...)):
    try:
        notification = notification_instance[request_data["sessionId"]]
        return await notification.get_all_notifications(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))


@router.post("/api/delete")
async def delete_notifications(request_data: dict = Body(...)):
    try:
        notification = notification_instance[request_data["sessionId"]]
        return await notification.delete_notifications(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
    

