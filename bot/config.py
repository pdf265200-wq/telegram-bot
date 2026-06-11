import os
from typing import List
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

class Config:
    """Bot configuration class"""
    
    # Bot settings
    BOT_TOKEN: str = os.getenv('BOT_TOKEN', '')
    BOT_NAME: str = os.getenv('BOT_NAME', 'ProfessionalBot')
    BOT_VERSION: str = '1.0.0'
    
    # Admin settings
    ADMIN_IDS: List[int] = [
        int(id.strip()) 
        for id in os.getenv('ADMIN_IDS', '').split(',') 
        if id.strip()
    ]
    
    # Database settings
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'sqlite:///data/bot.db')
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    
    # Logging settings
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE: str = 'logs/bot.log'
    
    # Feature flags
    MAINTENANCE_MODE: bool = os.getenv('MAINTENANCE_MODE', 'false').lower() == 'true'
    ENABLE_RATE_LIMITING: bool = os.getenv('ENABLE_RATE_LIMITING', 'true').lower() == 'true'
    ENABLE_ANTI_SPAM: bool = os.getenv('ENABLE_ANTI_SPAM', 'true').lower() == 'true'
    
    # Rate limiting settings
    RATE_LIMIT_SECONDS: int = int(os.getenv('RATE_LIMIT_SECONDS', '2'))
    RATE_LIMIT_MAX_REQUESTS: int = int(os.getenv('RATE_LIMIT_MAX_REQUESTS', '5'))
    RATE_LIMIT_BURST: int = int(os.getenv('RATE_LIMIT_BURST', '10'))
    
    # File settings
    MAX_FILE_SIZE: int = int(os.getenv('MAX_FILE_SIZE', str(20 * 1024 * 1024)))  # 20MB
    ALLOWED_EXTENSIONS: set = {
        '.jpg', '.jpeg', '.png', '.gif', '.bmp',
        '.pdf', '.doc', '.docx', '.txt',
        '.mp3', '.wav', '.ogg', '.m4a',
        '.mp4', '.avi', '.mkv'
    }
    TEMP_DIR: str = 'temp'
    DATA_DIR: str = 'data'
    
    # Path settings
    BASE_DIR: Path = Path(__file__).parent.parent
    TESSERACT_PATH: str = os.getenv('TESSERACT_PATH', '/usr/bin/tesseract')
    FFMPEG_PATH: str = os.getenv('FFMPEG_PATH', '/usr/bin/ffmpeg')
    
    # Language settings
    SUPPORTED_LANGUAGES: dict = {
        'en': 'English',
        'ar': 'Arabic',
        'fr': 'French',
        'es': 'Spanish'
    }
    DEFAULT_LANGUAGE: str = 'en'
    
    # URL Shortener settings
    URL_SHORTENER_SERVICE: str = os.getenv('URL_SHORTENER_SERVICE', 'tinyurl')
    
    # QR Code settings
    QR_DEFAULT_SIZE: int = int(os.getenv('QR_DEFAULT_SIZE', '10'))
    QR_DEFAULT_BORDER: int = int(os.getenv('QR_DEFAULT_BORDER', '4'))
    
    # Cache settings
    CACHE_TIMEOUT: int = int(os.getenv('CACHE_TIMEOUT', '300'))  # 5 minutes
    CACHE_MAX_SIZE: int = int(os.getenv('CACHE_MAX_SIZE', '1000'))
    
    # Webhook settings (for production)
    WEBHOOK_URL: str = os.getenv('WEBHOOK_URL', '')
    WEBHOOK_PORT: int = int(os.getenv('PORT', '8443'))
    WEBHOOK_LISTEN: str = os.getenv('WEBHOOK_LISTEN', '0.0.0.0')
    
    # Development settings
    DEBUG: bool = os.getenv('DEBUG', 'false').lower() == 'true'
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration"""
        errors = []
        
        if not cls.BOT_TOKEN:
            errors.append("BOT_TOKEN is required")
        
        if not cls.ADMIN_IDS:
            errors.append("ADMIN_IDS is required")
        
        if errors:
            for error in errors:
                print(f"Configuration Error: {error}")
            return False
        
        return True
    
    @classmethod
    def get_allowed_languages(cls) -> List[str]:
        """Get list of allowed language codes"""
        return list(cls.SUPPORTED_LANGUAGES.keys())
    
    @classmethod
    def is_admin(cls, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id in cls.ADMIN_IDS
