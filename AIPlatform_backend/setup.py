import os
import logging
import yaml
from Database.applicationDataBase import *
from UserManagment.authorization import *
from werkzeug.security import generate_password_hash
import json
from pymongo import MongoClient

projectDirectory = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
logDir = os.path.join(projectDirectory, "logs")
logBackendDir = os.path.join(logDir, "backend")
logFilePath = os.path.join(logBackendDir, "logger.log")

# Configure logging settings
logging.basicConfig(
    filename=logFilePath,  # Set the log file name
    level=logging.INFO,  # Set the desired log level (e.g., logging.DEBUG, logging.INFO)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

logger = logging.getLogger(__name__)

client = None

def load_config():
    backendApiPath = os.path.abspath(os.path.join(os.path.dirname(__file__)))
    configPath = os.path.join(backendApiPath, "config.yaml")
    try:
        with open(configPath, "r") as configFile:
            logging.info(f"Loading configuration from {configPath}")
            return yaml.safe_load(configFile), 200
    except FileNotFoundError:
        logging.error(f"Config file not found at: {configPath}")
        return None, 404
    except yaml.YAMLError as e:
        logging.error(f"Error parsing YAML file: {e}")
        return None, 500
    except Exception as e:
        logging.error(f"Error loading config: {e}")
        return None, 500

'''def initialize_application():
    try:
        appSetup = ApplicationSetup()
        success, status_code = appSetup, appSetup.status_code

        if success:
            logging.info("Application setup successful.")
        else:
            logging.error("Application setup failed. Check status code for details.")

        # Handle status code if needed
        if status_code == 400:
            logging.error("Bad request: Invalid input.")
        elif status_code == 500:
            logging.error("Internal server error: Unexpected error occurred during setup.")

        config_initialized, status_code = appSetup.initializeConfigData()
        if status_code == 201:
            logging.info("Configuration data initialized successfully.")
        elif status_code == 409:
            logging.warning("Config data already exists in the collection.")
        elif status_code == 500:
            logging.error("Error initializing config data. Check logs for details.")
        
        use_case_initialized, status_code = appSetup.initializeUseCaseConfig()
        if status_code == 201:
            logging.info("Use case config data initialized successfully.")
        elif status_code == 409:
            logging.warning("Use case config data already exists in the collection.")
        elif status_code == 500:
            logging.error("Error initializing use case config data. Check logs for details.")

        if not config_initialized:
            logging.error("Error initializing configuration data.")
            return False, False, 500
        if not use_case_initialized:
            logging.error("Error initializing use case configuration data.")
            return False, False, 500
        return config_initialized, use_case_initialized, 200
    except TypeError as te:
        logging.error(str(te))
        return False, False, 400
    except Exception as e:
        logging.error(f"Error initializing application: {e}")
        return False, False, 500'''
    
def load_register_config():
    try:
        projectDirectory = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        configdirectory = os.path.join(projectDirectory, "config")
        yamlFilePath = os.path.join(configdirectory, "registerConfig.yaml")

        with open(yamlFilePath, 'r') as yaml_file:
            return yaml.safe_load(yaml_file), 200
    except FileNotFoundError:
        logging.error(f"Register config file not found at: {yamlFilePath}")
        return None, 404
    except yaml.YAMLError as e:
        logging.error(f"Error parsing YAML file: {e}")
        return None, 500
    except Exception as e:
        logging.error(f"Error loading register config: {e}")
        return None, 500

def setup_users_collections():
    try:
        userSetup = ApplicationDataBase()

        if userSetup.status_code == 200:
            logging.info("User setup completed successfully.")
            collections_created = userSetup.createUserCollections()
            if collections_created:
                logging.info("User database setup completed successfully.")
                return True, 200
            else:
                logging.error("Failed to create user collections.")
                return False, 500
        elif userSetup.status_code == 400:
            logging.error("Bad request: Invalid input.")
        elif userSetup.status_code == 500:
            logging.error("Internal server error: Unexpected error occurred during setup.")
    except Exception as e:
        logging.error(f"Error setting up users database: {e}")
        return False, 500


def check_existing_user(user_setup, username: str, email: str):
    try:
        if not isinstance(user_setup, ApplicationDataBase):
            raise TypeError("user_setup should be an instance of ApplicationDataBase.")
        if not isinstance(username, str) or not isinstance(email, str):
            raise TypeError("Username and email should be strings.")
        
        return user_setup.checkExistingUser(username, email)
    except TypeError as te:
        logging.error(str(te))
        return None
    except Exception as e:
        logging.error(f"Error checking existing user: {e}")
        return None

def create_user(user_setup, user_data: dict):
    try:
        if not isinstance(user_setup, ApplicationDataBase):
            raise TypeError("user_setup must be an instance of ApplicationDataBase.")
        if not isinstance(user_data, dict):
            raise TypeError("user_data must be a dictionary.")
        
        user_setup.insertData("users", user_data)
    except TypeError as te:
        logging.error(str(te))
    except Exception as e:
        logging.error(f"Failed to insert user data into database: {e}")

def create_user_authentication(user_setup, auth_data: dict):
    try:
        if not isinstance(user_setup, ApplicationDataBase):
            raise TypeError("user_setup must be an instance of ApplicationDataBase.")
        if not isinstance(auth_data, dict):
            raise TypeError("auth_data must be a dictionary.")
        
        user_setup.insertData("userAuthentication", auth_data)
    except TypeError as te:
        logging.error(str(te))
    except Exception as e:
        logging.error(f"Failed to insert user authentication data into database: {e}")

def create_user_attributes(user_setup, attr_data: dict):
    try:
        if not isinstance(user_setup, ApplicationDataBase):
            raise TypeError("user_setup must be an instance of ApplicationDataBase.")
        if not isinstance(attr_data, dict):
            raise TypeError("attr_data must be a dictionary.")
        
        user_setup.insertData("userAttributes", attr_data)
    except TypeError as te:
        logging.error(str(te))
    except Exception as e:
        logging.error(f"Failed to insert user attributes data into database: {e}")

def create_refresh_token(user_setup, token_data: dict):
    try:
        if not isinstance(user_setup, ApplicationDataBase):
            raise TypeError("user_setup must be an instance of ApplicationDataBase.")
        if not isinstance(token_data, dict):
            raise TypeError("token_data must be a dictionary.")
        
        user_setup.insertData("refreshTokens", token_data)
    except TypeError as te:
        logging.error(str(te))
    except Exception as e:
        logging.error(f"Failed to insert refresh token data into database: {e}")

def document_exists(collection, document):
    return collection.count_documents(document, limit=1) > 0

def import_json_data(folderPath):
    global client
    databaseName = os.path.basename(folderPath)
    db = client[databaseName]
    for filename in os.listdir(folderPath):
        if filename.endswith('.json'):
            collectionName = os.path.splitext(filename)[0].split('.')[-1]
            if collectionName in db.list_collection_names():
                db.drop_collection(collectionName)
            collection = db[collectionName]
            with open(os.path.join(folderPath, filename), 'r') as file:
                data = json.load(file)
                for document in data:
                    if not document_exists(collection, document):
                        collection.insert_one(document)
    logging.info(db.list_collection_names())

def setup():
    try:
        # Load configuration data
        # config_data, status_code = load_config()
        # Read the DEMO value from environment variable
        demo_value = os.environ.get('DEMO', 'False').lower()
        logging.info(demo_value)

        # Set demo to True if the value is 'true', False otherwise
        demo = demo_value == 'true'
        if not demo:
            '''# Initialize application settings
            config_initialized, use_case_initialized, status_code = initialize_application()
            if status_code == 200:
                if config_initialized:
                    logging.info("Config data initialized successfully.")
                if use_case_initialized:
                    logging.info("Use case config data initialized successfully.")
            elif status_code == 400:
                # Bad request: Invalid input data or type
                logging.error("Bad request: Invalid input data or type.")
            elif status_code == 500:
                # Internal server error: Error occurred during initialization
                logging.error("Internal server error: Error occurred during initialization.")'''
        
            # Load register configuration
            register_config, status_code = load_register_config()
            if status_code == 200:
                logging.info("Register config loaded successfully.")
            elif status_code == 404:
                logging.error("Register config file not found.")
            elif status_code == 500:
                logging.error("Error loading register config. Check logs for details.")

            # Further processing with register_config if needed
            if register_config is not None:
                super_admin_details = register_config.get("superAdmin")

                collections_initialized, status_code = setup_users_collections()

                if collections_initialized:
                    logging.info("User collections initialized successfully.")
                        
                else:
                    logging.error("Failed to initialize user collections. Check status code for details.")

                # Handle status code if needed
                if status_code == 400:
                    logging.error("Bad request: Invalid input.")
                elif status_code == 500:
                    logging.error("Internal server error: Unexpected error occurred during setup.")

                # Check if database collections were initialized successfully
                if collections_initialized:
                    logging.info("Users DB collections created successfully.")
                else:
                    logging.error("Failed to create Users DB collections.")

                # Create super admin user
                user_setup = ApplicationDataBase()
                existing_user = check_existing_user(user_setup, super_admin_details["username"], super_admin_details["email"])

                if existing_user:
                    logging.warning("Email or username already registered as superAdmin.")
                else:
                    # Validate super admin details
                    if not validateEmail(super_admin_details["email"]):
                        logging.error("Invalid Email in registerConfig")
                    elif not validatePassword(super_admin_details["password"]):
                        logging.error("Password is weak")
                    else:
                        hashed_password = generate_password_hash(super_admin_details["password"], method="pbkdf2:sha256")
                        user_id = generateUserId()
                            
                        user_data = {
                                "userId": user_id,
                                "username": super_admin_details["username"],
                                "email": super_admin_details["email"],
                                "firstName": super_admin_details["firstName"],
                                "lastName": super_admin_details["lastName"],
                                "contactNumber": super_admin_details["contactNumber"],
                                "password": hashed_password,
                                "role": {"superadmin":[]}
                            }

                        user_authentication_data = {
                                "userId": user_id,
                                "contactNumberVerification": False,
                                "oneTimePassword": None,
                                "otpAttemptsCount": 0,
                                "otpAttemptLocked": False,
                                "otpCoolDown": None,
                                "otpSendCount": 0,
                                "otpSendLastTimestamp": None,
                                "otpSendLock": False,
                                "otpSendLockedUntil": None
                            }

                        user_attributes_data = {
                                "userId": user_id,
                                "deviceHash": None,
                                "activeStatus": "inactive"
                            }

                        refresh_token_data = {
                                "userId": user_id,
                                "refreshToken": None
                            }

                        create_user(user_setup, user_data)
                        create_user_authentication(user_setup, user_authentication_data)
                        create_user_attributes(user_setup, user_attributes_data)
                        create_refresh_token(user_setup, refresh_token_data)
        else:
            global client
            mongo_ip = "172.10.10.56"
            mongo_port = "27017"
            db_uri = "mongodb://"+mongo_ip+":"+mongo_port+"/"
            client = MongoClient(db_uri)
            backendDirectory = os.path.abspath(os.path.join(os.path.dirname(__file__)))
            demoDataPath = os.path.join(backendDirectory,"DemoData")
            dbFolders = [name for name in os.listdir(demoDataPath) if os.path.isdir(os.path.join(demoDataPath, name))]

            for dbFolder in dbFolders:
                dbFolderPath = os.path.join(demoDataPath, dbFolder)
                import_json_data(dbFolderPath)
            logging.info("Demo Data Added Successfully")
    except Exception as e:
        logging.error(f"Setup failed: {e}")

