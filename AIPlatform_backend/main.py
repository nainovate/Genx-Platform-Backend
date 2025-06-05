import logging
import os
import setup
from fastapi import FastAPI
from ApplicationRoutes.authenticationRoutes import router as authentication_router
from ApplicationRoutes.superAdminRoutes import router as superadmin_router
from ApplicationRoutes.adminRotes import router as admin_router
from ApplicationRoutes.analystRoutes import router as analyst_router
from ApplicationRoutes.dataEngineerRoutes import router as dataEngineer_router
from ApplicationRoutes.evaluationRoutes import router as evaluation_router
from ApplicationRoutes.aiEngineerRoutes import router as aiEngineerRoutes
from ApplicationRoutes.ChatBotRoutes import router as chatBotRoutes
from ApplicationRoutes.schedulerRoutes import router as schedulerRoutes
from ApplicationRoutes.NotificationRoutes import router as NotificationRoutes
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

current_directory = os.path.dirname(__file__)
configdir = os.path.join(current_directory, "config")
logdir = os.path.join(current_directory, "logs")

# Ensure the logs directory exists
if not os.path.exists(logdir):
    os.makedirs(logdir)

log_file_path = os.path.join(logdir, "logger.log")

# Configure logging
logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust origins as needed
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Include the authentication router with prefix /v1
app.include_router(authentication_router)

app.include_router(superadmin_router)

app.include_router(admin_router)

app.include_router(analyst_router)

app.include_router(dataEngineer_router)

app.include_router(evaluation_router)

app.include_router(aiEngineerRoutes)

app.include_router(chatBotRoutes)

app.include_router(schedulerRoutes)

app.include_router(NotificationRoutes)  # Assuming setup.py has a router defined


# Entry point
if __name__ == "__main__":
    import uvicorn
    setup.setup()  # Assuming there is a setup function in setup.py
    # setup.sub_scheduler()
    setup.main_scheduler()
    uvicorn.run(app, host="0.0.0.0", port=5000)

