"""
Pytest configuration and fixtures for TRAMOS tests
"""

import os
import sys
import pytest
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture
def mock_db_session():
    """Mock database session for testing"""
    session = MagicMock()
    session.execute.return_value.scalar.return_value = 0
    session.execute.return_value.fetchall.return_value = []
    session.execute.return_value.fetchone.return_value = None
    return session


@pytest.fixture
def mock_db_manager(mock_db_session):
    """Mock database manager"""
    manager = MagicMock()
    manager.get_session.return_value.__enter__ = MagicMock(return_value=mock_db_session)
    manager.get_session.return_value.__exit__ = MagicMock(return_value=False)
    manager.SessionLocal = MagicMock(return_value=mock_db_session)
    return manager


# ============================================================================
# API RESPONSE FIXTURES
# ============================================================================

@pytest.fixture
def sample_dashboard_response():
    """Sample dashboard API response"""
    return {
        "overview": {
            "total_sessions": 150,
            "total_tickets": 25,
            "total_messages": 850,
            "success_rate": 83.33,
            "avg_messages_per_session": 5.67,
            "active_sessions": 3,
            "ai_resolved_sessions": 125,
        },
        "categories": {
            "categories": [
                {"name": "GPS", "count": 45},
                {"name": "Kamera", "count": 35},
                {"name": "Battery", "count": 30},
                {"name": "Lainnya", "count": 40},
            ]
        },
        "quality": {
            "completion_rate": 78.5,
            "avg_duration_seconds": 180,
            "abandoned_sessions": 12,
            "total_sessions": 150,
        },
        "tickets": {
            "total_tickets": 25,
            "by_category": [
                {"category": "GPS", "count": 10},
                {"category": "Kamera", "count": 8},
                {"category": "Battery", "count": 7},
            ]
        },
        "severity": {
            "severities": [
                {"name": "medium", "count": 15},
                {"name": "low", "count": 20},
                {"name": "high", "count": 5},
            ]
        },
        "recent_sessions": {
            "sessions": [
                {
                    "name": "John Doe",
                    "phone": "+6281234567890",
                    "problem": "GPS tidak akurat",
                    "category": "GPS",
                    "state": "resolved",
                    "messages": 8,
                    "created_at": datetime.now().isoformat(),
                }
            ]
        }
    }


@pytest.fixture
def sample_session():
    """Sample WhatsApp session"""
    return {
        "id": 1,
        "phone_number": "+6281234567890",
        "user_name": "John Doe",
        "current_state": "resolved",
        "category": "GPS",
        "ticket_id": None,
        "message_count": 8,
        "created_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def sample_message():
    """Sample WhatsApp message"""
    return {
        "id": 1,
        "conversation_id": 1,
        "phone_number": "+6281234567890",
        "sender": "user",
        "message_text": "GPS saya tidak akurat",
        "message_type": "text",
        "intent": "troubleshooting",
        "category": "GPS",
        "confidence": 85,
        "created_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def sample_ticket():
    """Sample support ticket"""
    return {
        "id": 1,
        "user_id": 1,
        "phone_number": "+6281234567890",
        "subject": "GPS tidak akurat",
        "description": "GPS di dashboard tidak menunjukkan lokasi yang benar",
        "category": "GPS",
        "status": "open",
        "priority": "medium",
        "osticket_id": 12345,
        "created_at": datetime.utcnow().isoformat(),
    }


# ============================================================================
# API CLIENT FIXTURES
# ============================================================================

@pytest.fixture
def api_client():
    """Async HTTP client for API testing"""
    import httpx
    return httpx.AsyncClient(base_url="http://testserver")


# ============================================================================
# MOCK SERVICES
# ============================================================================

@pytest.fixture
def mock_ai_engine():
    """Mock AI engine"""
    engine = MagicMock()
    engine.generate_response = AsyncMock(return_value="Test response from AI")
    engine.analyze_intent = AsyncMock(return_value={
        "intent": "troubleshooting",
        "category": "GPS",
        "confidence": 85
    })
    return engine


@pytest.fixture
def mock_kb_service():
    """Mock Knowledge Base service"""
    kb = MagicMock()
    kb.search = AsyncMock(return_value=[
        {
            "id": 1,
            "title": "GPS Accuracy Issues",
            "content": "Solution for GPS accuracy...",
            "similarity": 0.92
        }
    ])
    return kb


@pytest.fixture
def mock_conversation_coordinator():
    """Mock conversation coordinator"""
    coordinator = MagicMock()
    coordinator.process_message = AsyncMock(return_value={
        "response": "Bot response here",
        "state": "collecting_details",
        "intent": "troubleshooting"
    })
    coordinator.health = AsyncMock(return_value={"status": "healthy", "distributed": True})
    coordinator.initialize = AsyncMock()
    coordinator.close = AsyncMock()
    return coordinator


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_test_user(role="user"):
    """Create test user data"""
    return {
        "id": 1,
        "email": f"test_{role}@example.com",
        "full_name": f"Test {role.title()}",
        "phone": "+6281234567890",
        "role": role,
        "is_verified": True,
        "created_at": datetime.utcnow().isoformat(),
    }


def create_test_conversation(state="new_issue", category="GPS"):
    """Create test conversation data"""
    return {
        "id": 1,
        "phone_number": "+6281234567890",
        "current_state": state,
        "category": category,
        "ticket_id": None,
        "context_data": {},
        "created_at": datetime.utcnow().isoformat(),
        "last_message_at": datetime.utcnow().isoformat(),
    }
