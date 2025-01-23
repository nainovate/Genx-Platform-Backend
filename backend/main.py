import os
from fastapi import FastAPI, HTTPException, Body
import logging
from setup import *
from ApplicationRoutes.authenticationRoutes import router as authentication_router
from ApplicationRoutes.adminRoutes import router as admin_router
from ApplicationRoutes.superAdminRoutes import router as super_admin_router
from ApplicationRoutes.userRoutes import router as user_router
try:
    from SkillPracticeBackend.skillPracticeRoutes import router as skill_practice_router
except ImportError:
    skill_practice_router = None  # Handle the case where the module is not present

try:
    from ChatBotBackend.chatBotRoutes import router as chat_bot_router
except ImportError:
    chat_bot_router = None  # Handle the case where the module is not present


current_directory = os.path.join(os.path.dirname(__file__))
project_directory = os.path.join(current_directory, "..")
configdir = os.path.join(project_directory, "config")
logdir = os.path.join(project_directory, "logs")
log_backenddir = os.path.join(logdir, "backend")

backend_api_path = os.path.abspath(os.path.join(os.path.dirname(__file__)))
config_path = os.path.join(backend_api_path, "config.yaml")

app = FastAPI()


log_file_path = os.path.join(log_backenddir, "logger.log")
logging.basicConfig(
    filename=log_file_path,  # Set the log file name
    level=logging.INFO,  # Set the desired log level (e.g., logging.DEBUG, logging.INFO)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


# Configure the logging settings
logger = logging.getLogger(__name__)

#Authentication Routes
app.include_router(authentication_router)

#Super Admin Routes
app.include_router(super_admin_router)

#Admin Routes
app.include_router(admin_router)

#User Routes
app.include_router(user_router)

# Skill Practice Routes
if skill_practice_router:
    app.include_router(skill_practice_router)

# Chat Bot Routes
if chat_bot_router:
    app.include_router(chat_bot_router)

if __name__ == "__main__":
    import uvicorn
    setup()
    uvicorn.run(app, host="0.0.0.0", port=5001)
    
