import os
import requests
# from urllib.parse import urlparse, unquote
from office365.runtime.auth.client_credential import ClientCredential
from office365.sharepoint.client_context import ClientContext
from urllib.parse import urlparse, unquote, quote, parse_qs
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

    def connectToSharepoint(self,cloud_config, timestamp):
        try:
            tenant_id = cloud_config['tenant_id']
            client_id = cloud_config['client_id']
            client_secret = cloud_config['client_secret']
            folder_url = cloud_config['folder_path']

            # === AUTHENTICATE WITH MICROSOFT GRAPH ===
            token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
            token_data = {
                'client_id': client_id,
                'scope': 'https://graph.microsoft.com/.default',
                'client_secret': client_secret,
                'grant_type': 'client_credentials'
            }

            token_r = requests.post(token_url, data=token_data)
            token_r.raise_for_status()
            access_token = token_r.json()['access_token']
            headers = {'Authorization': f'Bearer {access_token}'}

            # === PARSE URL ===
            parsed_url = urlparse(folder_url)
            hostname = parsed_url.hostname
            decoded_path = unquote(parsed_url.path)
            path_parts = [part for part in decoded_path.split('/') if part]
            site_index = path_parts.index('sites')
            site_name = path_parts[site_index + 1]
            target_folder_name = path_parts[-1]

            # === GET SITE ID ===
            site_resp = requests.get(
                f"https://graph.microsoft.com/v1.0/sites/{hostname}:/sites/{site_name}",
                headers=headers
            )
            site_resp.raise_for_status()
            site = site_resp.json()

            # === GET DRIVES (Document Libraries) ===
            drives_resp = requests.get(
                f"https://graph.microsoft.com/v1.0/sites/{site['id']}/drives",
                headers=headers
            )
            drives_resp.raise_for_status()
            drives = drives_resp.json()['value']
            drive = next((d for d in drives if d['name'] in ["Documents", "Shared Documents"]), None)
            if not drive:
                raise Exception("Documents library not found")

            # === GET ROOT CHILDREN TO FIND TARGET FOLDER ===
            root_items_resp = requests.get(
                f"https://graph.microsoft.com/v1.0/sites/{site['id']}/drives/{drive['id']}/root/children",
                headers=headers
            )
            root_items_resp.raise_for_status()
            root_items = root_items_resp.json()['value']

            target_folder = next((item for item in root_items if item['name'].lower() == target_folder_name.lower() and 'folder' in item), None)

            if not target_folder:
                raise Exception(f'Folder "{target_folder_name}" not found')

            # === GET TARGET FOLDER CONTENT ===
            folder_items_resp = requests.get(
                f"https://graph.microsoft.com/v1.0/sites/{site['id']}/drives/{drive['id']}/items/{target_folder['id']}/children",
                headers=headers
            )
            folder_items_resp.raise_for_status()
            items = folder_items_resp.json()['value']

            files = []
            folders = []

            for item in items:
                base = {
                    "webUrl": item.get('webUrl')
                }
                if 'file' in item:
                    # files.append(unquote(item.get('webUrl')))
                    created_datetime_str = item["fileSystemInfo"].get("createdDateTime")
                    created_datetime = datetime.fromisoformat(created_datetime_str.rstrip("Z")).replace(tzinfo=timezone.utc)
                    created_unix = int(created_datetime.timestamp())
                    if not timestamp:
                        files.append(folder_url+'/'+item.get('name'))
                    elif created_unix > timestamp:
                        files.append(folder_url+'/'+item.get('name'))

                elif 'folder' in item:
                    folders.append({
                        **base,
                        "type": "folder",
                        "childCount": item['folder'].get('childCount', 0)
                    })
            if len(files) == 0:
                return {"skip":"true"}
            ext_dict = {}

            for url in files:
                parsed = urlparse(url)
                # Handle URLs that use a query parameter to name the file (e.g., &file=sales.xlsx)
                if parsed.path.endswith("Doc.aspx"):
                    query = parse_qs(parsed.query)
                    filename = query.get("file", [None])[0]
                else:
                    filename = os.path.basename(parsed.path)
                
                if filename:
                    ext = os.path.splitext(filename)[1].lower()
                    ext_dict.setdefault(ext.replace('.',''), []).append(url)
            return {
                "client_id":client_id,
                "tenant_id":tenant_id,
                "client_secret":client_secret,
                "split_files": ext_dict
            }

        except Exception as e:
            print("❌ Error:", e)
            return {
                "success": False,
                "error": str(e)
            }

            
    def ingestService(self,api_url: str, input_data: dict):
        """Function to call the external API."""
        try:
            config_data = input_data["config"]
            data = {}
            data["client_api_key"] = config_data["client_api_key"]
            data["vector_db_config_id"] = config_data["vector_db_config_id"]
            data["embedding_model_id"] = config_data["embedding_model_id"]
            data["splitter_config_id"] = config_data["splitter_config_id"]
            data["framework"] = config_data["framework"]
            data["user_id"]= config_data["user_id"]
            jobId = input_data["jobId"]
            status_code, job = self.organizationDB.checkJob(jobId=jobId)
            timestamp = job["prev_job"][0] if job.get("prev_job") else None
            args= self.connectToSharepoint(cloud_config=config_data["cloud_config"],timestamp=timestamp)
            if args.get("skip"):
                pass
            else:
                for ext, urls in args['split_files'].items():
                    args_data ={
                        "client_id":args["client_id"],
                        "tenant_id":args["tenant_id"],
                        "client_secret":args["client_secret"],
                        "file_paths": urls
                    }
                    inputDataConfig = {
                        "type":config_data["source_type"],
                        "service_name":config_data["cloud_service"],
                        "args":args_data,
                        "download_file": False,
                        "file_type":ext
                    }
                    data["input_data_config"] = inputDataConfig
                    data["loader_params"] = {
                        "file_config": {}
                    }
                    response = requests.post(api_url, json = data)
                    print(f"API Response: {response.status_code} - {response.text}")
            self.organizationDB.updateJob(data=input_data)
        except Exception as e:
            print(f"Error calling API: {e}")
        
    async  def writeScheduleJob(self, input_data: dict):
        try:
            job = scheduler.add_job(self.ingestService, input_data["trigger"], [f'{self.endpoint}/aiService/ingest', input_data], replace_existing=True)
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
            config["user_id"]= self.userId
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
            # if job["status_code"] == 200:
            #     return {
            #         "status_code":200,
            #         "detail":job["detail"],
            #     }
            # else:
            #     return {
            #         "status_code":job["status_code"],
            #         "detail":job["detail"],
            #     }
            return job
            
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
            jobFound = scheduler.get_job(job_id=job["job"])
            if jobFound:
                scheduler.remove_job(job["job"])
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
            if not isinstance(data, dict) or "orgId" not in data:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid input data. Expected a dictionary with 'orgId' key."
                }
            orgId = data["orgId"]
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
            jobs = self.organizationDB.getAllJobs()
            if jobs:
                return {
                    "status_code": status.HTTP_200_OK,
                    "jobs": jobs,
                }
            else:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": f"Jobs Not Found",
                }
        except Exception as e:
            logger.error(f"Error in getting jobs: {str(e)}")
            print(f"Error in getting jobs: {str(e)}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": "Internal server error",
            }
        # job_list = []
        # for job in scheduler.get_jobs():  # Fetch all active jobs
        #     print('----job',job)
        #     job_list.append({
        #         "job_id": job.id,
        #         "name": job.name,
        #         "next_run_time": job.next_run_time.strftime("%Y-%m-%d %H:%M:%S") if job.next_run_time else "Not scheduled",
        #         "trigger": str(job.trigger)
        #     })

        # return {"jobs": job_list}
        