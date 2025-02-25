
import asyncio
import csv
import json
import logging
import os
import time
import uuid
from fastapi import HTTPException,status
from fastapi.responses import StreamingResponse
import pandas as pd
import pymongo
import requests
from Database.organizationDataBase import OrganizationDataBase
from datetime import datetime
from datasets import load_dataset, DatasetDict, Dataset
from db_config import finetuning_config
import concurrent.futures

projectDirectory = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
logDir = os.path.join(projectDirectory, "logs")
logBackendDir = os.path.join(logDir, "backend")
logFilePath = os.path.join(logBackendDir, "logger.log")

tasks = {}
metric_results = {}

class finetune():
    def __init__(self, role: dict, userId: str,orgIds:list):
        self.role = role
        self.userId = userId
        self.orgIds=orgIds
        self.endpoint = finetuning_config["TRAINING_ENDPOINT"]

    async def fine_tune_model(self, input_request):
        try:
            
            # Validate missing or empty fields
            required = ["orgId","user_id","model_id","series_id","csvftlog","dataset_id","seed","r_values","alpha_values","dropout_values","learning_rates","batch_sizes","num_epochs","weight_decays","high_memory","searchlimit","target_loss"]
            missing_fields = [field for field in required if field not in input_request]
            empty_fields = [field for field in required if input_request.get(field) == ""]

            if missing_fields:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": f"Missing fields: {', '.join(missing_fields)}"
                }

            if empty_fields:
                return {
                    "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                    "detail": f"Empty fields: {', '.join(empty_fields)}"
                }
            orgId = input_request["orgId"]

            if orgId not in self.orgIds:
                return {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "detail": "Unauthorized Access "
                }

            # Generate a unique process ID
            process_id = str(uuid.uuid4()).replace('-', '')[:8]

            # Start the fine-tuning process in the background
            asyncio.create_task( self.fine_tune_service(process_id,input_request))


            return {
                "status_code": 200,
                "process_id": process_id,
                "message": "Fine-tuning has been started in the background."
            }

        except HTTPException as http_ex:
            raise http_ex
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred: {str(e)}"
            )
    
    
    
    
    async def fine_tune_service(self, process_id, input_request):
        try:
            model_id = input_request.get("model_id")
            target_loss = input_request.get("target_loss")
            dataset_id = input_request.get("dataset_id")
            orgId = input_request.get("orgId")
            seed = input_request.get("seed")

            # Initialize the organization database
            organizationDB = OrganizationDataBase(orgId)
            if organizationDB.status_code != 200:
                return {
                    "status_code": organizationDB.status_code,
                    "detail": "Error initializing the organization database"
                }

            path = await organizationDB.get_dataset_path(dataset_id)
           
            if not path or path.get("status_code") != 200:
                return {
                    "status_code": path.get("status_code"),
                    "detail": path.get("detail")
                }
            dataset_path = path.get("dataset_path")

            start_time = datetime.now()

            # Update the task with start time
            tasks[process_id] = {
            "user_id":self.userId,
            "model": model_id,
            "status": "started",
            "target_loss":target_loss,
            "start_time": time,
            "end_time": None,
            "async_task": asyncio.current_task()}

            # Config Data for Database
            config_data = {
                "Timestamp": start_time,
                "user_id": self.userId,
                "process_id": process_id,
                "model_id": model_id,
                "dataset_path": dataset_path
            }
            await organizationDB.config_record(config_data)

            # Step 2: Prepare Datasets
            prepare_response = await self.prepare_datasets(dataset_path, seed)
            if not prepare_response or prepare_response.get("status_code") != 200:
                return {
                    "status_code": prepare_response.get("status_code"),
                    "detail": prepare_response.get("detail")
                }

            splitdataset_Path = prepare_response.get("dataset_path")

            # Step 3: Fine-Tune the Model
            fine_tune_response = await self.control_random(process_id, splitdataset_Path, input_request)
            if not fine_tune_response or fine_tune_response.get("status_code") != 200:
                return {
                    "status_code": fine_tune_response.get("status_code"),
                    "detail": fine_tune_response.get("detail")
                }

            # Step 4: Mark Completion
            tasks[process_id]["status"] = "completed"
            tasks[process_id]["end_time"] = datetime.now()

            return fine_tune_response

        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(500, f"An unexpected error occurred: {str(e)}")

    
    def get_current_timestamp(self):
        return int(time.time())


    async def control_random(self,process_id,splitdataset,input_request):
        try:
            model_id = input_request.get("model_id")
            series_id = input_request.get("series_id")
            target_loss = input_request.get("target_loss")
            orgId = input_request.get("orgId")
            csvftlog = input_request.get("csvftlog")
            r_values= input_request.get("r_values")
            alpha_values= input_request.get("alpha_values")
            dropout_values = input_request.get("dropout_values")
            learning_rates = input_request.get("learning_rates")
            batch_sizes = input_request.get("batch_sizes")
            num_epochs = input_request.get("num_epochs")
            weight_decays = input_request.get("weight_decays")
            high_memory = input_request.get("high_memory")
            searchlimit = input_request.get("searchlimit")
            target_loss = input_request.get("target_loss")
            # Initialize the organization database
            organizationDB = OrganizationDataBase(orgId)
            
            # Check if organizationDB is initialized successfully
            if organizationDB.status_code != 200:
                return {
                    "status_code": organizationDB.status_code,
                    "detail": "Error initializing the organization database"
                }
            
            timestamp = self.get_current_timestamp()
            metric_results[process_id] = []
            # status = "started"
            # self.Inserting.update_status_in_mongo(self,self.series_id, self.model_id, status)
            
            status_record = {
            "user_id" : self.userId,
            "process_id": process_id,
            "model_id": model_id,
            "status": "started"
            }
            tasks[process_id]["status"] = "In Progress"
            status = await organizationDB.update_status_in_mongo(status_record)
            # Ensure the directory exists
            os.makedirs(os.path.dirname(csvftlog), exist_ok=True)

            # Check if the file exists
            file_exists = os.path.exists(csvftlog)

            try:
                header = ['series_id', 'r', 'lora_alpha', 'lora_dropout', 'learning_rate', 
                            'batch_size', 'num_epochs', 'weight_decay', 'eval_loss']

                if file_exists:
                    # Check if the file already has headers
                    with open(csvftlog, mode='r') as file:
                        reader = csv.reader(file)
                        existing_headers = next(reader, None)  # Read the first row (headers)
                    
                    if existing_headers is None or existing_headers != header:
                        # If headers are missing or different, prepend headers to the file
                        with open(csvftlog, mode='r') as file:
                            data = file.readlines()  # Read all existing lines

                        # Write back headers and original data
                        with open(csvftlog, mode='w', newline='') as file:
                            writer = csv.writer(file)
                            writer.writerow(header)  # Write header
                            file.writelines(data)  # Write the original data after the header
                else:
                    # Create a new file and write the headers
                    with open(csvftlog, mode='w', newline='') as file:
                        writer = csv.writer(file)
                        writer.writerow(header)  # Write header for a new file
                
            except Exception as e:
                logging.error(f"Error initializing or appending to CSV: {e}")
                return {"status_code": 500, "detail": f"CSV handling Failed: {str(e)}"}
            high_memory = bool(high_memory)
            # Main loop variables
            
            batchFT = True
            start_search = True
            r_index = 0
            lora_alpha_index = 0
            lora_dropout_index = 0   
            run_crv1 = False
            abc_counter = 0
            top_config_counter = 0
            bias_counter = 0
            increment_counter = 0
            limit = 0
            prev_loss = 10
            eval_loss = 9
            current_loss = 10
            tasks[process_id]["status"] = "In Progress"
            status_record["status"] = "in progress "
            await organizationDB.update_status_in_mongo(status_record)
            while batchFT and abc_counter < searchlimit:
                try:
                    
                
                    logging.info(f"Starting iteration {abc_counter}")
                    
                    tasks[process_id]["status"] = "In Progress"
                    status_record["status"] = "in progress"
                    await organizationDB.update_status_in_mongo(status_record)
                    # Biased random config generator logic
                    if top_config_counter < bias_counter:
                        unique_config = await self.get_top_five_sets(abc_counter,csvftlog)
                        logging.info(f"Using bias set: {unique_config}")
                        if not unique_config or unique_config.get("status_code") != 200:
                                # await self.mongoinfo.store_session_metrics(self.user_id,process_id, self.session_metrics,self.model_id,target_loss)
                                tasks[process_id]["status"] = "Failed"
                                status_record["status"] = "Failed "
                                await organizationDB.update_status_in_mongo(status_record)
                                return{
                                    "status_code": unique_config.get("status_code"),
                                    "detail": unique_config.get("detail")
                                }
                        
                        top_config_counter += 1
                        run_crv1 = False
                    else:
                        logging.info("Using Controlled Random Approach")
                        run_crv1 = True
                    
                    # Pre-search configuration
                    if run_crv1:
                       
                        

                        try:   
                            
                            reseponse =await self.regularize_search(abc_counter, eval_loss, r_index, lora_alpha_index, lora_dropout_index,r_values,alpha_values,dropout_values)
                            if not reseponse or reseponse.get("status_code") != 200:
                                tasks[process_id]["status"] = "Failed"
                                # await self.mongoinfo.store_session_metrics(self.user_id,process_id, self.session_metrics,self.model_id,target_loss)
                                status_record["status"] = "Failed "
                                await organizationDB.update_status_in_mongo(status_record)
                                return{
                                    "status_code": reseponse.get("status_code"),
                                    "detail": reseponse.get("detail"),
                                }
                            r = r_values[reseponse.get("r_index")]
                            lora_alpha = alpha_values[reseponse.get("lora_alpha_index")]
                            lora_dropout = dropout_values[reseponse.get("lora_dropout_index")]
                            learningrate = learning_rates[0]
                            weightdecay = weight_decays[0]
                            batchsize =batch_sizes[0]
                            unique_config = [r, lora_alpha, lora_dropout, learningrate, batchsize, num_epochs, weightdecay]

                            
                            
                        except IndexError as e:
                            logging.error(f"Index error with configuration lists: {e}")
                            return {"status_code": 500, "detail": f"Configuration index error: {str(e)}"}
                    # Skip if configuration already exists
                    
                    exists, exist_loss = await self.get_config_eval_loss(unique_config,csvftlog,series_id)
                    if exists == True:
                        print("This however takes the same loss for this same config, which is eval_loss: ", exist_loss)
                        eval_loss = exist_loss
                        abc_counter += 1
                        unique_config = None
                        
                    # Main Loop
                    if unique_config != None:
                        abc_counter += 1
                    # self.get_gpu_memory_usage()
                    
                    test_payload = await self.create_sample_request(self.userId,model_id,num_epochs,splitdataset,weightdecay,learningrate,batchsize,high_memory,r,lora_alpha,lora_dropout,abc_counter)
                    if not test_payload or test_payload.get("status_code") != 200:
                                tasks[process_id]["status"] = "Failed"
                                status_record["status"] = "Failed "
                                await organizationDB.update_status_in_mongo(status_record)
                                # await self.mongoinfo.store_session_metrics(self.user_id,process_id, self.session_metrics,self.model_id,target_loss)
                                return{
                                    "status_code": test_payload.get("status_code"),
                                    "detail": test_payload.get("detail"),
                                }
                    data = test_payload.get("payload")
                    # Send the POST request
                    response = requests.post(self.endpoint,json=data,headers={"Content-Type": "application/json"})
                    response = response.json()
                    if not response or response.get("status_code") != 200:
                            tasks[process_id]["status"] = "Failed"
                            status_record["status"] = "Failed "
                            await organizationDB.update_status_in_mongo(status_record)
                            # await self.mongoinfo.store_session_metrics(self.user_id,process_id, self.session_metrics,self.model_id,target_loss)
                            return{
                                "status_code": response.get("status_code"),
                                "detail": response.get("detail"),
                            }
                            

                            # Try to get eval_loss from the response, if it exists
                    eval_loss = response.get("eval_loss")
                    
                   
                    
                    header = ['series_id', 'r', 'lora_alpha', 'lora_dropout', 'learning_rate', 
                            'batch_size', 'num_epochs', 'weight_decay', 'eval_loss']

                    # Ensure the directory exists
                    os.makedirs(os.path.dirname(csvftlog), exist_ok=True)

                    # Check if the file exists
                    file_exists = os.path.exists(csvftlog)

                    try:
                        # Open the file in append mode
                        with open(csvftlog, mode='a', newline='') as file:
                            writer = csv.writer(file)
                            
                            # Write the header only if the file is new
                            if not file_exists:
                                writer.writerow(header)
                            
                            # Log the current results
                            writer.writerow([
                                series_id, r, lora_alpha, lora_dropout, learningrate,
                                batchsize, num_epochs, weightdecay, eval_loss
                            ])
                    except Exception as e:
                        logging.error(f"Error initializing or writing to CSV file: {e}")
                        return {"status_code": 500, "detail": f"CSV operation Failed: {str(e)}"}

                    current_loss = eval_loss
        
                    # Target Loss Check
                    if eval_loss <= target_loss:
                        batchFT = False
                        best_flag = 1 if eval_loss < best_loss else 0  
                        last_metrics = {
                            "series_id": series_id,
                            "r": r,
                            "lora_alpha": lora_alpha,
                            "lora_dropout": lora_dropout,
                            "learning_rate": learningrate,
                            "batch_size": batchsize,
                            "num_epochs": num_epochs,
                            "weight_decay": weightdecay,
                            "eval_loss": eval_loss,
                            "best_flag": best_flag  # Mark last entry correctly
                        }
                        metric_results[process_id].append(last_metrics)
                        

                        print("Target loss reached. Terminating Search.")
                    if abc_counter == 1: # First Iteration
                        best_loss = current_loss
                        best_flag = 1
                    else:
                    # Determine best_flag **before** updating best_loss
                        best_flag = 1 if eval_loss < best_loss else 0  # Corrected logic
                        
                    # Best Loss Set    
                    if current_loss <= best_loss: 
                        best_loss = current_loss
                        best_params = {
                            "r": r,
                            "lora_alpha": lora_alpha,
                            "lora_dropout": lora_dropout,
                        }
                        print(f"New best found: {best_params} with loss: {best_loss}")
                        increment_counter = 0  # Reset counter on new best  
                    # Search Logic
                    current_loss = eval_loss
                    current_metrics = {
                        "series_id": series_id,
                        "r": r,
                        "lora_alpha": lora_alpha,
                        "lora_dropout": lora_dropout,
                        "learning_rate": learningrate,
                        "batch_size": batchsize,
                        "num_epochs": num_epochs,
                        "weight_decay": weightdecay,
                        "eval_loss": eval_loss,
                        "best_flag": best_flag  # Add the best_flag to indicate whether the loss is better (1) or worse (0)
                    }

                    metric_results[process_id].append(current_metrics)
                    if increment_counter < limit: # Below the limit

                        response = await self.search_forward(abc_counter,best_params,r_index,lora_alpha_index,lora_dropout_index,r_values,alpha_values,dropout_values)
                        if not response or response.get("status_code") != 200:
                                tasks[process_id]["status"] = "Failed"
                                status_record["status"] = "Failed "
                                organizationDB.update_status_in_mongo(status_record)
                                # await self.mongoinfo.store_session_metrics(self.user_id,process_id, self.session_metrics,self.model_id,target_loss)
                                return{
                                    "status_code": response.get("status_code"),
                                    "detail": response.get("detail"),
                                }

                        r_index= response.get("r_index")
                        lora_alpha_index= response.get("lora_alpha_index")
                        lora_dropout_index= response.get("lora_dropout_index")

                        increment_counter += 1

                    else: # Above the limit
                        
                        if current_loss < prev_loss:
                            response=await self.search_forward(abc_counter,best_params,r_index,lora_alpha_index,lora_dropout_index,r_values,alpha_values,dropout_values)
                            if not response or response.get("status_code") != 200:
                                tasks[process_id]["status"] = "Failed"
                                status_record["status"] = "Failed "
                                await organizationDB.update_status_in_mongo(status_record)
                                return{
                                    "status_code": response.get("status_code"),
                                    "detail": response.get("detail"),
                                }
                            r_index= response.get("r_index")
                            lora_alpha_index= response.get("lora_alpha_index")
                            lora_dropout_index= response.get("lora_dropout_index")
                        if prev_loss < current_loss:
                            response=self.search_backward(abc_counter,best_params,r_index,lora_alpha_index,lora_dropout_index,r_values,alpha_values,dropout_values)
                            if not response or response.get("status_code") != 200:
                                tasks[process_id]["status"] = "Failed"
                                status_record["status"] = "Failed "
                                await organizationDB.update_status_in_mongo(status_record)
                                return{
                                    "status_code": response.get("status_code"),
                                    "detail": response.get("detail"),
                                }
                            r_index= response.get("r_index")
                            lora_alpha_index= response.get("lora_alpha_index")
                            lora_dropout_index= response.get("lora_dropout_index")


                           
                except Exception as e:
                    logging.error(f"Unexpected error in iteration {abc_counter}: {str(e)}")
                    tasks[process_id]["status"] = "Failed"
                    # status = "Failed : Iteration error"
                    status_record["status"] = "Failed "
                    await organizationDB.update_status_in_mongo(status_record)

                    # self.Inserting.update_status_in_mongo(self.series_id, self.model_id,status )
                    return {"status_code": 500, "detail": f"Unexpected error: {str(e)}"}
            # metrics = list(self.session_metrics.values())[0]
            metrics = metric_results.get(process_id)
            
            kgjfdu = await organizationDB.store_session_metrics(self.userId,process_id, metrics,model_id,target_loss)
            tasks[process_id]["status"] = "Completed"
            tasks[process_id]["end_time"] = timestamp
            status_record["status"] = "Completed "
            await organizationDB.update_status_in_mongo(status_record)
            allresponse = await organizationDB.get_metrics(process_id)
            resultpath= await self.write_data_to_excel(allresponse)
            await organizationDB.update_result_path(process_id, resultpath["file_path"])
            return {
                "status_code": 200,
                "detail": "Training completed successfully",
                "final_loss": eval_loss,
                "iterations_completed": abc_counter
            }

        except Exception as e:
            tasks[process_id]["status"] = "Failed"
            status_record["status"] = "Failed "
            await organizationDB.update_status_in_mongo(status_record)
            logging.error(f"Control random process Failed: {str(e)}")
            return {"status_code": 500, "detail": f"Process Failed: {str(e)}"}



    async def get_top_five_sets(self, abc_counter,csvftlog):
        """
        Returns one of the top five configurations with the lowest evaluation loss from a CSV file.

        Parameters:
            abc_counter (int): A counter to select one of the top five sets.

        Returns:
            dict: A dictionary with status_code and detail, including the data or error message.
        """
        try:
            # Check if the file exists
            if not os.path.isfile(csvftlog):
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": f"File '{csvftlog}' not found or inaccessible.",
                }

            # Read the CSV file
            try:
                df = pd.read_csv(csvftlog)
            except pd.errors.EmptyDataError:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": f"File '{csvftlog}' is empty or corrupted.",
                }

            # Check if the DataFrame is empty
            if df.empty:
                return {
                    "status_code": status.HTTP_204_NO_CONTENT,
                    "detail": "CSV file is empty. No data to process.",
                }

            # Validate required columns
            required_columns = {'r', 'lora_alpha', 'lora_dropout', 'learning_rate', 'batch_size', 'num_epochs', 'weight_decay', 'eval_loss'}
            if not required_columns.issubset(df.columns):
                missing_columns = list(required_columns - set(df.columns))
                return {
                    "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                    "detail": f"CSV file is missing required columns: {missing_columns}.",
                }

            # Process top configurations
            unique_combinations = df.groupby(
                ['r', 'lora_alpha', 'lora_dropout', 'learning_rate', 'batch_size', 'num_epochs', 'weight_decay']
            )['eval_loss'].min().reset_index()

            sorted_combinations = unique_combinations.sort_values(by='eval_loss')
            
            top_five_unique_sets = sorted_combinations.head(5).drop(columns=['eval_loss'])

            # Validate abc_counter bounds
            if abc_counter >= len(top_five_unique_sets):
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": f"abc_counter {abc_counter} is out of bounds. Valid range is 0 to {len(top_five_unique_sets) - 1}.",
                }

            # Retrieve and process the selected set
            set_to_return = top_five_unique_sets.iloc[abc_counter % 5].tolist()
            for idx in [0, 1, 4, 5]:  # Convert specific indices to int
                set_to_return[idx] = int(set_to_return[idx])

            return {
                "status_code": status.HTTP_200_OK,
                "detail": "Set retrieved successfully.",
                "data": set_to_return,
            }
        
        except Exception as e:
            # Log and handle unexpected errors
            return {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": f"Unexpected error occurred: {str(e)}",
            }

    async def create_sample_request(self,user_id,model_id,num_epochs, splitdataset, weightdecay, learningrate, batchsize, high_memory, r, lora_alpha, lora_dropout, abc_counter
            ):
        try:
            # Generate a unique ID
            uniqueid = str(uuid.uuid1())  # Convert to string

            # Create the payload
            payload = {
                "userid": user_id,
                "uniqueid": uniqueid,
                "modelid": model_id,
                "high_memory": high_memory,
                "r": r,
                "lora_alpha": lora_alpha,
                "lora_dropout": lora_dropout,
                "abc_counter": abc_counter,
                "weight_decay": weightdecay,
                "learning_rate": learningrate,
                "batchsize": batchsize,
                "num_epochs": num_epochs,
                "split_dataset": splitdataset,
                
                
                # "model_metadata": model_metadata
            }

            # Serialize to JSON to validate
            json.dumps(payload)  # Ensure it's valid JSON

            return {
                "status_code": 200,
                "detail": "Payload successfully created and serialized.",
                "payload": payload
            }
        
        except TypeError as e:
            error_message = f"JSON serialization error: {str(e)}"

            return {
                "status_code": 400,
                "detail": error_message,
            }



    async def search_forward(self, abc_counter, best_params, r_index, lora_alpha_index, lora_dropout_index,r_values,alpha_values,dropout_values):
        
        try:
            r_length = len(r_values)
            alpha_length = len(alpha_values)
            dropout_length = len(dropout_values)
            total_length = r_length + alpha_length + dropout_length

            # Initialize variables with default values from best_params
            r = best_params.get("r")
            lora_alpha = best_params.get("lora_alpha" )
            lora_dropout = best_params.get("lora_dropout")

            # Determine which parameter to increment based on abc_counter
            if abc_counter < r_length:
                r_index = min(r_index + 1, r_length - 1)
                r = r_values[r_index]
            elif abc_counter < (r_length + alpha_length):
                lora_alpha_index = min(lora_alpha_index + 1, alpha_length - 1)
                lora_alpha = alpha_values[lora_alpha_index]
            elif abc_counter < total_length:
                lora_dropout_index = min(lora_dropout_index + 1, dropout_length - 1)
                lora_dropout = dropout_values[lora_dropout_index]
            else:
                return{
                    "detail":"abc_counter exceeds the total number of values in all lists."}

            
            return {
                "status_code": 200,
                "detail": "search_forward completed successfully.",
                "r_index": r_index,
                "lora_alpha_index": lora_alpha_index,
                "lora_dropout_index": lora_dropout_index,
                "r": r,
                "lora_alpha": lora_alpha,
                "lora_dropout": lora_dropout
            }
        
        except IndexError as e:
            return {"status_code": 400, "detail": f"IndexError: {str(e)}"}
        except KeyError as e:
            return {"status_code": 400, "detail": f"KeyError: Missing key {str(e)} in best_params."}
        except Exception as e:
            return {"status_code": 500, "detail": f"An unexpected error occurred: {str(e)}"}
    


    async def search_backward(self, abc_counter, best_params, r_index, lora_alpha_index, lora_dropout_index,r_values,alpha_values,dropout_values):
        
        try:
            r_length = len(r_values)
            alpha_length = len(alpha_values)
            dropout_length = len(dropout_values)
            total_length = r_length + alpha_length + dropout_length

            # Initialize variables with default values from best_params
            r = best_params.get("r")
            lora_alpha = best_params.get("lora_alpha")
            lora_dropout = best_params.get("lora_dropout")

            # Determine which parameter to decrement based on abc_counter
            if abc_counter < r_length:
                r_index = max(r_index - 1, 0)
                r = r_values[r_index]
            elif abc_counter < (r_length + alpha_length):
                lora_alpha_index = max(lora_alpha_index - 1, 0)
                lora_alpha = alpha_values[lora_alpha_index]
            elif abc_counter < total_length:
                lora_dropout_index = max(lora_dropout_index - 1, 0)
                lora_dropout = dropout_values[lora_dropout_index]
            else:
                raise IndexError("abc_counter exceeds the total number of values in all lists.")

            
            return {
                "status_code": 200,
                "detail": "search_backward completed successfully.",
                "r_index": r_index,
                "lora_alpha_index": lora_alpha_index,
                "lora_dropout_index": lora_dropout_index,
                "r": r,
                "lora_alpha": lora_alpha,
                "lora_dropout": lora_dropout
            }
        
        except IndexError as e:
            return {"status_code": 400, "detail": f"IndexError: {str(e)}"}
        except KeyError as e:
            return {"status_code": 400, "detail": f"KeyError: Missing key {str(e)} in best_params."}
        except Exception as e:
            return {"status_code": 500, "detail": f"An unexpected error occurred: {str(e)}"}




    async def get_config_eval_loss(self,config,csvftlog,series_id):
        if not os.path.isfile(csvftlog):
            return False, None  # File does not exist
        with open(csvftlog, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['series_id'] == series_id:
                    if (int(row['r']) == config[0] and
                        int(row['lora_alpha']) == config[1] and
                        float(row['lora_dropout']) == config[2] and
                        float(row['learning_rate']) == config[3] and
                        int(row['batch_size']) == config[4] and
                        int(row['num_epochs']) == config[5] and
                        float(row['weight_decay']) == config[6]):
                        return True, row['eval_loss']
        return False, None


    async def regularize_search(self, abc_counter, eval_loss, r_index, lora_alpha_index, lora_dropout_index,r_values,alpha_values,dropout_values):

        """
        Regularize search indices to ensure they stay within valid bounds.
        """
        try:
            
            if abc_counter > 0:
                prev_loss = eval_loss
            else:
                prev_loss = 10
            
            # Wrap around for forward direction by resetting indices if out of bounds
            if r_index >= len(r_values):
                r_index = 0
            if lora_alpha_index >= len(alpha_values):
                lora_alpha_index = 0
            if lora_dropout_index >= len(dropout_values):
                lora_dropout_index = 0
                
            # Wrap around for backward direction by setting to last index if negative
            if r_index < 0:
                r_index = len(r_values) - 1
            if lora_alpha_index < 0:
                lora_alpha_index = len(alpha_values) - 1
            if lora_dropout_index < 0:
                lora_dropout_index = len(dropout_values) - 1
            # Return the adjusted indices and previous loss as a success response
            return {
                "status_code": 200,
                "detail": "Indices regularized successfully.",
                "r_index": r_index,
                "lora_alpha_index": lora_alpha_index,
                "lora_dropout_index": lora_dropout_index,
                "prev_loss": prev_loss
            }

        except AttributeError as e:
            return {
                "status_code": 500,
                "detail": f"Attribute error: {str(e)} - One or more parameters may be missing or incorrect."
            }
        except TypeError as e:
            return {
                "status_code": 500,
                "detail": f"Type error: {str(e)} - Ensure all parameters have valid types."
            }
        except IndexError as e:
            return {
                "status_code": 400,
                "detail": f"Index error: {str(e)} - Indices are out of bounds for one of the parameters."
            }
        except Exception as e:
            return {
                "status_code": 500,
                "detail": f"Unexpected error in regularize_search: {str(e)}"
            }

    async def write_data_to_excel(self,data):
        """
        Writes a list of dictionaries into an Excel file with a generic path.

        Args:
            data (list): List of dictionaries containing data to write.

        Returns:
            dict: A dictionary containing status code and file path.
        """
        try:
            filtered_data = [{k: v for k, v in row.items() if k != list(row.keys())[-1]} for row in data]
            # Convert data into a DataFrame
            df = pd.DataFrame(filtered_data)
            timestamp = int(time.time())
            # Specify the directory and file path
            directory = "C:/Users/Admin/projects/projects/Genx-Platform-Backend/AIPlatform_backend/AiManagement"
            file_name = f"result_{timestamp}.xlsx"
            file_path = os.path.join(directory, file_name)
            
            # Ensure the directory exists
            if not os.path.exists(directory):
                os.makedirs(directory)
            
            # Write the DataFrame to an Excel file
            df.to_excel(file_path, index=False, sheet_name="Metrics")
            
            print(f"Data successfully written to {file_path}")
            return {"status_code": 200, "file_path": file_path}
        
        except Exception as e:
            print(f"An error occurred: {e}")
            return {"status_code": 500, "detail": str(e)}
    async def prepare_datasets(self,dataset_path,seed):
        """
        Loads a CSV file as a Hugging Face dataset, formats the data, and splits it into train and test sets.

        Returns:
            dict: Contains 'train' and 'test' dataset file paths.
        """
        try:
            test_size = 0.2  # Define test split ratio

            # Load the dataset
            dataset = load_dataset('csv', data_files=dataset_path)
            
            # Validate dataset structure
            if 'train' not in dataset or len(dataset['train']) == 0:
                return {"status_code": 400, "detail": "Invalid or empty dataset."}

            def format_data(example):
                 # Print each row before processing
                input_text = example.get('input', '').strip()
                response_text = example.get('output', '').strip()

                if not input_text or not response_text:
                    return None  # This may cause complete row removal
                
                formatted_text = f"###Input: {input_text} ###Response: {response_text} <|end_of_text|>"

                return {"text": formatted_text}
            # Apply formatting while filtering out None values
            formatted_dataset = dataset.map(format_data, remove_columns=dataset['train'].column_names)
            # print("Formatted Dataset Sample:", formatted_dataset['train'][:-1])
            

            # Split dataset
            split_dataset = formatted_dataset['train'].train_test_split(test_size=test_size, shuffle=True, seed=seed)
            
            
            trainpath = "C:/Users/Admin/projects/projects/Genx-Platform-Backend/AIPlatform_backend/AiManagement"
            split_dataset.save_to_disk(trainpath)
            
            response = {
                "status_code": 200,
                "detail": "Datasets prepared successfully.",
                "dataset_path": trainpath
            }
            
            return response 
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"File not found: {dataset_path}")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Dataset loading error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

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

    def cancel_fine_tune(self,data):
        try:
            required_fields = ["process_id","orgId"]
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                logging.error(f"Missing required fields: {', '.join(missing_fields)}")
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": f"Missing required fields: {', '.join(missing_fields)}."
                }
            process_id = data["process_id"]
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
            # Check if process ID exists in the running tasks
            task = tasks.get(process_id)
            if not task:
                return {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "detail": f"No running task found with process ID: {process_id}",
                }

            user_id = task.get("user_id", None)
            model_id = task.get("models", None)
            target_loss = task.get("target_loss", None)

            if not user_id or not model_id:
                return {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "detail": f"Missing required fields in task data for process ID: {process_id}",
                }

            # Attempt to cancel the task
            async_task = task.get("async_task")
            if async_task:
                async_task.cancel()
                try:
                    async_task
                except asyncio.CancelledError:
                    pass  # Task was successfully canceled

            # Update the task status in the store
            tasks[process_id] = {
                "status": "canceled",
                "end_time": datetime.now()
            }

            # Prepare the status update record
            status_record = {
                "process_id": process_id,
                "user_id": user_id,
                "model_id": model_id,
                "status": "canceled"
            }

            # Update MongoDB with the new status
            update_result = organizationDB.update_status_in_mongo(status_record)

            # Retrieve session metrics safely
            metrics = metrics.get(process_id)

            # Remove the task from the running store
            tasks.pop(process_id, None)

            # Store session metrics
            store_result = organizationDB.store_session_metrics(user_id, process_id, metrics, model_id, target_loss)

            return {
                "status_code": 200,
                "message": f"Fine-tuning process with ID {process_id} has been canceled.",
                "mongo_update": update_result,
                "store_metrics_result": store_result
            }

        except HTTPException as http_ex:
            raise http_ex  # Re-raise FastAPI-specific exceptions
        except KeyError as key_ex:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing key in request: {str(key_ex)}",
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred: {str(e)}",
            )
