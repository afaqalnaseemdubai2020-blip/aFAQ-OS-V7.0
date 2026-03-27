"""WhatsApp Config"""
import os

class WhatsAppConfig:
    def __init__(self):
        self.phone_number_id = os.getenv("WA_PHONE_NUMBER_ID", "")
        self.access_token = os.getenv("WA_ACCESS_TOKEN", "")
        self.verify_token = os.getenv("WA_VERIFY_TOKEN", "afaq_verify_2024")
        self.api_version = "v18.0"
    
    @property
    def base_url(self):
        return f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}"
    
    @property
    def headers(self):
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    @property
    def is_configured(self):
        return bool(self.access_token and self.phone_number_id)

config = WhatsAppConfig()
