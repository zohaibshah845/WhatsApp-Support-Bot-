# whatsapp_handler.py - WATI WhatsApp Integration (FIXED)
import requests
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class WhatsAppHandler:
    """WhatsApp messages handle karne ke liye - WATI API ke saath"""
    
    def __init__(self, instance_id=None, token=None):
        """
        WATI WhatsApp handler initialize karo
        
        Args:
            instance_id: Not needed for WATI
            token: WATI API Token (Bearer token)
        """
        # WATI credentials
        self.token = token or os.getenv('WATI_API_TOKEN')
        self.tenant_id = os.getenv('WATI_TENANT_ID', '10231096')
        
        # ✅ FIXED: Correct WATI API URL format
        self.api_base = f"https://live-server-{self.tenant_id}.wati.io"
        
        # Connection status
        if self.token:
            self.is_connected = True
            print(f"✅ WATI connected!")
            print(f"📱 Tenant ID: {self.tenant_id}")
            print(f"🔗 API URL: {self.api_base}")
        else:
            self.is_connected = False
            print("⚠️ WATI credentials missing! WhatsApp disabled.")
        
        # Message log file
        self.log_file = 'whatsapp_logs.json'
    
    def send_message(self, to_number: str, message: str) -> Tuple[bool, str]:
        """
        Customer ko WhatsApp message bhejo via WATI
        
        Args:
            to_number: Customer ka phone number (e.g., 923001234567)
            message: Message content
        
        Returns:
            (success, message_id_or_error)
        """
        if not self.is_connected:
            print("❌ WATI connected nahi hai!")
            return False, "WATI not connected"
        
        try:
            # Phone number format karo - WATI ko without + chahiye
            formatted_number = self.format_phone_number_for_wati(to_number)
            
            # ✅ FIXED: Correct WATI API endpoint
            url = f"{self.api_base}/api/v1/sendMessage"
            
            # ✅ FIXED: Correct WATI payload format
            payload = {
                'waId': formatted_number,
                'message': message
            }
            
            # Headers
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            }
            
            print(f"📤 Sending to: {formatted_number}")
            print(f"🔗 URL: {url}")
            print(f"📝 Message: {message[:50]}...")
            
            # API call karo
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                message_id = result.get('id', 'unknown')
                print(f"✅ WATI Message sent to {formatted_number}: {message_id}")
                
                # Log save karo
                self._log_message(formatted_number, message, 'outgoing')
                
                return True, str(message_id)
            elif response.status_code == 401:
                error_msg = "401 Unauthorized - Token invalid or expired"
                print(f"❌ {error_msg}")
                print(f"❌ Token used: {self.token[:20]}...")
                return False, error_msg
            else:
                error_msg = f"WATI API Error: {response.status_code} - {response.text}"
                print(f"❌ {error_msg}")
                return False, error_msg
                
        except requests.exceptions.Timeout:
            print("❌ WATI Timeout")
            return False, "Timeout"
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            return False, str(e)
    
    def send_media_message(self, to_number: str, media_url: str, caption: str = None) -> Tuple[bool, str]:
        """Customer ko media message bhejo via WATI"""
        if not self.is_connected:
            return False, "WATI not connected"
        
        try:
            formatted_number = self.format_phone_number_for_wati(to_number)
            
            # ✅ FIXED: Correct media endpoint
            url = f"{self.api_base}/api/v1/sendMedia"
            
            payload = {
                'waId': formatted_number,
                'mediaUrl': media_url,
                'caption': caption or ''
            }
            
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                message_id = result.get('id', 'unknown')
                print(f"✅ WATI Media sent to {formatted_number}: {message_id}")
                return True, str(message_id)
            else:
                error_msg = f"WATI API Error: {response.status_code} - {response.text}"
                print(f"❌ {error_msg}")
                return False, error_msg
                
        except Exception as e:
            print(f"❌ Error sending media: {e}")
            return False, str(e)
    
    def format_phone_number_for_wati(self, phone_number: str) -> str:
        """
        WATI ko phone number without + chahiye: 923001234567
        """
        # Remove all non-digits
        digits = re.sub(r'\D', '', phone_number)
        
        # Remove @c.us if present
        digits = digits.replace('c', '').replace('us', '')
        
        # Format for Pakistan numbers
        if digits.startswith('0'):
            digits = '92' + digits[1:]
        elif len(digits) == 10 and digits.startswith('3'):
            digits = '92' + digits
        
        return digits
    
    def format_phone_number(self, phone_number: str) -> str:
        """General format: +923001234567"""
        digits = re.sub(r'\D', '', phone_number)
        
        digits = digits.replace('c', '').replace('us', '')
        
        if digits.startswith('0'):
            digits = '92' + digits[1:]
        elif len(digits) == 10 and digits.startswith('3'):
            digits = '92' + digits
        
        return '+' + digits
    
    def format_message(self, text: str) -> str:
        """WhatsApp formatting"""
        text = text.replace('*', '')
        text = text.replace('_', '')
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _log_message(self, phone_number: str, message: str, direction: str) -> None:
        """Message log karo"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'phone': phone_number,
            'direction': direction,
            'message': message[:200]
        }
        
        try:
            try:
                with open(self.log_file, 'r') as f:
                    logs = json.load(f)
            except:
                logs = []
            
            logs.append(log_entry)
            
            if len(logs) > 1000:
                logs = logs[-1000:]
            
            with open(self.log_file, 'w') as f:
                json.dump(logs, f, indent=2)
                
        except Exception as e:
            print(f"❌ Logging error: {e}")
    
    def get_connection_status(self):
        """Health check ke liye"""
        return {
            "connected": self.is_connected, 
            "provider": "WATI",
            "tenant_id": self.tenant_id,
            "api_url": self.api_base
        }


# Test function
if __name__ == "__main__":
    print("🧪 WATI WhatsApp Handler Test")
    print("=" * 40)
    
    handler = WhatsAppHandler()
    
    test_numbers = [
        '03001234567',
        '+923001234567',
        '923001234567',
        '923286652760@c.us',
    ]
    
    print("\n📱 Phone Number Format Test for WATI:")
    for num in test_numbers:
        formatted = handler.format_phone_number_for_wati(num)
        print(f"  {num:25s} -> {formatted}")
    
    print("\n📊 Connection Status:")
    print(json.dumps(handler.get_connection_status(), indent=2))
