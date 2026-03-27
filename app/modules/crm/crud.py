from .models import Contact, Deal, Note, LeadStatus
from typing import Optional
from datetime import datetime

class CRMService:
    def __init__(self):
        self._contacts = {}
        self._deals = {}
        self._notes = {}

    def create_contact(self, data):
        c = Contact(**data)
        self._contacts[c.id] = c
        return c

    def get_contact(self, cid):
        return self._contacts.get(cid)

    def list_contacts(self, status=None):
        out = list(self._contacts.values())
        if status:
            out = [c for c in out if c.status == status]
        return sorted(out, key=lambda c: c.created_at, reverse=True)

    def update_contact(self, cid, data):
        c = self._contacts.get(cid)
        if not c: return None
        for k, v in data.items():
            if hasattr(c, k) and v is not None:
                setattr(c, k, v)
        c.updated_at = datetime.now().isoformat()
        return c

    def delete_contact(self, cid):
        return self._contacts.pop(cid, None) is not None

    def create_deal(self, data):
        d = Deal(**data)
        self._deals[d.id] = d
        return d

    def get_deal(self, did):
        return self._deals.get(did)

    def list_deals(self, contact_id=None):
        out = list(self._deals.values())
        if contact_id:
            out = [d for d in out if d.contact_id == contact_id]
        return sorted(out, key=lambda d: d.created_at, reverse=True)

    def create_note(self, data):
        n = Note(**data)
        self._notes[n.id] = n
        return n

    def list_notes(self, contact_id):
        return [n for n in self._notes.values() if n.contact_id == contact_id]

crm = CRMService()