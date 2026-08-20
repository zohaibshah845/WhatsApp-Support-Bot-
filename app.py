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
app = Flask(__name__)
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
@app.route('/webhook', methods=['GET', 'POST'])
@app.route('/webhook/whatsapp', methods=['GET', 'POST'])
@app.route('/webhook/ultramsg', methods=['GET', 'POST'])
def whatsapp_webhook():
    """WhatsApp se messages receive karne ke liye webhook (UltraMsg)"""
    try:
        # UltraMsg webhook data
        message_data = request.get_json()
        
        print("=" * 50)
        print("ULTRAMSG DATA:", message_data)
        print("=" * 50)
        
        # UltraMsg ka nested data nikalo
        data = message_data.get('data', {})
        from_number = data.get('from', '')
        message_body = data.get('body', '')
        
        # Groups/Newsletter ignore karo
        if '@g.us' in from_number or '@newsletter' in from_number or '@broadcast' in from_number:
            return jsonify({'success': True}), 200
        
        # Khali message check
        if not message_body or not from_number:
            print(f"❌ EMPTY: from={from_number}, body={message_body}")
            return jsonify({'success': False}), 400
        
        # Sirf number nikalo
        phone_number = from_number.split('@')[0]
        
        print(f"📨 Message from {phone_number}: {message_body}")
        
        # Bot ka jawab banao
        bot_response = rag_engine.query(message_body)
        
        # DB me save karo
        db.save_chat(phone_number, message_body, bot_response)
        
        # Reply bhejo
        success, msg_id = whatsapp_handler.send_message(phone_number, bot_response)
        
        if success:
            print(f"✅ Reply sent: {msg_id}")
        else:
            print(f"❌ Send failed: {msg_id}")
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        print(f"❌ CRASH: {e}")
        return jsonify({'success': False}), 500
