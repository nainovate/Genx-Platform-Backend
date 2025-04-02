import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging
import uuid
from datetime import datetime, timezone
from fastapi import HTTPException, status
from Database.organizationDataBase import *
import requests
from Database.applicationDataBase import *



projectDirectory = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
logDir = os.path.join(projectDirectory, "logs")
logBackendDir = os.path.join(logDir, "backend")
logFilePath = os.path.join(logBackendDir, "logger.log")

def initilizeApplicationDB():
    applicationDB = ApplicationDataBase()
    return applicationDB

# Configure logging settings
logging.basicConfig(
    filename=logFilePath,  # Set the log file name
    level=logging.INFO,  # Set the desired log level (e.g., logging.DEBUG, logging.INFO)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


scheduler = BackgroundScheduler()
scheduler.start()
# jobs = {}



class Scheduler:
    def __init__(self, role: dict, userId: str, orgIds: list):
        self.role = role
        self.userId = userId
        self.orgIds = orgIds
        self.organizationDB = None
        self.AIServicesIp = os.getenv("AIServicesIp")
        self.AIServerPort = os.getenv("AIServerPort")
        self.endpoint = "http://"+self.AIServicesIp+":"+self.AIServerPort
        self.applicationDB = initilizeApplicationDB()

        
    def ingestService(self,api_url: str, input_data: dict):
        """Function to call the external API."""
        try:
            # res_data = input_data["config"]
            # response = requests.post(api_url, json = res_data)
            # print(f"API Response: {response.status_code} - {response.text}")
            self.organizationDB.updateJob(data=input_data)
            print('----comming into ingest service function',input_data["jobId"])
        except Exception as e:
            print(f"Error calling API: {e}")
        
    async  def writeScheduleJob(self, input_data: dict):
        try:
            job = scheduler.add_job(self.ingestService, input_data["trigger"], [f'{self.endpoint}/aiService/ingest', input_data], replace_existing=True)
            # jobs[input_data["jobId"]] = job
            data = {
                "jobId":input_data["jobId"],
                "job":job.id,
                "name":input_data["name"],
                "config":input_data["config"],
                "interval":input_data["interval"],
                "time":input_data["time"],
                "userId":self.userId
            }
            status_code = self.organizationDB.createJob(data=data)
            if status_code == 409:
                return {
                    "status_code": status.HTTP_409_CONFLICT,
                    "detail": f"Job Name Already Exsist: {data['name']}",
                }
            elif not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error",
                }
            # jobs[input_] = job
            return {"status_code": status.HTTP_200_OK, "detail":"Job created successfully."}
        except Exception as e:
            print(f"Error calling API: {e}")
            return {"status_code": status.HTTP_500_INTERNAL_SERVER_ERROR, "detail":"Internal server error."}

        
    async def schedule_task(self,data:dict):
        # Get current timestamp
        try:
            if not isinstance(data, dict):
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. Expected a dictionary."
                }

            if not "dataengineer" in self.role and not "aiengineer" in self.role:
                return {
                        "status_code": status.HTTP_401_UNAUTHORIZED,
                        "detail": "Unauthorized Access"
                }
            if not isinstance(data, dict) or "config" not in data or "orgId" not in data or "time"  not in data or "interval" not in data or "name" not in data:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. Expected a dictionary with 'config', 'orgId', 'time', 'interval' and 'name' keys."
                }
            interval = data["interval"]
            config = data["config"]
            time = data["time"]
            orgId = data["orgId"]
            name = data["name"]
            if not orgId in self.orgIds:
                return {
                        "status_code": status.HTTP_401_UNAUTHORIZED,
                        "detail": "Unauthorized Access"
                }
            current_timestamp = int(datetime.now(tz=timezone.utc).timestamp())
            # Define interval mapping
            intervals = {
                "minute": 60,
                "hourly": 3600,
                # "hourly": 10,
                "daily": 86400,
                "weekly": 604800,
                "monthly": 2592000  # Approximate month (30 days)
            }

            if interval not in intervals:
                return {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "detail": "Invalid interval. Choose from 'minute', 'hourly', 'daily', 'weekly', 'monthly'."
                }

            # Initialize the organization database
            self.organizationDB = OrganizationDataBase(orgId)
            
            # Check if organizationDB is initialized successfully
            if not self.organizationDB:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Error initializing the organization database"
                }
            job_id = str(uuid.uuid4())
            if current_timestamp >= time:
                time = current_timestamp + intervals[interval]
            else:
                pass

            start_time = datetime.fromtimestamp(time, tz=timezone.utc)

            trigger = IntervalTrigger(seconds=intervals[interval], start_date=start_time)
            
            inputData = {
                "jobId":job_id,
                "name":name,
                "config":config,
                "interval":interval,
                "trigger": trigger,
                "time":time,
                "seconds":intervals[interval]
            }
            job = await self.writeScheduleJob(input_data=inputData)
            if job["status_code"] == 200:
                return {
                    "status_code":200,
                    "detail":job["detail"],
                }
            else:
                return {
                    "status_code":job["status_code"],
                    "detail":job["detail"],
                }
            
        except Exception as e:
            logger.error(f"Error in getTasksForRole: {str(e)}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": "Internal server error",
            }

    async def remove_task(self,data:dict):
        # Get current timestamp
        try:
            if not isinstance(data, dict):
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. Expected a dictionary."
                }

            if not "dataengineer" in self.role and not "aiengineer" in self.role:
                return {
                        "status_code": status.HTTP_401_UNAUTHORIZED,
                        "detail": "Unauthorized Access"
                }
            if not isinstance(data, dict) or "orgId" not in data or "jobId" not in data:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. Expected a dictionary with 'orgId' and 'jobId' keys."
                }
            orgId = data["orgId"]
            jobId = data["jobId"]
            if not orgId in self.orgIds:
                return {
                        "status_code": status.HTTP_401_UNAUTHORIZED,
                        "detail": "Unauthorized Access"
                }

            # Initialize the organization database
            self.organizationDB = OrganizationDataBase(orgId)
            
            # Check if organizationDB is initialized successfully
            if not self.organizationDB:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Error initializing the organization database"
                }
            status_code, job = self.organizationDB.checkJob(jobId=jobId)
            if status_code == 404:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": f"Job Not Found",
                }
            elif not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal server error",
                }
            scheduler.remove_job(job)
            self.organizationDB.deleteJob(jobId=jobId)
            return {
                "status_code":status.HTTP_200_OK,
                "detail":"Job Deleted Successfully.",
            }
        except Exception as e:
            logger.error(f"Error in deleting job: {str(e)}")
            print(f"Error in deleting job: {str(e)}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": "Internal server error",
            }
            
    async def getAllJobs(self,data:dict):
        # try:
        #     if not isinstance(data, dict):
        #         return {
        #             "status_code": status.HTTP_400_BAD_REQUEST,
        #             "detail": "Invalid input data. Expected a dictionary."
        #         }

        #     if not "dataengineer" in self.role and not "aiengineer" in self.role:
        #         return {
        #                 "status_code": status.HTTP_401_UNAUTHORIZED,
        #                 "detail": "Unauthorized Access"
        #         }
        #     if not isinstance(data, dict) or "orgId" not in data:
        #         return {
        #             "status_code": status.HTTP_400_BAD_REQUEST,
        #             "detail": "Invalid input data. Expected a dictionary with 'orgId' key."
        #         }
        #     orgId = data["orgId"]
        #     if not orgId in self.orgIds:
        #         return {
        #                 "status_code": status.HTTP_401_UNAUTHORIZED,
        #                 "detail": "Unauthorized Access"
        #         }

        #     # Initialize the organization database
        #     self.organizationDB = OrganizationDataBase(orgId)
            
        #     # Check if organizationDB is initialized successfully
        #     if not self.organizationDB:
        #         return {
        #             "status_code": status.HTTP_400_BAD_REQUEST,
        #             "detail": "Error initializing the organization database"
        #         }
        #     jobs = self.organizationDB.getAllJobs()
        #     if jobs:
        #         return {
        #             "status_code": status.HTTP_200_OK,
        #             "jobs": jobs,
        #         }
        #     else:
        #         return {
        #             "status_code": status.HTTP_404_NOT_FOUND,
        #             "detail": f"Jobs Not Found",
        #         }
        # except Exception as e:
        #     logger.error(f"Error in getting jobs: {str(e)}")
        #     print(f"Error in getting jobs: {str(e)}")
        #     return {
        #         "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        #         "detail": "Internal server error",
        #     }
        job_list = []
        for job in scheduler.get_jobs():  # Fetch all active jobs
            print('----job',job)
            job_list.append({
                "job_id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.strftime("%Y-%m-%d %H:%M:%S") if job.next_run_time else "Not scheduled",
                "trigger": str(job.trigger)
            })

        return {"jobs": job_list}
        