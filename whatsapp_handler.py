import requests
import os
import json

class WhatsAppHandler:
    def __init__(self):
        # WATI Config
        self.wati_token = os.getenv('WATI_API_TOKEN')
        self.wati_url = os.getenv('WATI_API_URL', 'https://live-server-10231096.wati.io/api/v1/sendMessage')
        
        # Debug print
        if self.wati_token:
            print("✅ WATI connected!")
            print(f"📱 Token: {self.wati_token[:10]}...")
            print(f"🔗 URL: {self.wati_url}")
        else:
            print("❌ WATI API Token NOT FOUND in environment variables!")
            print("Please add WATI_API_TOKEN to Railway Variables")
    
    def send_message(self, phone_number, message):
        """Send message via WATI"""
        if not self.wati_token:
            print("❌ No WATI token configured")
            return False, "No WATI token configured"
        
        # Clean phone number
        phone_number = phone_number.replace('+', '').replace(' ', '')
        
        # WATI API endpoint
        url = self.wati_url
        
        headers = {
            "Authorization": f"Bearer {self.wati_token}",
            "Content-Type": "application/json"
        }
        
        # WATI payload format
        payload = {
            "waId": phone_number,
            "message": message
        }
        
        try:
            print(f"📤 Sending to {phone_number} via WATI...")
            print(f"📝 Message: {message[:100]}...")
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ WATI sent successfully!")
                return True, data.get('id', 'success')
            elif response.status_code == 401:
                print(f"❌ WATI Auth Error: Token invalid or expired")
                print(f"❌ Token used: {self.wati_token[:10]}...")
                return False, "401 Unauthorized - Token invalid"
            elif response.status_code == 400:
                print(f"❌ WATI Bad Request: {response.text}")
                return False, f"400 Bad Request: {response.text}"
            else:
                print(f"❌ WATI API Error: {response.status_code}")
                print(f"❌ Response: {response.text}")
                return False, f"WATI API Error: {response.status_code}"
                
        except requests.exceptions.Timeout:
            print("❌ WATI Timeout")
            return False, "Timeout"
        except requests.exceptions.ConnectionError as e:
            print(f"❌ WATI Connection Error: {e}")
            return False, f"Connection Error: {e}"
        except Exception as e:
            print(f"❌ WATI Exception: {e}")
            return False, str(e)
