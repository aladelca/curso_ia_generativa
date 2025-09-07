"""
Configuración para AWS Services
"""
import os
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class AWSConfig:
    """Configuración centralizada para AWS"""
    
    def __init__(self):
        # Configuración S3
        self.S3_BUCKET = os.getenv('S3_BUCKET_NAME', 'uber-ml-models-bucket')
        self.S3_MODELS_PREFIX = os.getenv('S3_MODELS_PREFIX', 'models/')
        self.S3_DATA_PREFIX = os.getenv('S3_DATA_PREFIX', 'data/')
        
        # Configuración AWS
        self.AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
        self.AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
        self.AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
        
        # ECR Configuration
        self.ECR_REPOSITORY_TRAINING = os.getenv('ECR_REPO_TRAINING', 'uber-ml-training')
        self.ECR_REPOSITORY_PREDICTION = os.getenv('ECR_REPO_PREDICTION', 'uber-ml-prediction')
        
        # ECS Configuration
        self.ECS_CLUSTER_NAME = os.getenv('ECS_CLUSTER_NAME', 'uber-ml-cluster')
        self.ECS_TASK_DEFINITION_TRAINING = os.getenv('ECS_TASK_DEF_TRAINING', 'uber-ml-training-task')
        
        # Lambda Configuration
        self.LAMBDA_FUNCTION_NAME = os.getenv('LAMBDA_FUNCTION_NAME', 'uber-driver-prediction')
        self.LAMBDA_MEMORY = int(os.getenv('LAMBDA_MEMORY', '1024'))
        self.LAMBDA_TIMEOUT = int(os.getenv('LAMBDA_TIMEOUT', '300'))
    
    def get_s3_client(self):
        """Obtiene cliente S3"""
        try:
            if self.AWS_ACCESS_KEY_ID and self.AWS_SECRET_ACCESS_KEY:
                return boto3.client(
                    's3',
                    aws_access_key_id=self.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=self.AWS_SECRET_ACCESS_KEY,
                    region_name=self.AWS_REGION
                )
            else:
                # Usar IAM role si está en AWS
                return boto3.client('s3', region_name=self.AWS_REGION)
        except Exception as e:
            logger.error(f"Error creating S3 client: {e}")
            raise
    
    def get_ecs_client(self):
        """Obtiene cliente ECS"""
        try:
            if self.AWS_ACCESS_KEY_ID and self.AWS_SECRET_ACCESS_KEY:
                return boto3.client(
                    'ecs',
                    aws_access_key_id=self.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=self.AWS_SECRET_ACCESS_KEY,
                    region_name=self.AWS_REGION
                )
            else:
                return boto3.client('ecs', region_name=self.AWS_REGION)
        except Exception as e:
            logger.error(f"Error creating ECS client: {e}")
            raise
    
    def get_ecr_client(self):
        """Obtiene cliente ECR"""
        try:
            if self.AWS_ACCESS_KEY_ID and self.AWS_SECRET_ACCESS_KEY:
                return boto3.client(
                    'ecr',
                    aws_access_key_id=self.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=self.AWS_SECRET_ACCESS_KEY,
                    region_name=self.AWS_REGION
                )
            else:
                return boto3.client('ecr', region_name=self.AWS_REGION)
        except Exception as e:
            logger.error(f"Error creating ECR client: {e}")
            raise


# Instancia global
aws_config = AWSConfig()
