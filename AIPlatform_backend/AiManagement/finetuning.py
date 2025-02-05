
import logging
from fastapi import HTTPException,status
import pymongo
from Database.organizationDataBase import OrganizationDataBase







class finetune():
    def __init__(self, role: dict, userId: str,orgIds:list):
        self.role = role
        self.userId = userId
        self.orgIds=orgIds
    



    def view_metricresult(self,data):
        try:
            required_fields = ["process_id","orgId"]
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                logging.error(f"Missing required fields: {', '.join(missing_fields)}")
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": f"Missing required fields: {', '.join(missing_fields)}."
                }
           
            orgId = data["orgId"]
            if orgId not in self.orgIds:
                    return {
                        "status_code": status.HTTP_401_UNAUTHORIZED,
                        "detail": "Unauthorized Access "
                    }

            # Initialize the organization database
            organizationDB = OrganizationDataBase(orgId)
            
            # Check if organizationDB is initialized successfully
            if organizationDB.status_code != 200:
                return {
                    "status_code": organizationDB.status_code,
                    "detail": "Error initializing the organization database"
                }
            process_id = data["process_id"]
            if not orgId or not process_id or not isinstance(data, dict):
                logging.error("Empty or invalid data received.")
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Request data cannot be empty",
                }
            # Check for empty values in the data
            empty_fields = [key for key, value in data.items() if not value]
            
            if empty_fields:
                logging.error(f"Empty values found in fields: {', '.join(empty_fields)}")
                return {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "detail": f"The following fields have empty values: {', '.join(empty_fields)}. Please provide valid data for these fields.",
                    }

            # Call the function to fetch metrics by process_id
            response = organizationDB.get_metrics_by_process_id(process_id)

            return response  # Now returning a dictionary instead of JSONResponse

        except HTTPException as http_exc:
            return {"status_code": http_exc.status_code,
                    "message": http_exc.detail}

        except pymongo.errors.ConnectionFailure:
            return {"status_code": status.HTTP_503_SERVICE_UNAVAILABLE, 
                    "message": "Database connection failed. Please try again later."}

        except Exception as e:
            return {"status_code": status.HTTP_500_INTERNAL_SERVER_ERROR, "message": "Internal Server Error", "detail": str(e)}
    



    def view_allmetricresult(self,data):
        try:
            required_fields = ["user_id","orgId"]
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                logging.error(f"Missing required fields: {', '.join(missing_fields)}")
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": f"Missing required fields: {', '.join(missing_fields)}."
                }
            orgId = data["orgId"]
            if orgId not in self.orgIds:
                    return {
                        "status_code": status.HTTP_401_UNAUTHORIZED,
                        "detail": "Unauthorized Access "
                    }
            
            # Initialize the organization database
            organizationDB = OrganizationDataBase(orgId)
            
            # Check if organizationDB is initialized successfully
            if organizationDB.status_code != 200:
                return {
                    "status_code": organizationDB.status_code,
                    "detail": "Error initializing the organization database"
                }
            # Extract process_id from the request body
            user_id = data["user_id"]
            # Call the function to fetch metrics by user_id
            response = organizationDB.get_documents_by_user_id(user_id)
            return response

        except HTTPException as http_exc:
            # Handle specific HTTP exceptions
            return {
                "status_code":http_exc.status_code,
                "message": http_exc.detail}
            

        except Exception as e:
            # Catch-all for unforeseen errors
            return {
                "status_code":status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Internal Server Error", "detail": str(e)}
        