# config.py - Configuration file (UltraMsg Version)
# Is file mein hum saari settings rakhte hain

import os
from dotenv import load_dotenv

# .env file ko load karo
load_dotenv()

class Config:
    """Main configuration class"""
    
    # UltraMsg Settings (WhatsApp ke liye)
    ULTRAMSG_INSTANCE_ID = os.getenv('ULTRAMSG_INSTANCE_ID')
    ULTRAMSG_TOKEN = os.getenv('ULTRAMSG_TOKEN')
    
    # OpenAI Settings
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Database paths
    SQLITE_DB_PATH = 'whatsapp_bot.db'
    CHROMA_DB_PATH = 'data/chromadb'
    UPLOAD_FOLDER = 'data/faqs'
    
    # Bot Settings
    BOT_NAME = "Malik's Assistant"  # Bot ka naam
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
    
    # Language Settings
    DEFAULT_LANGUAGE = "urdu-english-mix"