
import json
import numpy as np
import pandas as pd
import requests
import logging
from sklearn.metrics import confusion_matrix, precision_score, recall_score, f1_score
from sentence_transformers import SentenceTransformer, util
import torch



# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class ScoreCalculator:
    def __init__(self, endpoint):
        self.endpoint = endpoint   

    def get_scores_data(self, data, mode):
    # Iterate over the specified keys: TruePositive, TrueNegative, etc.
        for key in ["TruePositive", "TrueNegative", "FalsePositive", "FalseNegative"]:
            if key in data:  # Check if the key exists in the input data
                for obj in data[key]:
                    prediction = obj.get("response", "")
                    reference = obj.get("answer", "")
                    
                    # Calculate similarity scores for the given mode
                    score = self.calculate_similarity_scores(prediction, reference, mode)
                    obj["score"] = score  # Add the score to the object

        return data

            

    def calculate_similarity(self, first_sentence, second_sentence):
        try:
            inputData = {
                "first_sentence": first_sentence,
                "second_sentence": second_sentence
            }
            customer_data = {
                "userId": "TEST",
                "clientApiKey": "R3AM-52JL-INUS-E5YL",
                "deployId": "7097",
                "inputData": inputData
            }
        
            response = requests.post(f"{self.endpoint}/accelerator/server", json=customer_data)
            response.raise_for_status()  # Raise an exception for HTTP errors

            result = response.json().get("response", "")
            similarity_str = result.split(":")[1].strip()  # Extract " 92.34%"
            similarity_value = float(similarity_str.strip('%'))  # Convert to float (remove '%')

            return similarity_value
        

        except requests.exceptions.RequestException as e:
            error_detail = f"RequestException: {str(e)}"
            logging.error(f"Error in calculate_similarity: {error_detail}")
            return {
                "status_code": 500,
                "detail": error_detail
            }

        except ValueError as e:
            error_detail = f"ValueError: {str(e)}"
            logging.error(f"Error in calculate_similarity: {error_detail}")
            return {
                "status_code": 400,
                "detail": error_detail
            }

        except IndexError as e:
            error_detail = f"IndexError: {str(e)}"
            logging.error(f"Error in calculate_similarity: {error_detail}")
            return {
                "status_code": 400,
                "detail": error_detail
            }

        except json.JSONDecodeError as e:
            error_detail = f"JSONDecodeError: {str(e)}"
            logging.error(f"Error in calculate_similarity: {error_detail}")
            return {
                "status_code": 500,
                "detail": error_detail
            }

        except Exception as e:
            error_detail = f"An unexpected error occurred: {str(e)}"
            logging.error(f"Error in calculate_similarity: {error_detail}")
            return {
            "status_code": 500,
            "detail": error_detail
            }

        
    @staticmethod    
    def calculate_cosine_similarity(pred, ref):
        # Load pre-trained model
        print("111")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print("model", model)
        # Encode the sentences to get their embeddings
        embedding1 = model.encode(pred, convert_to_tensor=True)
        embedding2 = model.encode(ref, convert_to_tensor=True)
        
        # Calculate cosine similarity
        cosine_sim = util.pytorch_cos_sim(embedding1, embedding2)
        print("cosine", cosine_sim)
        # Return the cosine similarity score
        return cosine_sim.item() * 100
    

    def calculate_similarity_scores(self, prediction, reference, mode):
        scores = []
        if mode == "Cosine Similarity":
            print("cosine")
            score = self.calculate_cosine_similarity(prediction, reference)
        elif mode == "Exact Match":
            score = self.exact_match_scores(prediction, reference)
        else:                          
            score = self.calculate_similarity(prediction, reference)
                
        return score
    def exact_match_score( self, predictions, references):
    
        print("predictions", predictions)
        print("references", references)
        if not predictions or not references:
            raise ValueError("Predictions and references must not be empty.")
    
        
    # Generate binary scores: 1 for match, 0 for no match
        em_scores = [1 if pred.strip() == truth.strip() else 0 for pred, truth in zip(predictions, references)]
        print("em scores", em_scores)
        return em_scores
    def exact_match_scores(self, prediction, reference):
    # # Calculate exact matches
       exact_match = 1 if prediction == reference else 0  
       print("exact match", exact_match)      
       return exact_match


    