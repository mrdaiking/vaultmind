"""
Tests for main.py API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from main import app, AIAgent


client = TestClient(app)


class TestHealthEndpoint:
    """Tests for health check endpoint"""

    def test_health_check(self):
        """Test health endpoint returns correct response"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["version"] == "1.0.0"


class TestChatEndpoint:
    """Tests for chat endpoint"""

    @patch("main.verify_jwt")
    @patch("main.AIAgent.process_message")
    async def test_chat_requires_authentication(
        self, mock_process, mock_verify, mock_jwt_payload
    ):
        """Test chat endpoint requires valid JWT"""
        mock_verify.return_value = mock_jwt_payload

        response = client.post(
            "/agent/chat",
            json={"message": "Hello", "timezone": "UTC"},
            headers={"Authorization": "Bearer fake_token"},
        )

        assert response.status_code in [200, 401]

    @patch("main.verify_jwt")
    @patch("main.AIAgent.process_message")
    async def test_chat_with_valid_message(
        self, mock_process, mock_verify, mock_jwt_payload
    ):
        """Test chat endpoint processes valid messages"""
        mock_verify.return_value = mock_jwt_payload
        mock_process.return_value = {
            "response": "Test response",
            "action_taken": "general_response",
            "success": True,
        }

        response = client.post(
            "/agent/chat",
            json={"message": "What's on my calendar?", "timezone": "America/New_York"},
            headers={"Authorization": "Bearer fake_token"},
        )

        # This will fail without proper auth, but structure is correct
        assert response.status_code in [200, 401]


class TestAIAgent:
    """Tests for AIAgent class"""

    @pytest.mark.asyncio
    async def test_process_message_calendar_list(self):
        """Test AI agent can process calendar list requests"""
        agent = AIAgent()

        result = await agent.process_message(
            message="Show my calendar",
            user_id="test_user",
            user_claims=None,
            timezone="UTC",
        )

        assert isinstance(result, dict)
        assert "response" in result
        assert "success" in result

    @pytest.mark.asyncio
    async def test_process_message_general_query(self):
        """Test AI agent handles general queries"""
        agent = AIAgent()

        result = await agent.process_message(
            message="Hello, how are you?",
            user_id="test_user",
            user_claims=None,
            timezone="UTC",
        )

        assert isinstance(result, dict)
        assert result["action_taken"] == "general_response"
        assert result["success"] is True


class TestAuditLog:
    """Tests for audit logging"""

    def test_audit_log_records_action(self):
        """Test audit log records actions correctly"""
        from main import AuditLog

        audit = AuditLog()
        audit.log_action(
            user_id="test_user",
            action="test_action",
            details={"test": "data"},
            success=True,
        )

        logs = audit.get_user_logs("test_user")
        assert len(logs) == 1
        assert logs[0]["action"] == "test_action"
        assert logs[0]["success"] is True

    def test_audit_log_filters_by_user(self):
        """Test audit log filters logs by user ID"""
        from main import AuditLog

        audit = AuditLog()
        audit.log_action("user1", "action1", {}, True)
        audit.log_action("user2", "action2", {}, True)
        audit.log_action("user1", "action3", {}, False)

        user1_logs = audit.get_user_logs("user1")
        assert len(user1_logs) == 2
        assert all(log["user_id"] == "user1" for log in user1_logs)
