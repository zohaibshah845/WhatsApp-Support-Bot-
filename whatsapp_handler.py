# whatsapp_handler.py - UltraMsg WhatsApp Integration
# Twilio ki jagah ab UltraMsg use karenge (Pakistan Friendly)
# UltraMsg: https://ultramsg.com - Free 1000 messages/month

import requests
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class WhatsAppHandler:
    """WhatsApp messages handle karne ke liye - UltraMsg API ke saath"""
    
    def __init__(self, instance_id=None, token=None):
        """
        UltraMsg WhatsApp handler initialize karo
        
        Args:
            instance_id: UltraMsg Instance ID (ultramsg.com se milega)
            token: UltraMsg Token (ultramsg.com se milega)
        """
        # Environment variables se credentials lo agar directly nahi diye
        self.instance_id = instance_id or os.getenv('ULTRAMSG_INSTANCE_ID')
        self.token = token or os.getenv('ULTRAMSG_TOKEN')
        
        # UltraMsg API base URLs
        self.api_base = f"https://api.ultramsg.com/{self.instance_id}"
        
        # Connection status
        if self.instance_id and self.token:
            self.is_connected = True
            print(f"✅ UltraMsg connected!")
            print(f"📱 Instance ID: {self.instance_id[:10]}...")
        else:
            self.is_connected = False
            print("⚠️ UltraMsg credentials missing! WhatsApp disabled.")
        
        # Message log file
        self.log_file = 'whatsapp_logs.json'
    
    def send_message(self, to_number: str, message: str) -> Tuple[bool, str]:
        """
        Customer ko WhatsApp message bhejo
        
        Args:
            to_number: Customer ka phone number (e.g., +923001234567)
            message: Message content
        
        Returns:
            (success, message_id_or_error)
        """
        if not self.is_connected:
            print("❌ UltraMsg connected nahi hai!")
            return False, "UltraMsg not connected"
        
        try:
            # Phone number format karo
            formatted_number = self.format_phone_number(to_number)
            
            # UltraMsg API endpoint
            url = f"{self.api_base}/messages/chat"
            
            # Request payload
            payload = {
                'token': self.token,
                'to': formatted_number,
                'body': message,
                'priority': 10,  # High priority
                'referenceId': f"msg_{datetime.now().timestamp()}"
            }
            
            # Headers
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            # API call karo
            response = requests.post(url, data=payload, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                message_id = result.get('id', result.get('messageId', 'unknown'))
                print(f"✅ Message sent to {formatted_number}: {message_id}")
                
                # Log save karo
                self._log_message(formatted_number, message, 'outgoing')
                
                return True, str(message_id)
            else:
                error_msg = f"API Error: {response.status_code} - {response.text}"
                print(f"❌ {error_msg}")
                return False, error_msg
                
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            return False, str(e)
    
    def send_media_message(self, to_number: str, media_url: str, caption: str = None) -> Tuple[bool, str]:
        """
        Customer ko media message bhejo (image, video, etc.)
        
        Args:
            to_number: Customer ka phone number
            media_url: Media file ka URL
            caption: Optional caption
        """
        if not self.is_connected:
            return False, "UltraMsg not connected"
        
        try:
            formatted_number = self.format_phone_number(to_number)
            
            # UltraMsg API endpoint for media
            url = f"{self.api_base}/messages/image"  # Ya video/document ke liye alag endpoint
            
            payload = {
                'token': self.token,
                'to': formatted_number,
                'image': media_url,
                'caption': caption or '',
                'priority': 10
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            response = requests.post(url, data=payload, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                message_id = result.get('id', 'unknown')
                print(f"✅ Media sent to {formatted_number}: {message_id}")
                return True, str(message_id)
            else:
                error_msg = f"API Error: {response.status_code} - {response.text}"
                print(f"❌ {error_msg}")
                return False, error_msg
                
        except Exception as e:
            print(f"❌ Error sending media: {e}")
            return False, str(e)
    
    def send_document(self, to_number: str, document_url: str, filename: str) -> Tuple[bool, str]:
        """Customer ko document bhejo (PDF, DOCX, etc.)"""
        if not self.is_connected:
            return False, "UltraMsg not connected"
        
        try:
            formatted_number = self.format_phone_number(to_number)
            
            url = f"{self.api_base}/messages/document"
            
            payload = {
                'token': self.token,
                'to': formatted_number,
                'document': document_url,
                'filename': filename,
                'priority': 10
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            response = requests.post(url, data=payload, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                message_id = result.get('id', 'unknown')
                print(f"✅ Document sent to {formatted_number}: {message_id}")
                return True, str(message_id)
            else:
                return False, f"API Error: {response.status_code}"
                
        except Exception as e:
            print(f"❌ Error sending document: {e}")
            return False, str(e)
    
    def create_webhook_response(self, message_text: str) -> str:
        """
        Webhook ke liye response create karo
        UltraMsg webhook ke liye simple JSON return karo
        """
        # UltraMsg webhook simple text response expect karta hai
        return message_text
    
    def parse_incoming_message(self, request_data) -> Dict:
        """
        Incoming WhatsApp message ko parse karo (UltraMsg webhook format)
        
        Args:
            request_data: Flask request data (JSON ya form)
        
        Returns:
            Dictionary with message details
        """
        # UltraMsg webhook data format
        message_data = {
            'from': request_data.get('from', ''),
            'to': request_data.get('to', ''),
            'body': request_data.get('body', ''),
            'message_id': request_data.get('id', ''),
            'timestamp': request_data.get('time', datetime.now().timestamp()),
            'phone': self.extract_phone_number(request_data.get('from', ''))
        }
        
        return message_data
    
    def extract_phone_number(self, from_number: str) -> str:
        """
        Phone number extract aur format karo
        
        Args:
            from_number: '923001234567' ya '+923001234567' format
        
        Returns:
            '+923001234567' format mein number
        """
        if not from_number:
            return ''
        
        # '@c.us' suffix remove karo (agar hai)
        phone = from_number.replace('@c.us', '').replace('@g.us', '')
        
        # Clean karo - sirf digits aur + sign rakho
        phone = re.sub(r'[^\d+]', '', phone)
        
        return self.format_phone_number(phone)
    
    def format_phone_number(self, phone_number: str) -> str:
        """
        Phone number ko proper international format mein lao
        
        Args:
            phone_number: Koi bhi phone number format
        
        Returns:
            E.164 format: +923001234567
        """
        # Sab non-digit characters remove karo
        digits = re.sub(r'\D', '', phone_number)
        
        # Agar number 0 se start ho to 92 lagao (Pakistan)
        if digits.startswith('0'):
            digits = '92' + digits[1:]
        # Agar number 92 se start ho to + lagao
        elif digits.startswith('92') and len(digits) > 10:
            digits = digits
        # Agar number 10 digits ka ho to 92 lagao
        elif len(digits) == 10 and digits.startswith('3'):
            digits = '92' + digits
        
        # + sign lagao
        return '+' + digits
    
    def format_message(self, text: str) -> str:
        """
        Message ko WhatsApp formatting ke liye prepare karo
        
        WhatsApp formatting:
        *bold* - Bold text
        _italic_ - Italic text
        ~strikethrough~ - Strikethrough
        """
        # Basic formatting
        text = text.replace('**', '*')  # Double asterisk to single
        text = text.replace('__', '_')  # Double underscore to single
        
        # Extra spaces remove karo
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def send_bulk_messages(self, numbers_list: List[str], message: str) -> List[Dict]:
        """
        Multiple numbers ko message bhejo
        
        Args:
            numbers_list: List of phone numbers
            message: Message to send
        
        Returns:
            List of results
        """
        results = []
        
        for number in numbers_list:
            success, response = self.send_message(number, message)
            results.append({
                'number': number,
                'success': success,
                'response': response
            })
            
            # Rate limiting (1 second ka gap)
            import time
            time.sleep(1)
        
        return results
    
    def get_connection_status(self) -> Dict:
        """
        UltraMsg connection status check karo
        """
        if not self.is_connected:
            return {'connected': False, 'message': 'Not configured'}
        
        try:
            url = f"{self.api_base}/instance/status"
            params = {'token': self.token}
            
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                status_data = response.json()
                return {
                    'connected': True,
                    'status': status_data.get('status', 'unknown'),
                    'instance_id': self.instance_id[:10] + '...'
                }
            else:
                return {'connected': False, 'message': 'API error'}
                
        except Exception as e:
            return {'connected': False, 'message': str(e)}
    
    def send_typing_indicator(self, to_number: str, is_typing: bool = True) -> bool:
        """
        Typing indicator bhejo (UltraMsg support karta hai)
        """
        if not self.is_connected:
            return False
        
        try:
            formatted_number = self.format_phone_number(to_number)
            url = f"{self.api_base}/messages/typing"
            
            payload = {
                'token': self.token,
                'to': formatted_number,
                'typing': '1' if is_typing else '0'
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            response = requests.post(url, data=payload, headers=headers)
            return response.status_code == 200
            
        except Exception as e:
            print(f"❌ Typing indicator error: {e}")
            return False
    
    def _log_message(self, phone_number: str, message: str, direction: str) -> None:
        """
        Message log karo (debugging ke liye)
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'phone': phone_number,
            'direction': direction,
            'message': message[:200]
        }
        
        try:
            # Existing logs read karo
            try:
                with open(self.log_file, 'r') as f:
                    logs = json.load(f)
            except:
                logs = []
            
            # Naya log add karo
            logs.append(log_entry)
            
            # Sirf last 1000 logs rakho
            if len(logs) > 1000:
                logs = logs[-1000:]
            
            # Save karo
            with open(self.log_file, 'w') as f:
                json.dump(logs, f, indent=2)
                
        except Exception as e:
            print(f"❌ Logging error: {e}")


# Test function - Direct run karne ke liye
if __name__ == "__main__":
    print("🧪 UltraMsg WhatsApp Handler Test")
    print("=" * 40)
    
    # Test handler (credentials ke baghair)
    handler = WhatsAppHandler()
    
    # Phone number format test
    test_numbers = [
        '03001234567',
        '+923001234567',
        '923001234567',
        '3001234567',
        '923001234567@c.us'
    ]
    
    print("\n📱 Phone Number Format Test:")
    for num in test_numbers:
        formatted = handler.format_phone_number(num)
        print(f"  {num:30s} -> {formatted}")
    
    # Message format test
    print("\n💬 Message Format Test:")
    test_messages = [
        '**Bold** text',
        '_Italic_ text',
        'Hello   World',
        '  Extra spaces  '
    ]
    
    for msg in test_messages:
        formatted = handler.format_message(msg)
        print(f"  '{msg}' -> '{formatted}'")
    
    print("\n✅ Test complete!")
    print("\n📝 Note: Real test ke liye UltraMsg credentials chahiye!")
    print("   1. https://ultramsg.com par jao")
    print("   2. Sign up karo")
    print("   3. Instance ID aur Token lo")
    print("   4. .env file mein add karo")