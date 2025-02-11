
import asyncio
import json
import logging
import os
from fastapi import HTTPException,status
from fastapi.responses import StreamingResponse
import pymongo
from Database.organizationDataBase import OrganizationDataBase
from datetime import datetime


projectDirectory = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
logDir = os.path.join(projectDirectory, "logs")
logBackendDir = os.path.join(logDir, "backend")
logFilePath = os.path.join(logBackendDir, "logger.log")



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
        
    

    def get_status(self,data):

        def event_generator():
            try:
                # Convert data to dictionary and check for missing/empty fields
                required = data
                missing_fields = [field for field, value in required.items() if value is None]
                empty_fields = [field for field, value in required.items() if value == ""]

                if missing_fields:
                    logging.error(f"Missing required fields: {', '.join(missing_fields)}")
                    yield f"data: {json.dumps({'status_code': status.HTTP_400_BAD_REQUEST, 'detail': f'Missing fields: {', '.join(missing_fields)}'})}\n\n"
                    return  # Stop execution

                if empty_fields:
                    logging.error(f"Empty fields: {', '.join(empty_fields)}")
                    yield f"data: {json.dumps({'status_code': status.HTTP_400_BAD_REQUEST, 'detail': f'Empty fields: {', '.join(empty_fields)}'})}\n\n"
                    return  # Stop execution
                orgId = data["orgId"]
                # Initialize the organization database
                organizationDB = OrganizationDataBase(orgId)
                
                # Check if organizationDB is initialized successfully
                if organizationDB.status_code != 200:
                    yield {
                        "status_code": organizationDB.status_code,
                        "detail": "Error initializing the organization database"
                    }
                
                process_id = data["process_id"]
                if not process_id:
                    logging.error("Process ID is required.")
                    yield f"data: {json.dumps({'status_code': status.HTTP_400_BAD_REQUEST, 'detail': 'Process ID is required.'})}\n\n"
                    return  # Stop execution

                while True:
                    try:
                        # Fetch the status from the database
                        document = organizationDB.fetch_process_status(process_id)
                        # If fetch_process_status returns an error, send it and stop execution
                        if isinstance(document, dict) and "status_code" in document:
                            yield f"data: {json.dumps(document)}\n\n"
                            return  # Stop execution

                        # Extract status and last_updated fields
                        status_value = document.get("status", "Unknown").strip()
                        last_updated_raw = document.get("last_updated", "Unknown")
                        last_updated = (
                            last_updated_raw.isoformat() if isinstance(last_updated_raw, datetime) else last_updated_raw
                        )

                        # Send SSE response
                        response_data = {
                            "process_id": process_id,
                            "status": status_value,
                            "last_updated": last_updated,
                        }
                        yield f"data: {json.dumps(response_data)}\n\n"

                        # If process is "Completed" or "Failed", stop the loop
                        if status_value.lower() in ["completed", "failed","canceled"]:
                            break

                        asyncio.sleep(2)  # Keep checking every 2 seconds

                    except Exception as db_error:
                        logging.error(f"Database error: {str(db_error)}")
                        yield f"data: {json.dumps({'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR, 'detail': f'Database error: {str(db_error)}'})}\n\n"
                        break  # Stop execution

            except Exception as e:
                logging.error(f"Unexpected error: {str(e)}")
                yield f"data: {json.dumps({'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR, 'detail': f'Unexpected error: {str(e)}'})}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Access-Control-Allow-Origin": "*",
            },
        )

