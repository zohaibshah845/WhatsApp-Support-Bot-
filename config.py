# config.py - Configuration file (Render Production Version)
# Is file mein hum saari settings rakhte hain

import os
from dotenv import load_dotenv

# .env file ko load karo - Render me Environment Variables se aye ga
load_dotenv()

class Config:
    """Main configuration class - Render Production Ready"""
    
    # UltraMsg Settings (WhatsApp ke liye)
    ULTRAMSG_INSTANCE_ID = os.getenv('ULTRAMSG_INSTANCE_ID')
    ULTRAMSG_TOKEN = os.getenv('ULTRAMSG_TOKEN')
    
    # OpenAI Settings
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Database paths - RENDER DISK KE LIYE UPDATED
    # Render free tier pe data delete ho jata hai, isliye /var/data use karna zaroori hai
    RENDER_DISK_PATH = '/var/data'  # ← Render Disk ka mount path
    
    SQLITE_DB_PATH = os.path.join(RENDER_DISK_PATH, 'whatsapp_bot.db')
    CHROMA_DB_PATH = os.path.join(RENDER_DISK_PATH, 'chromadb')
    UPLOAD_FOLDER = os.path.join(RENDER_DISK_PATH, 'faqs')
    
    # Bot Settings
    BOT_NAME = "Malik's Assistant"  # Bot ka naam
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
    
    # Flask Secret Key - Render Env se aye gi
    FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'fallback-secret-key-change-this')
    
    # Language Settings
    DEFAULT_LANGUAGE = "urdu-english-mix"