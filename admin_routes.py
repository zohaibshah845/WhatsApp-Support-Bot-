# admin_routes.py - Admin Panel ke liye routes
# Is file mein admin panel ke saare functions hain

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from functools import wraps

# Blueprint create karo admin routes ke liye
admin_bp = Blueprint('admin', __name__)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'docx'}

def allowed_file(filename):
    """Check karo file extension allowed hai ya nahi"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def require_admin(f):
    """Decorator - Admin authentication ke liye"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        password = request.form.get('password') or request.args.get('password')
        admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
        
        if password != admin_password:
            return jsonify({
                'success': False,
                'error': '❌ Galat password! Access denied.'
            }), 401
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/admin')
def admin_panel():
    """Admin panel ka main page"""
    return render_template('admin.html')

@admin_bp.route('/admin/dashboard')
def admin_dashboard():
    """Admin dashboard - statistics dikhao"""
    try:
        from database import Database
        db = Database()
        
        # Statistics calculate karo
        total_chats = len(db.get_chat_history(limit=1000))
        total_documents = len(db.get_all_documents())
        
        # Recent chats lo
        recent_chats = db.get_chat_history(limit=10)
        
        # Format chats
        chats_list = []
        for chat in recent_chats:
            chats_list.append({
                'id': chat[0],
                'phone': chat[1],
                'customer_message': chat[2][:100] + '...' if len(chat[2]) > 100 else chat[2],
                'bot_response': chat[3][:100] + '...' if len(chat[3]) > 100 else chat[3],
                'timestamp': chat[4]
            })
        
        return jsonify({
            'success': True,
            'statistics': {
                'total_chats': total_chats,
                'total_documents': total_documents,
                'bot_name': os.getenv('BOT_NAME', "Malik's Assistant")
            },
            'recent_chats': chats_list
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/admin/upload', methods=['POST'])
def upload_document():
    """Naya document upload karo"""
    try:
        # Admin authentication
        password = request.form.get('password', '')
        admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
        
        if password != admin_password:
            return jsonify({
                'success': False,
                'error': '❌ Galat password!'
            }), 401
        
        # File check karo
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': '❌ Koi file select nahi ki!'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': '❌ File ka naam khali hai!'
            }), 400
        
        # File extension check karo
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': '❌ Sirf PDF, TXT, ya DOCX files upload karo!'
            }), 400
        
        # Secure filename banao
        filename = secure_filename(file.filename)
        
        # Unique filename banao (timestamp ke saath)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        
        # Upload folder ka path
        upload_folder = os.getenv('UPLOAD_FOLDER', 'data/faqs')
        os.makedirs(upload_folder, exist_ok=True)
        
        # File save karo
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        
        # File size check karo
        file_size = os.path.getsize(file_path)
        if file_size > 16 * 1024 * 1024:  # 16MB
            os.remove(file_path)
            return jsonify({
                'success': False,
                'error': '❌ File bahut badi hai! Max 16MB allowed.'
            }), 400
        
        # RAG engine mein document add karo
        from rag_engine import RAGEngine
        from config import Config
        
        rag = RAGEngine(Config.OPENAI_API_KEY, Config.CHROMA_DB_PATH)
        success, message = rag.add_document(file_path)
        
        if success:
            # Database mein document save karo
            from database import Database
            db = Database()
            db.save_document(unique_filename, file_path)
            
            return jsonify({
                'success': True,
                'message': f'✅ Document "{filename}" successfully upload ho gaya!',
                'filename': unique_filename,
                'size': f'{file_size/1024:.2f} KB'
            })
        else:
            # Agar RAG mein error aaye to file delete karo
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({
                'success': False,
                'error': f'❌ Document process nahi ho saka: {message}'
            }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'❌ Upload error: {str(e)}'
        }), 500

@admin_bp.route('/admin/documents')
@require_admin
def list_documents():
    """Uploaded documents ki list dikhao"""
    try:
        from database import Database
        db = Database()
        documents = db.get_all_documents()
        
        docs_list = []
        for doc in documents:
            docs_list.append({
                'id': doc[0],
                'filename': doc[1],
                'file_path': doc[2],
                'upload_date': doc[3]
            })
        
        return jsonify({
            'success': True,
            'documents': docs_list,
            'total': len(docs_list)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/admin/chats')
@require_admin
def view_chats():
    """Chat history dekho"""
    try:
        from database import Database
        db = Database()
        
        # Query parameters
        phone = request.args.get('phone', None)
        limit = int(request.args.get('limit', 50))
        
        # Limit check karo
        if limit > 500:
            limit = 500
        
        # Chat history get karo
        chats = db.get_chat_history(phone, limit)
        
        # Format chats
        chat_list = []
        for chat in chats:
            chat_list.append({
                'id': chat[0],
                'phone': chat[1],
                'customer_message': chat[2],
                'bot_response': chat[3],
                'timestamp': chat[4]
            })
        
        return jsonify({
            'success': True,
            'chats': chat_list,
            'total': len(chat_list)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/admin/delete/document/<int:doc_id>', methods=['DELETE'])
@require_admin
def delete_document(doc_id):
    """Document delete karo"""
    try:
        from database import Database
        db = Database()
        
        # Document get karo
        documents = db.get_all_documents()
        doc_to_delete = None
        
        for doc in documents:
            if doc[0] == doc_id:
                doc_to_delete = doc
                break
        
        if not doc_to_delete:
            return jsonify({
                'success': False,
                'error': 'Document nahi mila!'
            }), 404
        
        # File system se delete karo
        file_path = doc_to_delete[2]
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Database se delete karo
        db.delete_document(doc_id)
        
        return jsonify({
            'success': True,
            'message': f'✅ Document "{doc_to_delete[1]}" delete ho gaya!'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/admin/test-bot', methods=['POST'])
def test_bot():
    """Bot ko test karo (baghair WhatsApp ke)"""
    try:
        # Admin authentication
        password = request.form.get('password') or request.json.get('password')
        admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
        
        if password != admin_password:
            return jsonify({
                'success': False,
                'error': '❌ Galat password!'
            }), 401
        
        # Test message lo
        test_message = request.form.get('message') or request.json.get('message')
        
        if not test_message:
            return jsonify({
                'success': False,
                'error': '❌ Test message khali hai!'
            }), 400
        
        # RAG engine se jawab lo
        from rag_engine import RAGEngine
        from config import Config
        
        rag = RAGEngine(Config.OPENAI_API_KEY, Config.CHROMA_DB_PATH)
        response = rag.query(test_message)
        
        return jsonify({
            'success': True,
            'test_message': test_message,
            'bot_response': response
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500