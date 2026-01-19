"""Pydantic schemas for WhatsApp webhook data"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class WhatsAppTextMessage(BaseModel):
    """WhatsApp text message body"""
    body: str = Field(..., description="Text message content")


class WhatsAppMessageObject(BaseModel):
    """WhatsApp message object"""
    from_: str = Field(..., alias="from", description="Sender phone number")
    id: str = Field(..., description="Message ID")
    timestamp: str = Field(..., description="Message timestamp")
    type: str = Field(..., description="Message type (text, image, etc)")
    text: Optional[WhatsAppTextMessage] = None


class WhatsAppContactObject(BaseModel):
    """WhatsApp contact information"""
    profile: Optional[Dict[str, str]] = None
    wa_id: str = Field(..., description="WhatsApp ID")


class WhatsAppValueObject(BaseModel):
    """WhatsApp value object containing messages and contacts"""
    messaging_product: str
    messages: Optional[List[WhatsAppMessageObject]] = None
    contacts: Optional[List[WhatsAppContactObject]] = None
    statuses: Optional[List[Dict[str, Any]]] = None


class WhatsAppChangeObject(BaseModel):
    """WhatsApp change object"""
    value: WhatsAppValueObject
    field: str


class WhatsAppEntry(BaseModel):
    """WhatsApp entry object"""
    id: str
    changes: List[WhatsAppChangeObject]


class WhatsAppWebhookPayload(BaseModel):
    """Complete WhatsApp webhook payload"""
    object: str
    entry: List[WhatsAppEntry]


class WhatsAppWebhookVerification(BaseModel):
    """WhatsApp webhook verification request"""
    hub_challenge: Optional[str] = None
    hub_mode: Optional[str] = None
    hub_verify_token: Optional[str] = None
