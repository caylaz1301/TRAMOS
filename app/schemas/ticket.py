"""Pydantic schemas for ticket creation and management"""
from typing import Optional
from pydantic import BaseModel, Field, EmailStr
from enum import Enum


class TicketPriority(str, Enum):
    """Ticket priority levels"""
    URGENT = "1"
    HIGH = "2"
    MEDIUM = "3"
    LOW = "4"


class CreateTicketRequest(BaseModel):
    """Request schema for creating a ticket in osTicket"""
    name: str = Field(..., description="Requester name")
    email: EmailStr = Field(..., description="Requester email")
    subject: str = Field(..., description="Ticket subject")
    message: str = Field(..., description="Ticket message/description")
    priority: Optional[int] = Field(default=3, description="Priority level (1-4)")
    source: Optional[str] = Field(default="api", description="Ticket source (api, whatsapp, email, etc)")
    ip: Optional[str] = Field(default="127.0.0.1", description="Client IP address")


class CreateTicketResponse(BaseModel):
    """Response schema after ticket creation"""
    success: bool = Field(..., description="Whether ticket creation was successful")
    ticket_id: Optional[str] = Field(None, description="Created ticket ID from osTicket")
    message: str = Field(..., description="Response message")
    error: Optional[str] = Field(None, description="Error details if unsuccessful")


class TicketStatusResponse(BaseModel):
    """Response schema for ticket status inquiry"""
    ticket_id: str
    status: str
    subject: str
    priority: int
