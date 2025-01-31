import os

import os

IP_ADDRESS = "172.10.10.99"  # You can change this value as needed
MONGO_IP = "172.10.10.99"


config = { 
    "mongoip": MONGO_IP,
    "mongoport": "27017",
    "maxOtpSendAttempts": 3,
    "otpLockDurationMinutes": 2,
    "maxOtpAttempts": 3,
    "otpAttemptsDurationMinutes": 2,
    "accessTokenExpireMinutes": 1,
    "refreshTokenExpireDays": 7,
    "secretKey": "BrilliusAI",
    "userIdLength": 4,
    "userIdChunkSize": 4
  }

eval_config = {
    "LOCAL_HOST": MONGO_IP,
    "MONGO_URI": os.getenv("MONGO_URI", f"mongodb://{MONGO_IP}:27017"),
    "DB_NAME": "evaluation",
    "STATUS_COLLECTION": "EvalStatus",
    "CONFIG_COLLECTION": "EvalConfig",
    "RESULTS_COLLECTION": "EvalResults",
    "METRICS_COLLECTION": "Metrics",
    "METRIC_CONFIG":"MetricConfig",
    # Endpoint to backend server
    "SERVER_ENDPOINT": f"http://{IP_ADDRESS}:4001/accelerator/server",
    "SCORE_ENDPOINT": f"http://{IP_ADDRESS}:4001"
}
    
bench_config ={ 
    "MONGO_URI" : os.getenv("MONGO_URI", f"mongodb://{MONGO_IP}:27017"),
    "DB_NAME" : "benchmarking",
    "STATUS_COLLECTION" : "BenchStatus",
    "CONFIG_COLLECTION" : "BenchConfig",
    "RESULTS_COLLECTION" : "BenchResults",
    "METRICS_COLLECTION": "Metrics",
     # Endpoint to backend server
    "SERVER_ENDPOINT" : f"http://{IP_ADDRESS}:4001/accelerator/server",
}

finetuning_config = {
    "LOCAL_HOST": IP_ADDRESS,
    "MONGO_URI": os.getenv("MONGO_URI", f"mongodb://{IP_ADDRESS}:27017"),
    "DB_NAME": "Finetuning",
    "status_collection": "tuning_status",
    "finetune_config": "tuning_config",
    "response": "Tuning_metrics",
    "dataset_collection": "Tuning_dataset",
    # Endpoint to backend server
    "TRAINING_ENDPOINT": f"http://{IP_ADDRESS}:8007/train_model"}
   


