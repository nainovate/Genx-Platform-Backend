import os
import logging
import yaml
from fastapi import HTTPException, Body, status
from Database.users import *
from Database.applicationSetup import *
from Database.applicationDataBase import *
from jose import JWTError, jwt
from datetime import datetime, timedelta
from random import randint
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from werkzeug.security import generate_password_hash


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

def initilizeUserDB():
    try:
        userDB = UsersSetup()
        return userDB
    except Exception as e:
        logging.error(f"Error while getting userDB: {e}")
        return None
    
def initilizeApplicationConfigDB():
    applicationDB = ApplicationSetup()
    return applicationDB


def getApplicationConfig():
    try:
        # Initialize application database
        applicationConfigDB = initilizeApplicationConfigDB()

        if applicationConfigDB is None:
            logging.error("Failed to initialize application database.")
            return None

        # Retrieve application configuration data
        applicationConfigData, status_code = applicationConfigDB.getApplicationConfig()

        if status_code == status.HTTP_200_OK:
            return applicationConfigData
        elif status_code == status.HTTP_404_NOT_FOUND:
            logging.error("No configuration found in the application database.")
            return None
        elif status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
            logging.error(
                "Internal server error occurred while retrieving application configuration."
            )
            return None
        else:
            logging.error(
                "Unknown error occurred while retrieving application configuration."
            )
            return None
    except Exception as e:
        logging.error(f"Error while getting application configuration: {e}")
        return None

conf = ConnectionConfig(
        MAIL_USERNAME="sivatar7@gmail.com",
        MAIL_PASSWORD="fmac zeax xtez osmr",
        MAIL_FROM="sivatar7@gmail.com",
        MAIL_PORT=587,
        MAIL_SERVER="smtp.gmail.com",
        MAIL_STARTTLS=True,
        MAIL_SSL_TLS=False,  # Set to False for STARTTLS
    )

fastmail = FastMail(conf)

class Authentication:
    def __init__(self, username = None, userId = None, refreshToken= None):
        self.username = username
        self.userId = userId
        self.refreshToken = refreshToken
        self.userDB = initilizeUserDB()
        self.applicationConfigData = getApplicationConfig()

    def generateRefreshToken(self, user_data: dict) -> str:
        try:
            SECRET_KEY = self.applicationConfigData["secretKey"]
            REFRESH_TOKEN_EXPIRE_DAYS = self.applicationConfigData["refreshTokenExpireDays"]

            expiration_time = datetime.utcnow() + timedelta(
                days=REFRESH_TOKEN_EXPIRE_DAYS
            )
            expiration_timestamp = int(expiration_time.timestamp())

            refresh_token = jwt.encode(
                {"user_data": user_data, "exp": expiration_timestamp},
                SECRET_KEY,
                algorithm="HS256",
            )
            return refresh_token  # Return token as a string
        except Exception as e:
            # Log and handle unexpected errors
            logging.error(f"Error while generating refresh token: {e}")
            HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail= f"{e}"
            )

    def generateAccessToken(self, user_data: dict) -> str:
        try:
            SECRET_KEY = self.applicationConfigData["secretKey"]
            ACCESS_TOKEN_EXPIRE_MINUTES = self.applicationConfigData["accessTokenExpireMinutes"]

            expiration_time = datetime.utcnow() + timedelta(
                minutes=ACCESS_TOKEN_EXPIRE_MINUTES
            )
            expiration_timestamp = int(expiration_time.timestamp())

            access_token = jwt.encode(
                {"user_data": user_data, "exp": expiration_timestamp},
                SECRET_KEY,
                algorithm="HS256",
            )
            return access_token, 200  # Return token as a string
        except Exception as e:
            # Log and handle unexpected errors
            logging.error(f"Error while generating access token: {e}")
            return None, HTTPException(status_code=500, detail=str(e))

    def verify_refresh_token(self, refresh_token: str) -> dict:
        try:
            SECRET_KEY = self.applicationConfigData["secretKey"]
            refresh_data = jwt.decode(refresh_token, SECRET_KEY, algorithms=["HS256"])
            if refresh_data:
                return refresh_data, status.HTTP_200_OK
            else:
                return None, status.HTTP_500_INTERNAL_SERVER_ERROR
        except JWTError:
            return {
                "Invalid refresh token",
                status.HTTP_401_UNAUTHORIZED
            }
        
    def login(self, requestData: dict):
        try:
            additional_fields = set(requestData.keys()) - {
                "username",
                "password",
                "deviceHash",
                "sessionId"
            }
            if additional_fields:
                return {
                    "status_code": 400,
                    "detail":"Additional fields in the request are not allowed",
                }
            username = self.username
            deviceHash = requestData["deviceHash"]
            password = requestData["password"]

            if not password:
                status_code, userId = self.userDB.checkDeviceLogin(
                    activeStatus="active", deviceHash=deviceHash
                )

                if status_code == 404:
                    return {
                            "status_code": status.HTTP_404_NOT_FOUND,
                            "detail": "User not logged in"
                        }

                elif status_code == 302:
                    status_code, UserCredentials = self.userDB.getUserCredentials(
                        userId= userId
                    )

                    userId = UserCredentials["userId"]
                    roles = UserCredentials["role"]
                    userName = UserCredentials["username"]


                    userData = {"userId": userId, "role": roles, "deviceHash": deviceHash}

                    status_code, refreshToken = self.userDB.getRefreshToken(userId= userId, deviceHash= deviceHash)

                    if status_code == 404:
                        return {
                            "status_code": status_code,
                            "detail": "Refresh Token Not Found"
                        }
                    
                    if not status_code == 200:
                        return {
                            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                            "detail": "Internal Server Error"
                        }
                    
                    self.refreshToken = refreshToken

                    data = {
                        "deviceHash": deviceHash
                    }

                    self.username = userName

                    data = self.new_access_token(data)

                    if not data["status"] == 200:
                        return{
                            "status_code": data["status"],
                            "message": data["detail"]
                        }
                    
                    self.refreshToken = refreshToken
                    self.userId = userId
                    self.userDB = initilizeUserDB()

                    return {
                        "status_code": status_code,
                        "message": "Authentication successful",
                        "userName": username,
                        "userId": userId,
                        "accessToken": data["access_token"],
                        "refreshToken": self.refreshToken,
                        "deviceHash": deviceHash,
                        "role": roles,
                    }
                else:
                    return {
                            "status_code":status.HTTP_500_INTERNAL_SERVER_ERROR,
                            "detail":"Internal server error",
                        }
            else:
                status_code, UserCredentials = self.userDB.checkUserCredentials(
                    username=username, password=password
                )

                if status_code == status.HTTP_401_UNAUTHORIZED:
                    # Incorrect password
                    return {
                        "status_code":status.HTTP_401_UNAUTHORIZED,
                        "detail":"Invalid Credentials",
                    }
                elif status_code == status.HTTP_404_NOT_FOUND:
                    # User not found
                    return {
                        "status_code":status.HTTP_404_NOT_FOUND, "detail":"Invalid Credentials"
                    }
                if not status_code == 200:
                    # Internal server error
                    return {
                        "status_code":status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "detail":"Internal server error",
                    }
                
                userId = UserCredentials["userId"]
                roles = UserCredentials["role"]
                org = UserCredentials.get("org")
                position = UserCredentials.get("position")
                email = UserCredentials["email"]

                userData = {"userId": userId, "role": roles, "deviceHash": deviceHash}

                # Generate access and refresh tokens
                accessToken, status_code = self.generateAccessToken(userData)
                refreshToken = self.generateRefreshToken(userData)

                status_code = self.userDB.addUserAttributes(
                    userId=userId, activeStatus="active", deviceHash= deviceHash
                )

                if status_code == 304:
                    return {
                        "status_code":status.HTTP_304_NOT_MODIFIED,
                        "detail":"Account Already Logged In Another Device",
                    }
                if not status_code == 200:
                    # Internal server error
                    return {
                        "status_code":status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "detail":"Internal server error",
                    }
                
                status_code = self.userDB.addRefreshToken(
                    userId = userId, deviceHash= deviceHash, refreshToken= refreshToken
                )

                self.refreshToken =  refreshToken
                
                # Authentication successful
                return {
                    "status_code": status_code,
                    "message": "Authentication successful",
                    "userName": username,
                    "email": email,
                    "userId": userId,
                    "refreshToken": self.refreshToken,
                    "accessToken": accessToken,
                    "deviceHash": deviceHash,
                    "role": roles,
                    "org": org,
                    "position": position
                }
        except Exception as e:
            logging.error(f"Error Log In: {e}")
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR, "detail": str(e)
            }

    def new_access_token(self, requestData: dict = Body(...)):
        try:
            additional_fields = set(requestData.keys()) - {
                "deviceHash"
            }
            if additional_fields:
                return {
                    "status" : status.HTTP_422_UNPROCESSABLE_ENTITY,
                    "detail": "Additional fields in the request are not allowed"
                }
            
            refresh_token = self.refreshToken
            deviceHash = requestData["deviceHash"]

            # You need to implement verify_refresh_token function
            refresh_data, status_code = self.verify_refresh_token(refresh_token)
            if status_code == 401:
                return {
                    "status": status.HTTP_401_UNAUTHORIZED,
                    "detail": "Invalid Refresh Token"
                }
            
            if not status_code == 200:
                return {
                    "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal Server Error"
                }

            username = self.username
            roles = refresh_data["user_data"]["role"]
            refreshTokenDeviceHash = refresh_data["user_data"]["deviceHash"]

            status_code, userId = self.userDB.getUserId(username=username, role=roles)

            if status_code == 404:
                return {
                    "status": status.HTTP_404_NOT_FOUND,
                    "detail": "User Not Found"
                }
            
            if not status_code == 200:
                return {
                    "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal Server Error"
                }

            if deviceHash == refreshTokenDeviceHash:
                userData = {"userId": userId, "role": roles, "deviceHash": deviceHash}
                accessToken, status_code = self.generateAccessToken(userData)
                if status_code == 200:
                    # Return the new access token
                    return {
                        "status": status_code,
                        "access_token": accessToken,
                        "token_type": "bearer",
                    }
                else:
                    return {
                        "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "detail": "Internal Server Error"
                    }
            else:
                return {
                    "status": status.HTTP_403_FORBIDDEN,
                    "detail":"Logged In another device"
                }
        except Exception as e:
            return {
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail":str(e)
            }

    def logout(self, deviceHash: str):
        try:
            # Update the user_active column to 'inactive'
            userId = self.userId
            if not userId:
                return HTTPException(status_code=400, detail="UserID is required")
            
            status_code = self.userDB.deleteUserAttributes(
                userId=userId, deviceHash= deviceHash
            )

            if status_code == 304:
                return HTTPException(
                    status_code=status.HTTP_304_NOT_MODIFIED,
                    detail="Account Already Logged Out",
                )
            if not status_code == 200:
                # Internal server error
                return HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Internal server error",
                )
            
            status_code = self.userDB.deleteRefreshTokens(
                userId=userId, deviceHash= deviceHash
            )

            if status_code == 304:
                return HTTPException(
                    status_code=status.HTTP_304_NOT_MODIFIED,
                    detail="Account Already Logged Out",
                )
            if not status_code == 200:
                # Internal server error
                return HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Internal server error",
                )
            
            return {"status_code": status_code,
                    "message": "User logged out successfully"
                }

        except Exception as e:
            return {
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail":str(e)
            }
        
    def generateOtp(self):
        return str(randint(100000, 999999))
    
    async def sendOtp(self,email, otp):
        message = MessageSchema(
            subject="Password Reset OTP",
            recipients=[email],
            body=f"Your OTP for password reset is: {otp}",
            subtype="html",  # Specify the subtype as "html" or "plain" as needed
        )

        try:
            await fastmail.send_message(message)
            logger.info(f"Email sent successfully to {email}")
            return True  # Email sent successfully
        except Exception as e:
            print(str(e))
            logger.error(f"Error sending email to {email}: {e}")
            return False
    
    async def resetPassword(self, emailId: str):
        try:
            status_code, userId = self.userDB.getUserInfo(emailId= emailId)

            if status_code == 404:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "Email not registered"
                }

            if not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal Server Error"
                }
            
            status_code, authenticationDetails = self.userDB.getAuthenticationDetails(userId= userId)

            if status_code == 404:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "Authentication Details Not Found"
                }

            if not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal Server Error"
                }
            
            if authenticationDetails["otpSendLock"]:
                current_time = datetime.now()

                otpSendLockedUntil = authenticationDetails["otpSendLockedUntil"]

                if current_time < otpSendLockedUntil:
                    return {
                        "status_code": status.HTTP_423_LOCKED,
                        "detail": f"Password reset locked until {otpSendLockedUntil}"
                    }
                else:
                    data = {
                        "otpSendLock": False,
                        "otpSendCount": 0,
                        "otpSendLockedUntil": None
                    }
                    status_code = self.userDB.updateAuthenticationDetails(userId= userId, data= data)

                    if status_code == 304:
                        return {
                            "status_code": status.HTTP_304_NOT_MODIFIED,
                            "detail": "Error in updating Authentication Details"
                        }

                    if not status_code == 200:
                        return {
                            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                            "detail": "Internal Server Error"
                        }
            
            status_code, authenticationDetails = self.userDB.getAuthenticationDetails(userId= userId)

            if status_code == 404:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "Authentication Details Not Found"
                }

            if not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal Server Error"
                }
            
            otpSendCount = authenticationDetails["otpSendCount"]

            if otpSendCount < self.applicationConfigData["maxOtpSendAttempts"] and not authenticationDetails["otpSendLock"]:
                # Generate an OTP
                otp = self.generateOtp()

                # Store the current timestamp when the OTP is generated
                otpGenerationTime = datetime.now()

                # Use your email sending logic here (replace the next line with your logic)
                result = await self.sendOtp(emailId, otp)  # Await the coroutine

                if result:
                    data = {
                        "oneTimePassword": otp,
                        "otpSendLastTimestamp": otpGenerationTime,
                        "otpSendCount": otpSendCount + 1
                    }

                    status_code = self.userDB.updateAuthenticationDetails(userId= userId, data= data)

                    if status_code == 304:
                        return {
                            "status_code": status.HTTP_304_NOT_MODIFIED,
                            "detail": "Error in updating Authentication Details"
                        }

                    if not status_code == 200:
                        return {
                            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                            "detail": "Internal Server Error"
                        }
                    
                    return {
                        "status_code": status.HTTP_200_OK, 
                        "detail": "OTP sent to your email"
                    }
                
                else:
                   return {
                            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                            "detail": "Failed To Send OTP"
                        }
            else:
                otpLockDurationMinutes = self.applicationConfigData["otpLockDurationMinutes"]
                otpSendLockedUntil = datetime.now() + timedelta(minutes= otpLockDurationMinutes)

                data = {
                    "otpSendLock" : True,
                    "otpSendLockedUntil" : otpSendLockedUntil
                }
                
                status_code = self.userDB.updateAuthenticationDetails(userId= userId, data= data)

                if status_code == 304:
                    return {
                        "status_code": status.HTTP_304_NOT_MODIFIED,
                        "detail": "Error in updating Authentication Details"
                    }

                if not status_code == 200:
                    return {
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "detail": "Internal Server Error"
                    }

                return {
                        "status_code": status.HTTP_423_LOCKED,
                        "detail": f"Password reset locked until {otpSendLockedUntil}"
                    }
        except Exception as e:
            print(str(e))
            return {
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail":str(e)
            }
        
    def isOTPExpired(self,otpGenerationTime):
        currentTime = datetime.now()
        timeElapsed = currentTime - otpGenerationTime
        validityPeriod = timedelta(minutes=3)  # Adjust the validity period as needed

        return timeElapsed > validityPeriod 
    
    def verifyOtp(self, requestData: dict):
        try:
            status_code, userId = self.userDB.getUserInfo(emailId= requestData["emailId"])

            if status_code == 404:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "Email not registered"
                }

            if not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal Server Error"
                }
            
            status_code, authenticationDetails = self.userDB.getAuthenticationDetails(userId= userId)

            if status_code == 404:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "Authentication Details Not Found"
                }

            if not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal Server Error"
                }
            
            if authenticationDetails["otpAttemptLocked"]:
                current_time = datetime.now()

                otpCoolDown = authenticationDetails["otpCoolDown"]

                if current_time < otpCoolDown:
                    return {
                        "status_code": status.HTTP_423_LOCKED,
                        "detail": f"Password reset locked until {otpCoolDown}"
                    }
                else:
                    data = {
                        "otpAttemptLocked": False,
                        "otpAttemptsCount": 0,
                        "otpCoolDown": None
                    }
                    status_code = self.userDB.updateAuthenticationDetails(userId= userId, data= data)

                    if status_code == 304:
                        return {
                            "status_code": status.HTTP_304_NOT_MODIFIED,
                            "detail": "Error in updating Authentication Details"
                        }

                    if not status_code == 200:
                        return {
                            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                            "detail": "Internal Server Error"
                        }
                    
            status_code, authenticationDetails = self.userDB.getAuthenticationDetails(userId= userId)

            if status_code == 404:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "Authentication Details Not Found"
                }

            if not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal Server Error"
                }
            
            otpAttemptsCount = authenticationDetails["otpAttemptsCount"]

            if otpAttemptsCount >= self.applicationConfigData["maxOtpAttempts"]:
                otpAttemptsDurationMinutes = self.applicationConfigData["otpAttemptsDurationMinutes"]
                otpCoolDown = datetime.now() + timedelta(minutes= otpAttemptsDurationMinutes)

                data = {
                    "otpAttemptLocked": True,
                    "otpCoolDown": otpCoolDown
                }

                status_code = self.userDB.updateAuthenticationDetails(userId= userId, data= data)

                if status_code == 304:
                    return {
                        "status_code": status.HTTP_304_NOT_MODIFIED,
                        "detail": "Error in updating Authentication Details"
                    }

                if not status_code == 200:
                    return {
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "detail": "Internal Server Error"
                    }

                return {
                        "status_code": status.HTTP_423_LOCKED,
                        "detail": f"Password reset locked until {otpCoolDown}"
                    }

            else:
                data = {
                    "otpAttemptsCount": otpAttemptsCount + 1
                }

                status_code = self.userDB.updateAuthenticationDetails(userId= userId, data= data)

                if status_code == 304:
                    return {
                        "status_code": status.HTTP_304_NOT_MODIFIED,
                        "detail": "Error in updating Authentication Details"
                    }

                if not status_code == 200:
                    return {
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "detail": "Internal Server Error"
                    }
            
            if not authenticationDetails["oneTimePassword"] == requestData["otp"]:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "Invalid OTP"
                }

            if self.isOTPExpired(authenticationDetails["otpSendLastTimestamp"]):
                data = {
                    "oneTimePassword": None,
                    "otpSendLastTimestamp": None
                }

                status_code = self.userDB.updateAuthenticationDetails(userId= userId, data= data)

                if status_code == 304:
                    return {
                        "status_code": status.HTTP_304_NOT_MODIFIED,
                        "detail": "Error in updating Authentication Details"
                    }

                if not status_code == 200:
                    return {
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "detail": "Internal Server Error"
                    }
                    
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": "OTP has Expired"
                }
                
            data = {
                "oneTimePassword": None,
                "otpSendCount": 0,
                "otpAttemptsCount": 0,
                "otpSendLastTimestamp": None,
                "otpCoolDown": None,
                "otpAttemptLocked": False
            }

            status_code = self.userDB.updateAuthenticationDetails(userId= userId, data= data)

            if status_code == 304:
                return {
                    "status_code": status.HTTP_304_NOT_MODIFIED,
                    "detail": "Error in updating Authentication Details"
                }

            if not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal Server Error"
                }
                
            return {
                "status_code": status.HTTP_200_OK,
                "detail": "OTP Verified"
            }

        except Exception as e:
            print(str(e))
            return {
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail":str(e)
            }
    
    def updatePassword(self, requestData: dict):
        try:
            status_code, userId = self.userDB.getUserInfo(emailId= requestData["emailId"])

            if status_code == 404:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": "No user found"
                }

            if not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal Server Error"
                }
            
            newPassword = requestData["newPassword"]
            password = generate_password_hash(newPassword, method="sha256")

            status_code= self.userDB.updatePassword(userId= userId, password= password)
            if status_code == 304:
                return {
                    "status_code": status.HTTP_304_NOT_MODIFIED,
                    "detail": "Failed To Reset Password"
                }

            if not status_code == 200:
                return {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "detail": "Internal Server Error"
                }
                 
            return {
                "status_code": status.HTTP_200_OK,
                "detail": "Password Reset Successfull"
            }

        except Exception as e:
            print(str(e))
            return {
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail":str(e)
            }
    
        
    