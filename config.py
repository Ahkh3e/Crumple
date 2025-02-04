import os
from pathlib import Path

class Config:
    # Base directory
    BASE_DIR = Path(__file__).resolve().parent

    # Flask and Security
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    WTF_CSRF_SECRET_KEY = os.getenv('WTF_CSRF_SECRET_KEY', 'csrf-dev-key')
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes
    
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
