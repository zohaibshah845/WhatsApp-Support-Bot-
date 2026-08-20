# whatsapp_handler.py - WATI WhatsApp Integration
import requests
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class WhatsAppHandler:
    """WhatsApp messages handle karne ke liye - WATI API ke saath"""
    
    def _init_(self, instance_id=None, token=None):
        """
        WATI WhatsApp handler initialize karo
        
        Args:
            instance_id: WATI Instance ID (not needed for WATI)
            token: WATI API Token (Bearer token)
        """
        # WATI credentials
        self.token = token or os.getenv('WATI_API_TOKEN')
        self.api_base = "https://live-mt-server.wati.io"
        self.tenant_id = os.getenv('WATI_TENANT_ID', '10231096')  # Aapka WATI ID
        
        # Connection status
        if self.token:
            self.is_connected = True
            print(f"✅ WATI connected!")
            print(f"📱 Tenant ID: {self.tenant_id}")
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
            
            # WATI API endpoint
            url = f"{self.api_base}/{self.tenant_id}/api/v1/sendSessionMessage/{formatted_number}"
            
            # Request payload - WATI format
            payload = {
                'messageText': message
            }
            
            # Headers - WATI Bearer token
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            }
            
            # API call karo
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                message_id = result.get('id', 'unknown')
                print(f"✅ WATI Message sent to {formatted_number}: {message_id}")
                
                # Log save karo
                self._log_message(formatted_number, message, 'outgoing')
                
                return True, str(message_id)
            else:
                error_msg = f"WATI API Error: {response.status_code} - {response.text}"
                print(f"❌ {error_msg}")
                return False, error_msg
                
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            return False, str(e)
    
    def send_media_message(self, to_number: str, media_url: str, caption: str = None) -> Tuple[bool, str]:
        """Customer ko media message bhejo via WATI"""
        if not self.is_connected:
            return False, "WATI not connected"
        
        try:
            formatted_number = self.format_phone_number_for_wati(to_number)
            
            url = f"{self.api_base}/{self.tenant_id}/api/v1/sendSessionFile/{formatted_number}"
            
            payload = {
                'mediaUrl': media_url,
                'caption': caption or ''
            }
            
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                message_id = result.get('id', 'unknown')
                print(f"✅ WATI Media sent to {formatted_number}: {message_id}")
                return True, str(message_id)
            else:
                return False, f"WATI API Error: {response.status_code}"
                
        except Exception as e:
            print(f"❌ Error sending media: {e}")
            return False, str(e)
    
    def format_phone_number_for_wati(self, phone_number: str) -> str:
        """
        WATI ko phone number without + chahiye: 923001234567
        """
        # Sab non-digit characters remove karo
        digits = re.sub(r'\D', '', phone_number)
        
        # Agar number 0 se start ho to 92 lagao (Pakistan)
        if digits.startswith('0'):
            digits = '92' + digits[1:]
        # Agar number 10 digits ka ho to 92 lagao
        elif len(digits) == 10 and digits.startswith('3'):
            digits = '92' + digits
        
        return digits  # WATI ko + nahi chahiye
    
    def format_phone_number(self, phone_number: str) -> str:
        """
        General format: +923001234567
