"""
Executable FastAPI auth tests for /health/llm-budget endpoint.
Proves member => 403, owner/admin => 200 with mocked budget summary.
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException

from app.infrastructure.auth.clerk import AuthContext


class TestHealthLLMBudgetAuth:
    """Test /health/llm-budget authorization with mock Redis."""

    @pytest.fixture
    def mock_budget(self):
        return {
            "status": "ok",
            "llm_enabled": True,
            "daily_cost": 0.01,
            "daily_limit": 0.50,
            "daily_pct": 2.0,
            "monthly_cost": 0.05,
            "monthly_limit": 10.00,
            "monthly_pct": 0.5,
            "flash_model": "deepseek-chat",
            "pro_model": "deepseek-reasoner",
        }

    def test_member_returns_403(self, mock_budget):
        """Member role => 403 Forbidden (Admin access required)."""
        from app.presentation.api.v1.routes.health_llm import health_llm_budget

        member_ctx = AuthContext(
            user_id=1,
            email="member@test.com",
            role="member",
            organization_id=1,
            organization_slug="test-org",
            permissions=["companies:read"],
        )

        with patch(
            "app.application.llm.gateway.get_budget_summary",
            new=AsyncMock(return_value=mock_budget),
        ):
            try:
                asyncio.run(health_llm_budget(ctx=member_ctx))
                pytest.fail("Expected HTTPException 403 for member")
            except HTTPException as e:
                assert e.status_code == 403, f"Expected 403, got {e.status_code}"
                assert "Admin" in e.detail, f"Expected admin message, got: {e.detail}"

    def test_admin_returns_200(self, mock_budget):
        """Admin role => 200 with budget data."""
        from app.presentation.api.v1.routes.health_llm import health_llm_budget

        admin_ctx = AuthContext(
            user_id=2,
            email="admin@test.com",
            role="admin",
            organization_id=1,
            organization_slug="test-org",
            permissions=["companies:read", "companies:write"],
        )

        with patch(
            "app.application.llm.gateway.get_budget_summary",
            new=AsyncMock(return_value=mock_budget),
        ):
            result = asyncio.run(health_llm_budget(ctx=admin_ctx))
            assert result["status"] == "ok"
            assert result["daily_cost"] == 0.01
            assert result["monthly_cost"] == 0.05

    def test_owner_returns_200(self, mock_budget):
        """Owner role => 200 with budget data."""
        from app.presentation.api.v1.routes.health_llm import health_llm_budget

        owner_ctx = AuthContext(
            user_id=3,
            email="owner@test.com",
            role="owner",
            organization_id=1,
            organization_slug="test-org",
            permissions=["companies:read", "companies:write"],
        )

        with patch(
            "app.application.llm.gateway.get_budget_summary",
            new=AsyncMock(return_value=mock_budget),
        ):
            result = asyncio.run(health_llm_budget(ctx=owner_ctx))
            assert result["status"] == "ok"
            assert result["daily_cost"] == 0.01
