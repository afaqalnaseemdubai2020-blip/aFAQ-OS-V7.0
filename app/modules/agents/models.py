"""Agents Module — Models"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    WON = "won"
    LOST = "lost"

class Channel(str, Enum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    CALL = "call"
    CHAT = "chat"

class LeadCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    company: Optional[str] = None
    source: str = "direct"
    interested_products: List[str] = []
    notes: Optional[str] = None
    language: str = "en"

class LeadUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    company: Optional[str] = None
    status: Optional[str] = None
    score: Optional[float] = None
    interested_products: Optional[List[str]] = None
    notes: Optional[str] = None
    language: Optional[str] = None

class BulkLeadCreate(BaseModel):
    leads: List[LeadCreate]
