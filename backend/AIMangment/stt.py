import subprocess
import requests
import os
import logging
import yaml
from fastapi import status

projectDirectory = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
logDir = os.path.join(projectDirectory, "logs")
logBackendDir = os.path.join(logDir, "backend")
logFilePath = os.path.join(logBackendDir, "logger.log")

# Configure logging settings
logging.basicConfig(
    filename=logFilePath,  # Set the log file name
    level=logging.INFO,  # Set the desired log level (e.g., logging.DEBUG, logging.INFO)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

class Stt:
    def __init__(self, clientApiKey: str, deployId: str, ffmpegFlag: int):
        self.AIServicesIp = os.getenv("AIServicesIp")
        self.AIServerPort = os.getenv("AIServerPort")
        self.endpoint = "http://"+self.AIServicesIp+":"+self.AIServerPort
        self.clientApiKey = clientApiKey
        self.deployId = deployId
        self.ffmpegFlag = ffmpegFlag

    def convertToText(self, file, userDirectory, fileName):
        try:
            audio_name = "audio_" + fileName
            audio_file = os.path.join(userDirectory, f"{audio_name}.mp3")
            ffmpeg_flag = self.ffmpegFlag
            if ffmpeg_flag == 1:
                # ffmpeg_executable = "C:\\ffmpeg\\bin\\ffmpeg.exe"  # Replace with the actual path
                # ffmpeg_cmd = f"{ffmpeg_executable} -i {video_file} -map 0:a -acodec libmp3lame {audio_file}"
                # subprocess.run(ffmpeg_cmd, shell=True, check=True)
                ffmpeg_cmd = f"ffmpeg -i {file} -map 0:a -acodec libmp3lame {audio_file}"
                subprocess.run(ffmpeg_cmd, shell=True, check=True)
                configdata = {"clientApiKey": self.clientApiKey, "input_file": audio_file}
            else:
                configdata = {
                    "clientApiKey": self.clientApiKey,
                    "input_file": file,
                    "deployId": self.deployId
                }
            response = requests.post(self.endpoint + "/accelerator/server", json=configdata)
            if response.status_code == 200:
                return status.HTTP_200_OK, response.json()["response"]
            else:
                return response.status_code, None
        except Exception as e:
            print(f"Error occurred while converting video to audio: {e}")
            return status.HTTP_500_INTERNAL_SERVER_ERROR, None
