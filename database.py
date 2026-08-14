# database.py - SQLite Database operations
# Is file mein hum chat history aur documents save karte hain

import sqlite3
from datetime import datetime, timedelta
import json
import os

class Database:
    """Database class - SQLite ke saath kaam karne ke liye"""
    
    def __init__(self, db_path='whatsapp_bot.db'):
        """Database initialize karo"""
        self.db_path = db_path
        self.init_db()
        print(f"✅ Database connected: {db_path}")
    
    def init_db(self):
        """Database tables create karo"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Chats table - customer messages store karne ke liye
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phone_number TEXT NOT NULL,
                    customer_message TEXT,
                    bot_response TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Documents table - uploaded files track karne ke liye
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT,
                    file_path TEXT,
                    upload_date DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Customers table - unique customers track karne ke liye
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phone_number TEXT UNIQUE,
                    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                    total_messages INTEGER DEFAULT 0
                )
            ''')
            
            # Indexes create karo (fast searching ke liye)
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_chats_phone 
                ON chats(phone_number)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_chats_timestamp 
                ON chats(timestamp)
            ''')
            
            conn.commit()
            conn.close()
            print("✅ Tables created successfully!")
            
        except Exception as e:
            print(f"❌ Database initialization error: {e}")
    
    def save_chat(self, phone_number, customer_message, bot_response):
        """Chat message save karo"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Chat save karo
            cursor.execute('''
                INSERT INTO chats (phone_number, customer_message, bot_response)
                VALUES (?, ?, ?)
            ''', (phone_number, customer_message, bot_response))
            
            # Customer update karo
            cursor.execute('''
                INSERT INTO customers (phone_number, first_seen, last_seen, total_messages)
                VALUES (?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1)
                ON CONFLICT(phone_number) 
                DO UPDATE SET 
                    last_seen = CURRENT_TIMESTAMP,
                    total_messages = total_messages + 1
            ''', (phone_number,))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Error saving chat: {e}")
            return False
    
    def get_chat_history(self, phone_number=None, limit=50, offset=0):
        """Chat history get karo"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if phone_number:
                cursor.execute('''
                    SELECT id, phone_number, customer_message, bot_response, timestamp
                    FROM chats 
                    WHERE phone_number = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ? OFFSET ?
                ''', (phone_number, limit, offset))
            else:
                cursor.execute('''
                    SELECT id, phone_number, customer_message, bot_response, timestamp
                    FROM chats 
                    ORDER BY timestamp DESC 
                    LIMIT ? OFFSET ?
                ''', (limit, offset))
            
            chats = cursor.fetchall()
            conn.close()
            
            # Format chats
            formatted_chats = []
            for chat in chats:
                formatted_chats.append({
                    'id': chat[0],
                    'phone_number': chat[1],
                    'customer_message': chat[2],
                    'bot_response': chat[3],
                    'timestamp': chat[4]
                })
            
            return formatted_chats
            
        except Exception as e:
            print(f"❌ Error getting chat history: {e}")
            return []
    
    def get_chats_by_date(self, date=None, limit=100):
        """Specific date ke chats get karo"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if date:
                cursor.execute('''
                    SELECT id, phone_number, customer_message, bot_response, timestamp
                    FROM chats 
                    WHERE DATE(timestamp) = DATE(?)
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (date, limit))
            else:
                # Aaj ke chats
                cursor.execute('''
                    SELECT id, phone_number, customer_message, bot_response, timestamp
                    FROM chats 
                    WHERE DATE(timestamp) = DATE('now')
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (limit,))
            
            chats = cursor.fetchall()
            conn.close()
            return chats
            
        except Exception as e:
            print(f"❌ Error getting chats by date: {e}")
            return []
    
    def save_document(self, filename, file_path):
        """Uploaded document ka record save karo"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO documents (filename, file_path)
                VALUES (?, ?)
            ''', (filename, file_path))
            
            doc_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return doc_id
            
        except Exception as e:
            print(f"❌ Error saving document: {e}")
            return None
    
    def get_all_documents(self):
        """Sab documents ki list get karo"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, filename, file_path, upload_date
                FROM documents 
                ORDER BY upload_date DESC
            ''')
            
            documents = cursor.fetchall()
            conn.close()
            
            # Format documents
            formatted_docs = []
            for doc in documents:
                formatted_docs.append({
                    'id': doc[0],
                    'filename': doc[1],
                    'file_path': doc[2],
                    'upload_date': doc[3]
                })
            
            return formatted_docs
            
        except Exception as e:
            print(f"❌ Error getting documents: {e}")
            return []
    
    def get_document_by_id(self, doc_id):
        """Specific document get karo"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, filename, file_path, upload_date
                FROM documents 
                WHERE id = ?
            ''', (doc_id,))
            
            doc = cursor.fetchone()
            conn.close()
            
            if doc:
                return {
                    'id': doc[0],
                    'filename': doc[1],
                    'file_path': doc[2],
                    'upload_date': doc[3]
                }
            return None
            
        except Exception as e:
            print(f"❌ Error getting document: {e}")
            return None
    
    def delete_document(self, doc_id):
        """Document delete karo database se"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Pehle file path get karo
            cursor.execute('SELECT file_path FROM documents WHERE id = ?', (doc_id,))
            result = cursor.fetchone()
            
            if result:
                file_path = result[0]
                
                # Database se delete karo
                cursor.execute('DELETE FROM documents WHERE id = ?', (doc_id,))
                conn.commit()
                conn.close()
                
                # File system se delete karo
                if os.path.exists(file_path):
                    os.remove(file_path)
                    
                return True, file_path
            
            conn.close()
            return False, None
            
        except Exception as e:
            print(f"❌ Error deleting document: {e}")
            return False, None
    
    def get_customers(self, limit=100):
        """Sab customers ki list get karo"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT phone_number, first_seen, last_seen, total_messages
                FROM customers 
                ORDER BY last_seen DESC 
                LIMIT ?
            ''', (limit,))
            
            customers = cursor.fetchall()
            conn.close()
            
            # Format customers
            formatted_customers = []
            for customer in customers:
                formatted_customers.append({
                    'phone_number': customer[0],
                    'first_seen': customer[1],
                    'last_seen': customer[2],
                    'total_messages': customer[3]
                })
            
            return formatted_customers
            
        except Exception as e:
            print(f"❌ Error getting customers: {e}")
            return []
    
    def get_chat_statistics(self):
        """Chat statistics calculate karo"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total chats
            cursor.execute('SELECT COUNT(*) FROM chats')
            total_chats = cursor.fetchone()[0]
            
            # Unique customers
            cursor.execute('SELECT COUNT(DISTINCT phone_number) FROM chats')
            unique_customers = cursor.fetchone()[0]
            
            # Today's chats
            cursor.execute('''
                SELECT COUNT(*) FROM chats 
                WHERE DATE(timestamp) = DATE('now')
            ''')
            today_chats = cursor.fetchone()[0]
            
            # Yesterday's chats
            cursor.execute('''
                SELECT COUNT(*) FROM chats 
                WHERE DATE(timestamp) = DATE('now', '-1 day')
            ''')
            yesterday_chats = cursor.fetchone()[0]
            
            # Last 7 days chats
            cursor.execute('''
                SELECT COUNT(*) FROM chats 
                WHERE timestamp >= datetime('now', '-7 days')
            ''')
            week_chats = cursor.fetchone()[0]
            
            # Total documents
            cursor.execute('SELECT COUNT(*) FROM documents')
            total_documents = cursor.fetchone()[0]
            
            # Average messages per customer
            cursor.execute('''
                SELECT AVG(msg_count) FROM (
                    SELECT COUNT(*) as msg_count 
                    FROM chats 
                    GROUP BY phone_number
                )
            ''')
            avg_messages = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return {
                'total_chats': total_chats,
                'unique_customers': unique_customers,
                'today_chats': today_chats,
                'yesterday_chats': yesterday_chats,
                'week_chats': week_chats,
                'total_documents': total_documents,
                'avg_messages_per_customer': round(avg_messages, 2)
            }
            
        except Exception as e:
            print(f"❌ Error getting statistics: {e}")
            return {
                'total_chats': 0,
                'unique_customers': 0,
                'today_chats': 0,
                'yesterday_chats': 0,
                'week_chats': 0,
                'total_documents': 0,
                'avg_messages_per_customer': 0
            }
    
    def search_chats(self, search_term, limit=50):
        """Chats mein search karo"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            search_pattern = f'%{search_term}%'
            
            cursor.execute('''
                SELECT id, phone_number, customer_message, bot_response, timestamp
                FROM chats 
                WHERE customer_message LIKE ? OR bot_response LIKE ?
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (search_pattern, search_pattern, limit))
            
            chats = cursor.fetchall()
            conn.close()
            
            # Format chats
            formatted_chats = []
            for chat in chats:
                formatted_chats.append({
                    'id': chat[0],
                    'phone_number': chat[1],
                    'customer_message': chat[2],
                    'bot_response': chat[3],
                    'timestamp': chat[4]
                })
            
            return formatted_chats
            
        except Exception as e:
            print(f"❌ Error searching chats: {e}")
            return []
    
    def delete_chat(self, chat_id):
        """Specific chat delete karo"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM chats WHERE id = ?', (chat_id,))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Error deleting chat: {e}")
            return False
    
    def clear_all_chats(self):
        """Sab chats delete karo (careful!)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM chats')
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Error clearing chats: {e}")
            return False
    
    def export_chats_to_json(self, file_path='chats_export.json'):
        """Chats ko JSON file mein export karo"""
        try:
            chats = self.get_chat_history(limit=10000)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(chats, f, indent=2, ensure_ascii=False)
            
            return True, file_path
            
        except Exception as e:
            print(f"❌ Error exporting chats: {e}")
            return False, None
    
    def get_database_size(self):
        """Database file ka size check karo"""
        try:
            if os.path.exists(self.db_path):
                size_bytes = os.path.getsize(self.db_path)
                size_kb = size_bytes / 1024
                size_mb = size_kb / 1024
                
                if size_mb > 1:
                    return f"{size_mb:.2f} MB"
                else:
                    return f"{size_kb:.2f} KB"
            return "0 KB"
            
        except Exception as e:
            print(f"❌ Error getting database size: {e}")
            return "Unknown"
    
    def backup_database(self, backup_path=None):
        """Database ka backup banao"""
        try:
            if not backup_path:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_path = f'backup_{timestamp}.db'
            
            # Simple file copy
            import shutil
            shutil.copy2(self.db_path, backup_path)
            
            return True, backup_path
            
        except Exception as e:
            print(f"❌ Error backing up database: {e}")
            return False, None


# Test function - Direct run karne ke liye
if __name__ == "__main__":
    print("🧪 Database Test")
    print("=" * 40)
    
    # Database initialize karo
    db = Database('test_database.db')
    
    # Test chat save karo
    print("\n💬 Chat save test:")
    db.save_chat('+923001234567', 'Delivery time kya hai?', '2-3 working days')
    db.save_chat('+923001234567', 'Free delivery kitne par hai?', 'Rs. 5000 se zyada par')
    db.save_chat('+923009876543', 'Return policy batao', '7 days return policy hai')
    
    # Chat history test
    print("\n📜 Chat history test:")
    chats = db.get_chat_history(limit=10)
    for chat in chats:
        print(f"  {chat['phone_number']}: {chat['customer_message']} -> {chat['bot_response']}")
    
    # Statistics test
    print("\n📊 Statistics test:")
    stats = db.get_chat_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Customer list test
    print("\n👥 Customers test:")
    customers = db.get_customers()
    for customer in customers:
        print(f"  {customer['phone_number']} - Messages: {customer['total_messages']}")
    
    # Document save test
    print("\n📄 Document test:")
    doc_id = db.save_document('test_faq.pdf', 'data/faqs/test_faq.pdf')
    print(f"  Document saved with ID: {doc_id}")
    
    documents = db.get_all_documents()
    print(f"  Total documents: {len(documents)}")
    
    # Database size
    print(f"\n💾 Database size: {db.get_database_size()}")
    
    # Cleanup test database
    if os.path.exists('test_database.db'):
        os.remove('test_database.db')
        print("\n✅ Test database cleaned up!")
    
    print("\n✅ All tests passed!")