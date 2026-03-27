from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from enum import Enum
import uuid

class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    WON = "won"
    LOST = "lost"

class Contact(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    phone: str = ""
    company: str = ""
    status: LeadStatus = LeadStatus.NEW
    assigned_to: str = ""
    notes: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

class Deal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    contact_id: str
    title: str
    value: float = 0.0
    currency: str = "USD"
    stage: LeadStatus = LeadStatus.NEW
    close_date: Optional[date] = None
    probability: int = 50
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

class Note(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    contact_id: str
    content: str
    author: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())