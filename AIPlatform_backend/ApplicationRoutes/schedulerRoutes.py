from fastapi import APIRouter, HTTPException, Body, FastAPI
from fastapi import FastAPI, HTTPException
from ApplicationRoutes.authenticationRoutes import scheduler_instance



router = APIRouter()

app = FastAPI()




@router.post("/api/schedule_task")
async def schedule_task(request_data: dict = Body(...)):
    try:
        scheduler = scheduler_instance[request_data["sessionId"]]
        return  await scheduler.schedule_task(request_data["data"])
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
    
    

# @router.delete("/remove_task/{job_id}")
# def remove_task(job_id: str):
#     """
#     Remove a scheduled task by job ID.
    
#     :param job_id: The ID of the job to remove.
#     """
#     if job_id in jobs:
#         scheduler.remove_job(job_id)
#         del jobs[job_id]
#         return {"message": "Task removed", "job_id": job_id}
#     else:
#         raise HTTPException(status_code=404, detail="Job ID not found.")

# @router.get("/api/list_tasks")
# def list_tasks():
#     """
#     List all scheduled tasks.
#     """
#     return {"jobs": list(jobs.keys())}
