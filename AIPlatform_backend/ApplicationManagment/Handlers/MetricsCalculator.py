from asyncio.log import logger
from datetime import datetime
from fastapi import HTTPException
import json
import os
from typing import List, Optional
import yaml
from Database.evaluationSetup import MongoDBHandler
import numpy as np
import pandas as pd
import requests
import logging
from ApplicationManagment.Handlers.Metrics import Metrics
from ApplicationManagment.Handlers.ScoreCalculator import ScoreCalculator
from db_config import eval_config
from ApplicationManagment.Handlers.storeExcel import JSONToExcelConverter
from utils import MetricStatus, MetricStatusRecord, MetricsPayload

# Initialize components
score_calculator = ScoreCalculator(eval_config['SCORE_ENDPOINT'])
metricsHandler = Metrics()

class MetricsCalculator:
    def __init__(self, mongoHandler: MongoDBHandler, payload):
        self.mongoHandler = mongoHandler
        self.payload = payload
        self.payload = payload
        self.payload_file_path = payload.get('payload_file_path')
        self.user_id = payload.get('user_id')
        self.process_id = payload.get('process_id')
        self.metrics = payload.get('metrics', [])  # Default empty list if not present
        self.process_name = payload.get('process_name')
        self.task_statuses = {}

    async def do_metrics(self, metric_id):
        start_time = datetime.now()
        try:
            payload = self.payload_file_path
            collection = self.load_yaml_data(payload)

            # Check if model is completed - this should be an async call
            model_completed = await self.mongoHandler.check_model_completed_status(self.process_id)
            if not model_completed:
                raise HTTPException(status_code=400, detail="Model processing not completed")

            # Get results document - this should be an async call
            results_doc = await self.mongoHandler.get_result_document_by_process_id(self.process_id)
            if not results_doc:
                raise HTTPException(status_code=404, detail="Results document not found")

            result_path = results_doc['results_path']
            config_type = results_doc['config_type']
            model_ids = [model["model_id"] for model in results_doc["models"]]
            object_id = results_doc['_id']

            # Initialize task statuses
            self.task_statuses[self.process_id] = {
                "models": {model_id: "Not Started - Metrics" for model_id in model_ids},
                "overall_status": "Evaluation Completed. Calculating Metrics",
                "start_time": start_time,
                "end_time": None
            }

            # Create initial status record
            status_record = MetricStatusRecord(
                user_id=self.user_id,
                process_id=self.process_id,
                metric_id=metric_id,
                models=[MetricStatus(
                    model_id=model_id,
                    status="Not Started - Metrics"
                ) for model_id in model_ids],
                overall_status="Evaluation Completed. Calculating Metrics",
                start_time=start_time
            )

            # Update metric status - this should be an async call
            await self.mongoHandler.update_metric_status_record(status_record, self.process_name)

            # Process each model
            for index, model_id in enumerate(model_ids):
                try:
                    # Update model status to "Calculating"
                    self.task_statuses[self.process_id]["models"][model_id] = "Calculating Metrics"
                    await self.mongoHandler.update_metric_model_status(
                        self.process_id, 
                        model_id, 
                        "Calculating Metrics",
                        metric_id,
                        "Evaluation completed. Calculating Metrics."
                    )

                    # Calculate metrics - this is synchronous
                    metrics_results = self.calculate_metrics(collection, self.metrics)
                    print("metrics_results", metrics_results)

                    if metrics_results.get('status_code') == 200:
                        try:
                            # Update status to completed
                            logger.info("Updating model status to Completed...")
                            new_status = "Metrics Calculation Completed"
                            await self.mongoHandler.update_metric_model_status(
                                self.process_id, 
                                model_id, 
                                new_status,
                                metric_id,
                                "Evaluation completed. Calculating Metrics."
                            )
                        except Exception as e:
                            logger.error(f"Error updating model status to Completed: {str(e)}")
                            raise

                        try:
                            # Update metrics results
                            print("Updating metrics results record...")
                            await self.mongoHandler.update_metrics_results_record(
                                self.process_id,
                                self.user_id,
                                config_type,
                                object_id,
                                metric_id,
                                self.process_name,
                                model_id,
                                metrics_results['data']
                            )
                        except Exception as e:
                            logger.error(f"Error updating metrics results record: {str(e)}")
                            raise

                    else:
                        print(f"Metrics calculation failed with status: {metrics_results.get('status_code')}")
                        # Update status to failed
                        await self.mongoHandler.update_metric_model_status(
                            self.process_id,
                            model_id,
                            "Metrics Calculation Failed",
                            metric_id,
                            "Evaluation completed. Calculating Metrics."
                        )
                        raise HTTPException(
                            status_code=500,
                            detail=f"Metrics calculation failed for model {model_id}"
                        )

                except Exception as e:
                    print(f"Error processing model {model_id}: {str(e)}")
                    try:
                        await self.mongoHandler.update_metric_model_status(
                            self.process_id,
                            model_id,
                            "Metrics Calculation Failed",
                            metric_id,
                            "Metrics Calculation Failed"
                        )
                    except Exception as update_error:
                        logger.error(f"Error updating failure status: {str(update_error)}")
                    raise

            try:
                # Update overall status when all models are processed
                print("Updating overall status to Completed...")
                final_status = "Metrics Calculation Completed"
                await self.mongoHandler.update_metric_overall_status(self.process_id, metric_id, final_status)
            except Exception as e:
                logger.error(f"Error updating overall status: {str(e)}")
                raise

            return {
                "status": self.task_statuses,
                "detail": "Metrics Calculation completed"
            }

        except Exception as e:
            logger.error(f"Unexpected error in metrics calculation: {e}")
            try:
                # Update overall status to failed
                await self.mongoHandler.update_metric_overall_status(
                    self.process_id,
                    metric_id,
                    "Metrics Calculation Failed"
                )
            except Exception as update_error:
                logger.error(f"Error updating failure status: {str(update_error)}")
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    def calculate_metrics(self, data, metrics):
        print("metrics --",metrics)
        try:
            
            if isinstance(metrics, str):
                metrics = [mode.strip() for mode in metrics.split(",")]
    
            final_result = data
            predictions = []
            references = []
           
            # Process each payload
            for payload_key, questions in data.items():
                #print("questions", questions)
                if not isinstance(questions, list):
                    logging.error(f"Invalid format for payload '{payload_key}': Expected a list, got {type(questions)}")
                    continue  # Skip invalid entries

                for question in questions:
                    if not isinstance(question, dict):
                        logging.error(f"Invalid question format: Expected a dictionary, got {type(question)}")
                        continue  # Skip invalid entries

                    prediction = question.get("response", "").strip()
                    reference = question.get("answer", "").strip()
                   
                    if prediction or reference:
                        predictions.append(prediction)
                        references.append(reference)
            # for question in data.get('query', []):
            #     prediction = question.get("response", "")
            #     reference = question.get("answer", "")
            #     if prediction or reference:
            #         predictions.append(prediction)
            #         references.append(reference)
            # print("actual data ----", predictions, references)

            for mode in metrics:
                if mode == "BERT Score":
                    P, R, F1 = metricsHandler.bert_score_evaluation(predictions, references)
                    final_result['BERT_score'] = {
                        'precision': P,
                        'recall': R,
                        'f1': F1
                    }
                    print("bert completed")
                elif mode == "BLEU Score":
                    score = metricsHandler.calculate_bleu(predictions, references)
                    final_result['BLEU Score'] = {
                        'score' : score
                    }   
                elif mode == "ROUGE Score":
                    rouge1_f1, rouge2_f1, rougel_f1 = metricsHandler.rouge_score_evaluation(predictions, references)
                    final_result['ROUGE_score'] = {
                        'ROUGE-1': rouge1_f1,
                        'ROUGE-2': rouge2_f1,
                        'ROUGE-L': rougel_f1
                    }
                    print("rouge completed")


                elif mode == "METEOR":
                    print("METEOR")
                    meteor_score = metricsHandler.calculate_meteor(predictions, references)
                    final_result['METEOR_score'] = {
                        'score': meteor_score
                    }
                    print("meteor completed")


                elif mode == "Multi-Class F1":
                    print("Multi-Class F1")
                    f1_scores = metricsHandler.calculate_multi_f1(predictions, references)
                    final_result['F1_scores'] = f1_scores
                    print("f1 completed")


                elif mode == "RER":
                    print("hello -----RER",)
                    rer_score = Metrics.calculate_rer(predictions, references)
                    final_result['RER_score'] = {
                        'score': rer_score
                    }
                    print("rer completed")

                elif mode == "NDCG":
                    dcg_score = Metrics.ndcg_at_k(predictions, references)
                    final_result['DCG_score'] = {
                        'score': dcg_score
                    }
                elif mode == "MAP":
                    map_score = Metrics.mean_average_precision(predictions, references)
                    final_result['MAP_Score'] = {
                        'score': map_score
                    }
                elif mode == "MRR":
                    mrr_score = Metrics.calculate_mrr(predictions, references)
                    final_result["MRR"] = {
                        'score': mrr_score
                    }
                    print("mrr completed")
                elif mode in ["Cosine Similarity", "Exact Match"]:
                    score_data = score_calculator.get_scores_data(data, mode)
                    
                    # Initialize containers for each confusion matrix category
                    true_positive = []
                    true_negative = []
                    false_positive = []
                    false_negative = []

                    # Iterate through the categories and populate the respective lists
                    for key, value in score_data.items():
                        if key == "TruePositive":
                            true_positive.extend(value)
                        elif key == "TrueNegative":
                            true_negative.extend(value)
                        elif key == "FalsePositive":
                            false_positive.extend(value)
                        elif key == "FalseNegative":
                            false_negative.extend(value)

                    # Process actual and predicted payloads for confusion matrix
                    actual_payloads, predicted_payloads = self.process_payloads({
                        "TruePositive": true_positive,
                        "TrueNegative": true_negative,
                        "FalsePositive": false_positive,
                        "FalseNegative": false_negative,
                    })
                    
                    if len(actual_payloads) != len(predicted_payloads):
                        raise ValueError("Mismatch between actual and predicted payload lengths!")

                    # Generate confusion matrix
                    cm = metricsHandler.create_confusion_matrix(actual_payloads, predicted_payloads)
                    confusion_matrix_dict = cm.to_dict()
                    
                    # Store results in the final dictionary
                    
                    final_result[mode] = confusion_matrix_dict


                else:
                    raise ValueError(f"Function '{mode}' is not defined.")

            return {
                "status_code": 200,
                "data": final_result         
            }

        except Exception as e:
            logging.error(f"An error occurred: {e}")
            return {
                "status_code": 500,
                "detail": str(e)
            }
        
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            return {
                "status_code": 500,
                "detail": str(e)
            }

    def process_payloads(self, data):
        actual_payloads = []
        predicted_payloads = []
        categories = ["TruePositive", "TrueNegative", "FalsePositive", "FalseNegative"]

        for category in categories:
            if category in data:
                actual = [category] * len(data[category])  # Repeat category as actual
                scores = [{"score": obj.get("score", 0)} for obj in data[category]]

                # Classify based on score
                predicted = [self.classify_percentage(score["score"]) for score in scores]

                # Debug: print category details
                print(f"Category: {category}, Actual: {actual}, Predicted: {predicted}")

                actual_payloads.extend(actual)
                predicted_payloads.extend(predicted)

       

        return actual_payloads, predicted_payloads



     # Classification rules
    @staticmethod
    def classify_percentage(score):
        if 90 <= score <= 100:
            return 'TruePositive'
        elif 0 <= score <= 10:
            return 'TrueNegative'
        elif 51 <= score <= 89:
            return 'FalsePositive'
        elif 11 <= score <= 50:
            return 'FalseNegative'
        return 'Unknown'
    def load_yaml_data(self, file_path):
        """Helper function to load YAML data."""
        try:
            with open(file_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            logging.error(f"Error loading YAML data: {e}")
            raise HTTPException(status_code=500, detail="Error loading configuration data.")
 