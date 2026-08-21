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

app = Flask(__name__)
CORS(app)

# Increase upload size to 16MB
app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')

os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(Config.CHROMA_DB_PATH, exist_ok=True)

db = Database(Config.SQLITE_DB_PATH)
rag_engine = RAGEngine(Config.OPENAI_API_KEY, Config.CHROMA_DB_PATH)

# ✅ FIXED: Only WATI - no UltraMsg
whatsapp_handler = WhatsAppHandler()

@app.route('/')
def home():
    return jsonify({
        'status': 'success',
        'message': 'AI WhatsApp Customer Support Bot is running! 🚀',
        'bot_name': Config.BOT_NAME,
        'whatsapp_provider': 'WATI',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/wati-webhook', methods=['POST'])
def wati_webhook():
    try:
        message_data = request.get_json()
        
        # Debug print
        print("=" * 60)
        print("📥 FULL WATI WEBHOOK DATA:")
        print(json.dumps(message_data, indent=2))
        print("=" * 60)

        # WATI sends different formats - handle all
        from_number = message_data.get('waId', '') or message_data.get('from', '')
        msg_type = message_data.get('type', 'text')
        
        # Handle text in different formats
        text_data = message_data.get('text', '')
        if isinstance(text_data, dict):
            message_body = text_data.get('body', '')
        elif isinstance(text_data, str):
            message_body = text_data
        else:
            message_body = ''
        
        # Some WATI versions send 'message' instead of 'text'
        if not message_body:
            message_body = message_data.get('message', '')
        
        message_body = message_body.strip()

        print(f"📨 From: {from_number}")
        print(f"📝 Message: {message_body}")
        print(f"📋 Type: {msg_type}")

        # Skip if not text or empty
        if not message_body or not from_number:
            print(f"⚠️ Skipping: type={msg_type}, body={message_body}")
            return jsonify({'success': True}), 200

        # Skip group messages
        if '@g.us' in from_number or '@newsletter' in from_number or '@broadcast' in from_number:
            print("⚠️ Group message - skipping")
            return jsonify({'success': True}), 200

        # Clean phone number
        phone_number = from_number.replace('@c.us', '').replace('+', '')
        print(f"📱 Phone: {phone_number}")

        # Get bot response
        bot_response = rag_engine.query(message_body)
        print(f"🤖 Bot Response: {bot_response[:100]}...")

        # Save to database
        db.save_chat(phone_number, message_body, bot_response)

        # Send via WATI
        success, msg_id = whatsapp_handler.send_message(phone_number, bot_response)

        if success:
            print(f"✅ WATI Reply sent: {msg_id}")
        else:
            print(f"❌ WATI Send failed: {msg_id}")

        return jsonify({'success': True}), 200

    except Exception as e:
        print(f"❌ WATI CRASH: {e}")
        return jsonify({'success': False}), 500

# Keep this for backward compatibility
@app.route('/webhook/ultramsg', methods=['GET', 'POST'])
def ultramsg_webhook():
    return jsonify({
        'success': False, 
        'message': 'UltraMsg is not configured. Using WATI only.'
    }), 200

# Health check endpoint
@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'wati_token': 'configured' if os.getenv('WATI_API_TOKEN') else 'missing',
        'openai_token': 'configured' if os.getenv('OPENAI_API_KEY') else 'missing',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
