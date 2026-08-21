# whatsapp_handler.py - WATI WhatsApp Integration (FIXED v2)
import requests
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class WhatsAppHandler:
    """WhatsApp messages handle karne ke liye - WATI API ke saath"""
    
    def __init__(self, instance_id=None, token=None):
        # WATI credentials
        self.token = token or os.getenv('WATI_API_TOKEN')
        self.tenant_id = os.getenv('WATI_TENANT_ID', '10231096')
        
        # ✅ FIXED: Correct WATI API base URL
        self.api_base = f"https://live-server-{self.tenant_id}.wati.io"
        
        if self.token:
            self.is_connected = True
            print(f"✅ WATI connected!")
            print(f"📱 Tenant ID: {self.tenant_id}")
            print(f"🔗 API URL: {self.api_base}")
        else:
            self.is_connected = False
            print("⚠️ WATI credentials missing!")
        
        self.log_file = 'whatsapp_logs.json'
    
    def send_message(self, to_number: str, message: str) -> Tuple[bool, str]:
        """Customer ko WhatsApp message bhejo via WATI"""
        if not self.is_connected:
            return False, "WATI not connected"
        
        try:
            formatted_number = self.format_phone_number_for_wati(to_number)
            
            # ✅ FIXED: Correct WATI API endpoint for sending messages
            url = f"{self.api_base}/api/v1/sendSessionMessage/{formatted_number}"
            
            # ✅ FIXED: Correct payload format
            payload = {
                'messageText': message
            }
            
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json-patch+json'  # WATI expects this
            }
            
            print(f"📤 Sending to: {formatted_number}")
            print(f"🔗 URL: {url}")
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                message_id = result.get('id', result.get('whatsappMessageId', 'unknown'))
                print(f"✅ WATI Message sent: {message_id}")
                self._log_message(formatted_number, message, 'outgoing')
                return True, str(message_id)
            elif response.status_code == 401:
                error_msg = "401 Unauthorized - Token invalid"
                print(f"❌ {error_msg}")
                return False, error_msg
            else:
                error_msg = f"WATI API Error: {response.status_code} - {response.text[:200]}"
                print(f"❌ {error_msg}")
                return False, error_msg
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False, str(e)
    
    def send_template_message(self, to_number: str, template_name: str, parameters: List[dict] = None) -> Tuple[bool, str]:
        """Template message bhejo (pre-approved templates ke liye)"""
        if not self.is_connected:
            return False, "WATI not connected"
        
        try:
            formatted_number = self.format_phone_number_for_wati(to_number)
            
            url = f"{self.api_base}/api/v1/sendTemplateMessage"
            
            payload = {
                'waId': formatted_number,
                'template_name': template_name,
                'parameters': parameters or []
            }
            
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Template sent to {formatted_number}")
                return True, str(result.get('id', 'success'))
            else:
                error_msg = f"WATI API Error: {response.status_code} - {response.text[:200]}"
                print(f"❌ {error_msg}")
                return False, error_msg
                
        except Exception as e:
            print(f"❌ Error sending template: {e}")
            return False, str(e)
    
    def format_phone_number_for_wati(self, phone_number: str) -> str:
        """WATI ko phone number without + chahiye"""
        digits = re.sub(r'\D', '', phone_number)
        digits = digits.replace('c', '').replace('us', '')
        
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
