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
        
   

@app.route('/admin')
def admin_panel():
    """Admin panel - documents upload karne ke liye"""
    return render_template('admin.html')

@app.route('/admin/upload', methods=['POST'])
def upload_document():
    """Naya document upload karo"""
    try:
        # Password check karo
        password = request.form.get('password', '')
        if password!= Config.ADMIN_PASSWORD:
            return jsonify({'error': 'Galat password!'}), 401
        
        # File check karo
        if 'file' not in request.files:
            return jsonify({'error': 'Koi file upload nahi hui!'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'File ka naam khali hai!'}), 400
        
        # File type check karo
        allowed_extensions = {'pdf', 'txt', 'docx'}
        file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        
        if file_extension not in allowed_extensions:
            return jsonify({'error': 'Sirf PDF, TXT, ya DOCX files upload karo!'}), 400
        
        # Unique filename banao
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = secure_filename(file.filename)
        unique_filename = f"{timestamp}_{filename}"
        
        # File save karo
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        # RAG engine mein document add karo
        success, message = rag_engine.add_document(file_path)
        
        if success:
            # Database mein document record karo
            db.save_document(unique_filename, file_path)
            return jsonify({
                'success': True,
                'message': f'Document "{filename}" successfully upload ho gaya! ✅'
            })
        else:
            # Agar RAG mein error aaye to file delete karo
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({'error': message}), 500
        
    except Exception as e:
        return jsonify({'error': f'Upload error: {str(e)}'}), 500

@app.route('/admin/chats')
def view_chats():
    """Chat history dekho (admin ke liye)"""
    try:
        # Simple authentication
        password = request.args.get('password', '')
        if password!= Config.ADMIN_PASSWORD:
            return jsonify({'error': 'Galat password!'}), 401
        
        # Chat history get karo
        chats = db.get_chat_history(limit=100)
        
        return jsonify({
            'success': True,
            'chats': chats,
            'total': len(chats)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/stats')
def view_stats():
    """Bot statistics dekho (admin ke liye)"""
    try:
        # Simple authentication
        password = request.args.get('password', '')
        if password!= Config.ADMIN_PASSWORD:
            return jsonify({'error': 'Galat password!'}), 401
        
        # Statistics get karo
        stats = db.get_chat_statistics()
        
        # UltraMsg connection status
        connection = whatsapp_handler.get_connection_status()
        
        return jsonify({
            'success': True,
            'statistics': stats,
            'whatsapp_connection': connection
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/test-bot', methods=['POST'])
def test_bot():
    """Bot ko test karo (baghair WhatsApp ke)"""
    try:
        # Password check karo
        password = request.form.get('password') or request.json.get('password')
        if password!= Config.ADMIN_PASSWORD:
            return jsonify({'error': 'Galat password!'}), 401
        
        # Test message lo
        test_message = request.form.get('message') or request.json.get('message')
        
        if not test_message:
            return jsonify({'error': 'Test message khali hai!'}), 400
        
        # RAG engine se jawab lo
        bot_response = rag_engine.query(test_message)
        
        return jsonify({
            'success': True,
            'test_message': test_message,
            'bot_response': bot_response
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'bot_name': Config.BOT_NAME,
        'database': 'connected',
        'rag_engine': 'ready',
        'whatsapp': whatsapp_handler.is_connected,
        'timestamp': datetime.now().isoformat()
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Page nahi mila!'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error!'}), 500

# Flask app run karo - UPDATED FOR RENDER
if __name__ == '__main__':
    print("=" * 50)
    print("🤖 WhatsApp Support Bot Starting...")
    print(f"📱 Provider: UltraMsg")
    print(f"🤖 Bot Name: {Config.BOT_NAME}")
    print(f"💾 Database: {Config.SQLITE_DB_PATH}")
    print(f"📁 Upload Folder: {Config.UPLOAD_FOLDER}")
    print("=" * 50)
    
    # Production server - Render ke liye updated
    port = int(os.environ.get('PORT', 5000))
    app.run(
        host='0.0.0.0', # ← 127.0.0.1 se 0.0.0.0 kar diya
        port=port, # ← Render ka PORT env use karo
        debug=False # ← Production me False karo
    )