import os
from pathlib import Path

class Config:
    # Base directory
    BASE_DIR = Path(__file__).resolve().parent

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    
    # Database - Using internal Docker network hostname
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://crumple:crumple@postgres:5432/crumple')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # RabbitMQ - Using internal Docker network hostname
    RABBITMQ_URL = os.getenv('RABBITMQ_URL', 'amqp://guest:guest@rabbitmq:5672')
    
    # Application settings
    PER_PAGE = int(os.getenv('PER_PAGE', 20))
    
    # Network settings
    SERVER_NAME = os.getenv('SERVER_NAME')  # Allow custom server name if needed
    PREFERRED_URL_SCHEME = os.getenv('PREFERRED_URL_SCHEME', 'http')
    
class DevelopmentConfig(Config):
    DEBUG = True
    
class ProductionConfig(Config):
    DEBUG = False
    
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://crumple:crumple@postgres:5432/crumple_test'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
