import logging
import numpy as np
import nltk
from typing import List, Optional, Dict, Tuple
from collections import Counter
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from nltk.translate.meteor_score import meteor_score
from nltk.tokenize import word_tokenize
import pandas as pd
from sklearn.metrics import matthews_corrcoef, f1_score, precision_score
from sentence_transformers import SentenceTransformer, util
from sklearn.metrics import confusion_matrix, precision_score, recall_score, f1_score
from bert_score import score as bert_score
from rouge_score import rouge_scorer
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForCausalLM

# Download the 'punkt' tokenizer
nltk.download('punkt')
nltk.download('punkt_tab')


nltk.download('wordnet')

class Metrics:
    def __init__(self):
        self.tokenizer = None
        self.model = None

    @staticmethod
    def create_confusion_matrix(actual_payloads, predicted_payloads):
        # Flatten the lists
        #y_true = [label for sublist in actual_payloads for label in sublist]
        #y_pred = [label for sublist in predicted_payloads for label in sublist]
        y_true = actual_payloads
        y_pred = predicted_payloads
        print("confusion matrix....")
        # Classes (Ensure these match your actual categories)
        labels = ['TruePositive', 'TrueNegative', 'FalsePositive', 'FalseNegative']
        print("labels")
        print("y_true", y_true)
        print("y_pred", y_pred)
        # Compute confusion matrix
        cm = confusion_matrix(y_true, y_pred, labels=labels)
        print("cm...", cm)
        # Calculate precision, recall, F1-score for each class
        precision = precision_score(y_true, y_pred, labels=labels, average=None, zero_division=0)
        recall = recall_score(y_true, y_pred, labels=labels, average=None, zero_division=0)
        f1 = f1_score(y_true, y_pred, labels=labels, average=None, zero_division=0)
        print("cm", precision,recall,f1)
        # Create DataFrame for better readability
        df = pd.DataFrame(cm, index=labels, columns=labels)
        df['Precision'] = precision
        df['Recall'] = recall
        df['F1-Score'] = f1

        return df

    
    @staticmethod
    def calculate_recall(actual_payloads, predicted_payloads):
        # Flatten the lists
        y_true = [label for sublist in actual_payloads for label in sublist]
        y_pred = [label for sublist in predicted_payloads for label in sublist]

        # Classes
        labels = ['Payload1', 'Payload2', 'Payload3', 'Payload4']

        # Calculate recall for each class
        recall = recall_score(y_true, y_pred, labels=labels, average=None)

        # Create DataFrame for recall
        df_recall = pd.DataFrame(recall, index=labels, columns=['Recall'])

        return df_recall
    


    @staticmethod
    def calculate_f1_score(actual_payloads, predicted_payloads):
        # Flatten the lists
        y_true = [label for sublist in actual_payloads for label in sublist]
        y_pred = [label for sublist in predicted_payloads for label in sublist]

        # Classes
        labels = ['Payload1', 'Payload2', 'Payload3', 'Payload4']

        # Calculate f1-score for each class
        f1 = f1_score(y_true, y_pred, labels=labels, average=None)

        # Create DataFrame for f1-score
        df_f1 = pd.DataFrame(f1, index=labels, columns=['f1-score'])

        return df_f1



    @staticmethod
    def calculate_precision(actual_payloads, predicted_payloads):
        # Flatten the lists
        y_true = [label for sublist in actual_payloads for label in sublist]
        y_pred = [label for sublist in predicted_payloads for label in sublist]

        # Classes
        labels = ['Payload1', 'Payload2', 'Payload3', 'Payload4']

        # Calculate precision for each class
        precision = precision_score(y_true, y_pred, labels=labels, average=None)
        
        # Create DataFrame for precision
        df_precision = pd.DataFrame(precision, index=labels, columns=['Precision'])

        return df_precision
    
    @staticmethod
    def calculate_accuracy(confusion_matrix):
        total_correct = sum(confusion_matrix.at[label, label] for label in confusion_matrix.index)
        total_samples = confusion_matrix.values.sum()
        accuracy = total_correct / total_samples
        return accuracy
    


    
    @staticmethod
    def bert_score_evaluation(predictions, references):
        
        P, R, F1 = bert_score(predictions, references, lang="en", rescale_with_baseline=True)
        
        return P.mean().item(), R.mean().item(), F1.mean().item()

    @staticmethod
    def rouge_score_evaluation(predictions, references):
        scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
        scores = [scorer.score(pred, ref) for pred, ref in zip(predictions, references)]
        print("scores", scores)
        rouge1_f1 = sum(score['rouge1'].fmeasure for score in scores) / len(scores)
        print("1", rouge1_f1)
        rouge2_f1 = sum(score['rouge2'].fmeasure for score in scores) / len(scores)
        print("2", rouge2_f1)
        rougel_f1 = sum(score['rougeL'].fmeasure for score in scores) / len(scores)
        print("3", rougel_f1)
        return rouge1_f1, rouge2_f1, rougel_f1

    def calculate_mrr(predictions, references):
        
        if not predictions or not references:
            print("not predic ")
            return 0.0
        
        reciprocal_ranks = []
        for pred_list, ref in zip(predictions, references):
            try:
                print("pred_list", pred_list)
                print("reference", ref)
                print("In looping")
                rank = pred_list.index(ref) + 1
                reciprocal_ranks.append(1.0 / rank)
            except Exception as e:
                print(f"Error processing {pred_list} and {ref}: {e}")
                reciprocal_ranks.append(0.0)
        return np.mean(reciprocal_ranks) if reciprocal_ranks else 0.0

    def calculate_rer(predictions: List[str], references: List[str], 
                 irrelevance_threshold: float = 0.3) -> float:
        """
        Calculate Relevance Error Rate (RER).
        
        Args:
            predictions: List of predicted responses
            references: List of reference responses
            irrelevance_threshold: Similarity threshold below which a response is considered irrelevant
        
        Returns:
            float: RER score between 0 and 1
        """
        def calculate_similarity(text1: str, text2: str) -> float:
            # Simple word overlap similarity - can be replaced with more sophisticated methods
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            
            if not words1 or not words2:
                return 0.0
                
            overlap = len(words1.intersection(words2))
            union = len(words1.union(words2))
            return overlap / union if union > 0 else 0.0
        
        irrelevant_count = 0
        total_predictions = len(predictions)
        
        for pred, ref in zip(predictions, references):
            similarity = calculate_similarity(pred, ref)
            if similarity < irrelevance_threshold:
                irrelevant_count += 1
        print("9999999", irrelevant_count / total_predictions if total_predictions > 0 else 1.0)
        return irrelevant_count / total_predictions if total_predictions > 0 else 1.0

    def calculate_tsr(predictions: List[str], references: List[str], 
                 required_elements: Optional[List[str]] = None) -> float:
        """
        Calculate Task Success Rate (TSR).
        
        Args:
            predictions: List of predicted responses
            references: List of reference responses
            required_elements: List of required elements/keywords that must be present
                            for a response to be considered successful
        
        Returns:
            float: TSR score between 0 and 1
        """
        if not required_elements:
            # If no specific elements are provided, check for exact match
            successful_tasks = sum(1 for pred, ref in zip(predictions, references) 
                                if pred.strip().lower() == ref.strip().lower())
        else:
            successful_tasks = 0
            for pred in predictions:
                pred_lower = pred.lower()
                # Check if all required elements are present in the prediction
                if all(element.lower() in pred_lower for element in required_elements):
                    successful_tasks += 1
        print("9999999", successful_tasks / len(predictions) if predictions else 0.0)
        return successful_tasks / len(predictions) if predictions else 0.0
    
    
        
    def calculate_bleu(self, predictions: List[str], references: List[str]) -> Dict[str, float]:
        """
        Calculate BLEU scores for 1-4 grams.
        """
        smooth = SmoothingFunction().method1
        bleu_scores = {f'bleu-{i}': 0.0 for i in range(1, 5)}
        
        for pred, ref in zip(predictions, references):
            # Tokenize
            pred_tokens = word_tokenize(pred.lower())
            ref_tokens = [word_tokenize(ref.lower())]
            
            # Calculate BLEU-1 to BLEU-4
            for n in range(1, 5):
                weights = tuple([1./n] * n + [0.] * (4-n))
                score = sentence_bleu(ref_tokens, pred_tokens, 
                                   weights=weights,
                                   smoothing_function=smooth)
                bleu_scores[f'bleu-{n}'] += score
        
        # Average scores
        for key in bleu_scores:
            bleu_scores[key] /= len(predictions) if predictions else 1
        print("9999999", bleu_scores)    
        return bleu_scores

    def calculate_meteor(self, predictions: List[str], references: List[str]) -> float:
        """
        Calculate METEOR score.
        """
        meteor_scores = []
        for pred, ref in zip(predictions, references):
            score = meteor_score([word_tokenize(ref)], word_tokenize(pred))
            meteor_scores.append(score)
        print("9999999", np.mean(meteor_scores) if meteor_scores else 0.0)
        return np.mean(meteor_scores) if meteor_scores else 0.0

    def calculate_mcc(self, predictions: List[str], references: List[str], 
                     labels: Optional[List[str]] = None) -> float:
        """
        Calculate Matthews Correlation Coefficient.
        """
        if not labels:
            # Get unique labels from both predictions and references
            labels = list(set(predictions + references))
        
        # Convert string labels to integers
        label_to_id = {label: idx for idx, label in enumerate(labels)}
        
        # Convert predictions and references to integer labels
        y_true = [label_to_id[ref] for ref in references]
        y_pred = [label_to_id[pred] for pred in predictions]
        print("9999999", matthews_corrcoef(y_true, y_pred))
        return matthews_corrcoef(y_true, y_pred)

    def calculate_multi_f1(self, predictions: List[str], references: List[str],
                          labels: Optional[List[str]] = None) -> Dict[str, float]:
        """
        Calculate Multi-Class F1 Score.
        """
        if not labels:
            # Get unique labels from both predictions and references
            labels = list(set(predictions + references))
        
        # Convert string labels to integers
        label_to_id = {label: idx for idx, label in enumerate(labels)}
        
        # Convert predictions and references to integer labels
        y_true = [label_to_id[ref] for ref in references]
        y_pred = [label_to_id[pred] for pred in predictions]
        
        # Calculate F1 scores
        f1_micro = f1_score(y_true, y_pred, average='micro')
        f1_macro = f1_score(y_true, y_pred, average='macro')
        f1_weighted = f1_score(y_true, y_pred, average='weighted')
        print("9999999", f1_macro, f1_micro, f1_weighted)
        return {
            'f1_micro': f1_micro,
            'f1_macro': f1_macro,
            'f1_weighted': f1_weighted
        }

    def calculate_perplexity(self, predictions: List[float]) -> float:
        """
        Calculate perplexity using cross-entropy loss.
        
        Args:
            actual_values: List of actual/reference texts (not used in this implementation)
            predicted_values: List of predicted probabilities
            
        Returns:
            float: Perplexity score
        """
        try:
            # Ensure predicted values are valid probabilities (between 0 and 1)
            cleaned_predictions = []
            for p in predictions:
                try:
                    p_float = float(p)
                    # Clip probabilities to avoid log(0)
                    p_float = np.clip(p_float, 1e-10, 1.0)
                    cleaned_predictions.append(p_float)
                except (ValueError, TypeError):
                    continue
            
            if not cleaned_predictions:
                raise ValueError("No valid prediction probabilities found")
            
            # Calculate cross-entropy loss
            loss = -np.mean([np.log(p) for p in cleaned_predictions])
            
            # Calculate perplexity
            perplexity = np.exp(loss)
            
            # Handle potential numerical overflow
            if np.isinf(perplexity) or np.isnan(perplexity):
                return float('inf')
            print("9999999", float(perplexity))
            return float(perplexity)
            
        except Exception as e:
            logging.error(f"Error calculating perplexity: {e}")
            return float('inf')

    def dcg_at_k(relevance_scores, k):
        """Calculate the Discounted Cumulative Gain (DCG) at rank k."""
        relevance_scores = relevance_scores[:k]
        return np.sum([rel / np.log2(i + 2) for i, rel in enumerate(relevance_scores)])

    def idcg_at_k(relevance_scores, k):
        """Calculate the Ideal Discounted Cumulative Gain (IDCG) at rank k."""
        sorted_relevance_scores = sorted(relevance_scores, reverse=True)
        return Metrics.dcg_at_k(sorted_relevance_scores, k)

    def ndcg_at_k(predictions, references, k=10):
        """Calculate the Normalized Discounted Cumulative Gain (NDCG) at rank k."""
        # Compute DCG for each prediction
        dcg_scores = []
        for pred_list, ref_list in zip(predictions, references):
            relevance_scores = [1 if ref in pred_list else 0 for ref in ref_list]
            dcg_score = Metrics.dcg_at_k(relevance_scores, k)
            idcg_score = Metrics.idcg_at_k(relevance_scores, k)
            if idcg_score == 0:
                ndcg_score = 0
            else:
                ndcg_score = dcg_score / idcg_score
            dcg_scores.append(ndcg_score)

        return np.mean(dcg_scores)  # Mean NDCG across all queries
    def average_precision_at_k(predictions, references, k):

        relevant_count = 0
        precision_at_k = 0
        
        for i, pred in enumerate(predictions[:k]):
            if pred in references:
                relevant_count += 1
                precision_at_k += relevant_count / (i + 1)
        
        # If there are no relevant documents, return 0
        return precision_at_k / min(len(references), k) if references else 0

    def mean_average_precision(predictions, references, k=3):
        ap_scores = []
        
        for pred_list, ref_list in zip(predictions, references):
            ap = Metrics.average_precision_at_k(pred_list, ref_list, k)
            ap_scores.append(ap)
        
        return np.mean(ap_scores)  # Return the mean of all Average Precision scores
            
    def calculate_mrr(predictions, references):
    
        if not predictions or not references or len(predictions) != len(references):
            raise ValueError("Predictions and references must be non-empty and have the same length.")
        
        reciprocal_ranks = []
        
        for pred, ref in zip(predictions, references):
            # Find the rank of the first relevant item
            rank = next((i + 1 for i, p in enumerate(pred) if p in ref), None)
            
            # If no relevant item is found, the rank contribution is 0
            reciprocal_ranks.append(1 / rank if rank else 0)
        
        # Calculate MRR as the mean of reciprocal ranks
        mrr = sum(reciprocal_ranks) / len(reciprocal_ranks)
        return mrr
    
    def exact_match_score(predictions, ground_truths):
    
        if len(predictions) != len(ground_truths):
            raise ValueError("Predictions and ground truths must have the same length.")

        # Count the number of exact matches
        exact_matches = sum(1 for pred, truth in zip(predictions, ground_truths) if pred.strip() == truth.strip())
        print("em", exact_matches)
        print("len", len(ground_truths))
        # Calculate EM score as a percentage
        return (exact_matches / len(ground_truths)) * 100
                                                                                                                                        