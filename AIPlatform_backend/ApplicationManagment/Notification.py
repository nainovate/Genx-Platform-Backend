# notification.py
from datetime import datetime
from Database.applicationDataBase import ApplicationDataBase
from fastapi import APIRouter, HTTPException, Body,status
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)

def initilizeApplicationDB():
      applicationDB = ApplicationDataBase()
      logger.info("Initialized ApplicationDataBase")
      return applicationDB

   
class NotificationManager:  
    def __init__(self, userId: str, role: dict):
        self.role = role
        self.userId = userId
        self.applicationDB = initilizeApplicationDB()

    async def create_notification(self, data: dict):
        try:
            required_keys = {"userId", "orgId", "message","context"}
            missing_keys = required_keys - data.keys()
            print(f"Missing keys: {missing_keys}")
            if missing_keys:
                logger.error(f"Missing keys: {missing_keys}")
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": f"Missing keys: {', '.join(missing_keys)}"
                }

            # Proceed to DB call
            return  self.applicationDB.create(data)

        except Exception as e:
            logger.error(f"Create Notification Error: {e}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": str(e)
            }

    async def get_unread_notifications(self,data: dict):
        try:
            if not data["userId"]:
                logger.error("userId is required.")
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "userId is required."
                }
            
            return  self.applicationDB.get_unread_counts_by_context(data)

        except Exception as e:
            logger.error(f"Get Notification Error: {e}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": str(e)
            }
        
    async def get_all_notifications(self, data: dict):
            if not data:
             return {
                "status_code": status.HTTP_400_BAD_REQUEST,
                "detail": "Request body cannot be empty"
                }
            # Validate required fields
            required_fields = ["userId", "page", "limit"]
            missing = [field for field in required_fields if field not in data]
            if missing:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": f"Missing required field(s): {', '.join(missing)}"
                }

            user_id = data["userId"]
            context = data.get("context", "All")
            page = data["page"]
            limit = data["limit"]

            if not isinstance(page, int) or not isinstance(limit, int) or page < 1 or limit < 1:
                return {
                    "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                    "detail": "Page and limit must be positive integers"
                }

            return  self.applicationDB.fetch_notifications(user_id, context, page, limit)


    async def get(self, user_id: str, context: str = "All", page: int = 1, limit: int = 10):
        try:
            skip = (page - 1) * limit

            query = {"userId": user_id}
            if context != "All":
                query["context"] = context

            total = await self.applicationDB["notifications"].count_documents(query)
            unread_count = await self.applicationDB["notifications"].count_documents({**query, "is_read": False})

            cursor = self.applicationDB["notifications"].find(query).sort("created_at", DESCENDING).skip(skip).limit(limit)
            notifications = await cursor.to_list(length=limit)

            # Convert ObjectId and timestamps
            for notif in notifications:
                notif["id"] = str(notif["_id"])
                notif.pop("_id", None)

            return {
                "status_code": 200,
                "detail": "Notifications fetched",
                "data": {
                    "context": context,
                    "notifications": notifications,
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "unread_count": unread_count
                }
            }

        except Exception as e:
            return {
                "status_code": 500,
                "detail": f"Database error: {str(e)}"
            }
    

   

    async def delete_notifications(self, data: dict):
            if "notification_id" not in data:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Missing required field: notification_id"
                }

            ids = data["notification_id"]

            # Normalize to list
            if isinstance(ids, str):
                ids = [ids]
            elif not isinstance(ids, list):
                return {
                    "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                    "detail": "notification_id must be a string or list of strings"
                }
            try:
                object_ids = [ObjectId(_id) for _id in ids]
            except Exception:
                return {
                    "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                    "detail": "Invalid notification_id format in list"
                }
            return self.applicationDB.delete_notifications(object_ids)


        
   
        
# Initialize the FastAPI router
