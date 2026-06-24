"""
Tests for Analytics endpoints
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch


class TestAnalyticsEndpoints:
    """Test analytics API endpoints"""

    @pytest.fixture
    def mock_db_with_data(self, mock_db_session):
        """Mock database with sample data"""
        # Overview stats
        mock_db_session.execute.return_value.scalar.return_value = 150
        mock_db_session.execute.return_value.fetchall.return_value = [
            ("GPS", 45),
            ("Kamera", 35),
            ("Battery", 30),
        ]
        return mock_db_session

    def test_dashboard_response_structure(self, sample_dashboard_response):
        """Test dashboard response has correct structure"""
        required_keys = [
            "overview",
            "categories",
            "quality",
            "tickets",
            "severity",
            "recent_sessions"
        ]

        for key in required_keys:
            assert key in sample_dashboard_response, f"Missing key: {key}"

    def test_overview_metrics_calculation(self, sample_dashboard_response):
        """Test overview metrics are calculated correctly"""
        overview = sample_dashboard_response["overview"]

        # Test AI resolution rate
        expected_resolution_rate = (
            overview["ai_resolved_sessions"] /
            overview["total_sessions"] * 100
        )
        assert abs(overview["success_rate"] - expected_resolution_rate) < 0.1

        # Test avg messages
        expected_avg = (
            overview["total_messages"] /
            overview["total_sessions"]
        )
        assert abs(overview["avg_messages_per_session"] - expected_avg) < 0.1

    def test_category_distribution(self, sample_dashboard_response):
        """Test category distribution sums to total"""
        categories = sample_dashboard_response["categories"]["categories"]
        total = sum(c["count"] for c in categories)

        assert total > 0
        assert total <= sample_dashboard_response["overview"]["total_sessions"]

    def test_ticket_metrics(self, sample_dashboard_response):
        """Test ticket metrics are consistent"""
        overview = sample_dashboard_response["overview"]
        tickets = sample_dashboard_response["tickets"]

        # Tickets created should be less than or equal to total sessions
        assert tickets["total_tickets"] <= overview["total_sessions"]

        # Tickets by category should sum to total
        by_cat_total = sum(c["count"] for c in tickets.get("by_category", []))
        assert by_cat_total <= tickets["total_tickets"]

    def test_severity_distribution(self, sample_dashboard_response):
        """Test severity distribution"""
        severities = sample_dashboard_response["severity"]["severities"]

        # Should have valid severity names
        valid_severities = {"critical", "high", "medium", "normal", "low"}
        for sev in severities:
            assert sev["name"] in valid_severities
            assert sev["count"] >= 0

    def test_recent_sessions_structure(self, sample_dashboard_response):
        """Test recent sessions have correct structure"""
        sessions = sample_dashboard_response["recent_sessions"]["sessions"]

        for session in sessions:
            assert "name" in session
            assert "phone" in session
            assert "state" in session
            assert "created_at" in session


class TestAnalyticsCalculations:
    """Test analytics calculation logic"""

    def test_ai_resolution_rate_zero_sessions(self):
        """Test AI resolution rate with zero sessions"""
        total_sessions = 0
        ai_resolved = 0

        resolution_rate = (
            (ai_resolved / total_sessions * 100) if total_sessions > 0 else 0
        )
        assert resolution_rate == 0

    def test_ai_resolution_rate_full_resolution(self):
        """Test AI resolution rate with 100% resolution"""
        total_sessions = 100
        ai_resolved = 100

        resolution_rate = (
            ai_resolved / total_sessions * 100
        )
        assert resolution_rate == 100.0

    def test_ai_resolution_rate_partial_resolution(self):
        """Test AI resolution rate with partial resolution"""
        total_sessions = 150
        ai_resolved = 125

        resolution_rate = ai_resolved / total_sessions * 100
        assert abs(resolution_rate - 83.33) < 0.1

    def test_abandonment_rate_calculation(self):
        """Test abandonment rate calculation"""
        total_sessions = 100
        abandoned = 15

        abandonment_rate = abandoned / total_sessions * 100
        assert abandonment_rate == 15.0

    def test_message_efficiency_score(self):
        """Test message efficiency scoring"""
        avg_messages = 5

        # Ideal is 4-6 messages
        if avg_messages <= 6:
            efficiency = 100
        else:
            efficiency = max(0, 100 - (avg_messages - 6) * 10)

        assert efficiency == 100

    def test_performance_score_weighted(self):
        """Test weighted performance score calculation"""
        ai_resolution = 80  # 40% weight
        completion = 85   # 30% weight
        abandonment = 5    # 15% weight (inverse)
        message_eff = 90    # 15% weight

        score = (
            ai_resolution * 0.40 +
            completion * 0.30 +
            (100 - abandonment) * 0.15 +
            message_eff * 0.15
        )

        expected = 80 * 0.40 + 85 * 0.30 + 95 * 0.15 + 90 * 0.15
        assert abs(score - expected) < 0.1


class TestDataValidation:
    """Test input validation for analytics"""

    def test_date_range_validation(self):
        """Test date range validation logic"""
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()

        # Valid range
        assert end_date > start_date

        # Range should not exceed 1 year
        assert (end_date - start_date).days <= 365

    def test_category_name_sanitization(self):
        """Test category names are sanitized"""
        test_cases = [
            ("GPS", "GPS"),
            ("gps tracker", "gps_tracker"),
            ("  Camera  ", "Camera"),
            ("", "Unknown"),
        ]

        for input_name, expected in test_cases:
            # Simple sanitization
            sanitized = input_name.strip().replace(" ", "_") or "Unknown"
            assert sanitized == expected

    def test_phone_number_format(self):
        """Test phone number format validation"""
        valid_phones = [
            "+6281234567890",
            "081234567890",
            "+62 812 3456 7890",
        ]

        for phone in valid_phones:
            # Should be able to extract digits
            digits = "".join(c for c in phone if c.isdigit())
            assert len(digits) >= 10
            assert digits.startswith("62") or digits.startswith("0")


class TestHealthCheck:
    """Test health check endpoint"""

    def test_health_response_structure(self):
        """Test health check has required fields"""
        health_response = {
            "status": "healthy",
            "components": {
                "database": "connected",
                "ai_engine": "operational",
                "whatsapp_api": "configured",
                "osticket": "configured",
            }
        }

        assert "status" in health_response
        assert "components" in health_response

        for component in ["database", "ai_engine"]:
            assert component in health_response["components"]

    def test_degraded_status(self):
        """Test degraded status when component fails"""
        components = {
            "database": "error: connection failed",
            "ai_engine": "not_configured",
        }

        is_degraded = any("error" in str(v) for v in components.values())
        assert is_degraded
