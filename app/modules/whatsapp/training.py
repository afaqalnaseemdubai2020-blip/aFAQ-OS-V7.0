"""Training Engine"""
import json, os, uuid
from datetime import datetime
from typing import List, Tuple, Optional
from difflib import SequenceMatcher
import re

DATA_DIR = "data/whatsapp"
os.makedirs(DATA_DIR, exist_ok=True)

DEFAULT_TRAINING = [
    {
        "id": "001", "category": "greeting",
        "examples": ["hello", "hi", "hey", "good morning", "مرحبا", "السلام عليكم", "هلا", "أهلا"],
        "response_en": "Hello! Welcome to AFAQ Beauty! How can I help you today?",
        "response_ar": "أهلاً وسهلاً! مرحباً بك في أفاقة بيوتي! كيف أقدر أساعدك؟",
        "language": "auto", "should_escalate": False
    },
    {
        "id": "002", "category": "product_inquiry",
        "examples": ["what products", "show me products", "tell me about babyliss", "ايش عندكم", "وش المنتجات", "منتجات"],
        "response_en": "We have amazing hair tools! Best sellers: Babyliss Pro, Wahl Senior, Dyson Supersonic, GHD Platinum. Want details on any?",
        "response_ar": "عندنا أدوات شعر ممتازة! الأكثر مبيعاً: بابيليس برو، واهل سينيور، دايسون، GHD. تبي تفاصيل؟",
        "language": "auto", "should_escalate": False
    },
    {
        "id": "003", "category": "pricing",
        "examples": ["how much", "price", "كم السعر", "كم يكلف", "price list"],
        "response_en": "What product are you interested in? I'll check the best price and any active offers for you!",
        "response_ar": "أي منتج تبي تعرف سعره؟ بشيك لك على أفضل سعر وعروض!",
        "language": "auto", "should_escalate": False
    },
    {
        "id": "004", "category": "order_status",
        "examples": ["where is my order", "track order", "when will it arrive", "وين طلبيتي", "متى توصل", "تتبع"],
        "response_en": "I'll check your order status! Can you share your order number? It starts with #10xx",
        "response_ar": "بشيك على حالة طلبك! تقدر تشاركني رقم الطلب؟ يبدأ بـ #10xx",
        "language": "auto", "should_escalate": False
    },
    {
        "id": "005", "category": "complaint",
        "examples": ["problem", "broken", "not working", "defective", "مشكلة", "خربان", "مايشتغل", "عيب"],
        "response_en": "Sorry to hear that! Let me connect you with our support team right away.",
        "response_ar": "أعتذر عن هذا! راح أوصلك بفريق الدعم الحين.",
        "language": "auto", "should_escalate": True
    },
    {
        "id": "006", "category": "return_refund",
        "examples": ["return", "refund", "exchange", "إرجاع", "استرداد", "تبديل", "ارجع"],
        "response_en": "I'll connect you with our returns team for a smooth process.",
        "response_ar": "راح أوصلك بفريق المرتجعات عشان نسهل الموضوع.",
        "language": "auto", "should_escalate": True
    },
    {
        "id": "007", "category": "shipping",
        "examples": ["shipping", "delivery", "deliver", "شحن", "توصيل", "كم تكلفة الشحن"],
        "response_en": "We deliver across UAE! Standard 2-3 days (FREE over 200 AED), Express next day (25 AED), Same day Dubai (50 AED).",
        "response_ar": "نوصل في كل الإمارات! عادي 2-3 أيام مجاني فوق 200 درهم، سريع بكرة 25 درهم، نفس اليوم دبي 50 درهم.",
        "language": "auto", "should_escalate": False
    },
    {
        "id": "008", "category": "payment",
        "examples": ["payment", "how to pay", "cash on delivery", "طرق الدفع", "كيف أدفع", "الدفع"],
        "response_en": "We accept: Credit/Debit Card, Cash on Delivery, Apple Pay, Bank Transfer, Tabby (Pay in 4).",
        "response_ar": "نقبل: بطاقة ائتمان، الدفع عند الاستلام، Apple Pay، تحويل بنكي، تابي.",
        "language": "auto", "should_escalate": False
    },
    {
        "id": "009", "category": "store_info",
        "examples": ["location", "where are you", "working hours", "contact", "وين موقعكم", "ساعات", "تواصل"],
        "response_en": "AFAQ Beauty - Dubai\nSun-Thu 9AM-10PM, Fri-Sat 10AM-11PM\nWhatsApp: +971-XXX-XXXX",
        "response_ar": "أفاقة بيوتي - دبي\nالأحد-الخميس 9ص-10م، الجمعة-السبت 10ص-11م",
        "language": "auto", "should_escalate": False
    },
    {
        "id": "010", "category": "promotion",
        "examples": ["offers", "discount", "sale", "coupon", "عروض", "خصومات", "تخفيضات"],
        "response_en": "Current offers: 15% off Babyliss (code BABYLISS15), Buy 2 Get 1 Free on hair care, Free shipping over 200 AED!",
        "response_ar": "العروض: خصم 15% بابيليس كود BABYLISS15، اشتري 2 و1 مجاني، شحن مجاني فوق 200 درهم!",
        "language": "auto", "should_escalate": False
    },
    {
        "id": "011", "category": "goodbye",
        "examples": ["bye", "goodbye", "thanks", "thank you", "مع السلامة", "شكرا", "يسلموا", "خلاص"],
        "response_en": "Thank you! Feel free to message anytime. Have a great day!",
        "response_ar": "شكراً لك! لا تتردد تراسلنا أي وقت. يومك سعيد!",
        "language": "auto", "should_escalate": False
    },
    {
        "id": "012", "category": "wholesale",
        "examples": ["wholesale", "bulk", "salon", "جملة", "كمية", "صالون", "تجاري"],
        "response_en": "We offer 20-30% off for bulk orders with a dedicated account manager! Let me connect you with our B2B team.",
        "response_ar": "نقدم خصم 20-30% للطلبات الكبيرة مع مدير حساب! خلني أوصلك بفريق B2B.",
        "language": "auto", "should_escalate": True
    }
]

class TrainingEngine:
    def __init__(self):
        self.examples = self._load()
    
    def _load(self):
        fp = os.path.join(DATA_DIR, "training.json")
        if os.path.exists(fp):
            return json.load(open(fp))
        self._save(DEFAULT_TRAINING)
        return DEFAULT_TRAINING
    
    def _save(self, data=None):
        fp = os.path.join(DATA_DIR, "training.json")
        json.dump(data or self.examples, open(fp, "w"), indent=2, ensure_ascii=False)
    
    def add_example(self, category, examples, response_ar=None, response_en=None, should_escalate=False, tags=None):
        ex = {
            "id": str(uuid.uuid4())[:8],
            "category": category,
            "examples": examples,
            "response_ar": response_ar,
            "response_en": response_en,
            "language": "auto",
            "should_escalate": should_escalate,
            "tags": tags or [],
            "created_at": datetime.now().isoformat()
        }
        self.examples.append(ex)
        self._save()
        return ex
    
    def find_match(self, message):
        msg_clean = re.sub(r'[^\w\s]', '', message.lower()).strip()
        msg_words = set(msg_clean.split())
        
        best, best_score = None, 0.0
        
        for ex in self.examples:
            for phrase in ex.get("examples", []):
                ph_clean = re.sub(r'[^\w\s]', '', phrase.lower()).strip()
                ph_words = set(ph_clean.split())
                
                if ph_clean in msg_clean or msg_clean in ph_clean:
                    score = 0.95
                elif msg_words and ph_words:
                    overlap = len(msg_words & ph_words)
                    score = overlap / max(len(msg_words), len(ph_words), 1)
                    if score > 0.5:
                        score = min(0.9, score + 0.2)
                else:
                    score = SequenceMatcher(None, msg_clean, ph_clean).ratio()
                
                if score > best_score:
                    best_score = score
                    best = ex
        
        return best, round(best_score, 3)
    
    def get_response(self, message, language="auto"):
        match, confidence = self.find_match(message)
        
        if not match:
            return {"response": None, "confidence": 0.0, "category": "unknown", "should_escalate": True}
        
        is_arabic = any('\u0600' <= c <= '\u06FF' for c in message)
        
        if is_arabic:
            response = match.get("response_ar") or match.get("response_en")
        else:
            response = match.get("response_en") or match.get("response_ar")
        
        threshold = 0.6
        should_escalate = match.get("should_escalate", False) or confidence < threshold
        
        return {
            "response": response,
            "confidence": confidence,
            "category": match.get("category"),
            "should_escalate": should_escalate
        }
    
    def get_stats(self):
        cats = {}
        for ex in self.examples:
            c = ex.get("category", "unknown")
            cats[c] = cats.get(c, 0) + 1
        return {"total_examples": len(self.examples), "categories": cats}

training = TrainingEngine()
