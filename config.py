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
    SPOTIFY_SCOPE = 'user-library-read user-read-email' 

    # Cookie handling
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Se True, o navegador SÓ envia o cookie se tiver cadeado HTTPS.
    # Se estivermos rodando local em HTTP simples, isso precisa ser False, senão o login falha.
    SESSION_COOKIE_SECURE = False

    # Rate limiting
    RATELIMIT_STORAGE_URI = os.getenv('REDIS_URL', 'memory://')
    RATELIMIT_DEFAULT = "200 per day; 50 per hour"
    RATELIMIT_HEADERS_ENABLED = True

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True 
    SESSION_REFRESH_EACH_REQUEST = True

# Dicionário para seleção fácil no app factory (se usasse factory pattern)
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}