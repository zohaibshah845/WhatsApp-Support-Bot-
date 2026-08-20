from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_cors import CORS
import os
from config import Config
from database import Database
from rag_engine import RAGEngine
from whatsapp_handler import WhatsAppHandler
from werkzeug.utils import secure_filename
import json
from datetime import datetime

# Flask app initialize karo
app = Flask(_name_)
CORS(app) # Cross-Origin Resource Sharing enable karo

# Configuration load karo
app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16MB max file size
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')

# Ensure folders exist
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(Config.CHROMA_DB_PATH, exist_ok=True)

# Objects initialize karo
db = Database(Config.SQLITE_DB_PATH)
rag_engine = RAGEngine(Config.OPENAI_API_KEY, Config.CHROMA_DB_PATH)

# UltraMsg WhatsApp handler initialize karo
whatsapp_handler = WhatsAppHandler(
    instance_id=os.getenv('ULTRAMSG_INSTANCE_ID'),
    token=os.getenv('ULTRAMSG_TOKEN')
)

@app.route('/')
def home():
    """Home page - simple welcome message"""
    return jsonify({
        'status': 'success',
        'message': 'AI WhatsApp Customer Support Bot is running! 🚀',
        'bot_name': Config.BOT_NAME,
        'whatsapp_provider': 'UltraMsg',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/webhook', methods=['GET', 'POST'])
@app.route('/webhook/whatsapp', methods=['GET', 'POST'])
@app.route('/webhook/ultramsg', methods=['GET', 'POST'])
def whatsapp_webhook():
    """WhatsApp se messages receive karne ke l
