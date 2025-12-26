import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configurações Base."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'default_dev_key')
    SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
    SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
    SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    # Escopos necessários: ler biblioteca e ler email/perfil
    SPOTIFY_SCOPE = 'user-library-read user-read-email' 

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

# Dicionário para seleção fácil no app factory (se usasse factory pattern)
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}