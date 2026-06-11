"""
Tests for anti-spam middleware
"""

import pytest
import asyncio
from unittest.mock import patch
from bot.middleware.anti_spam import AntiSpamMiddleware
from bot.config import Config

class TestAntiSpamMiddleware:
    """Test anti-spam functionality"""
    
    @pytest.fixture
    def anti_spam(self):
        return AntiSpamMiddleware()
    
    @pytest.mark.asyncio
    async def test_admin_bypass(self, anti_spam):
        """Test that admins bypass spam checks"""
        admin_id = Config.ADMIN_IDS[0]
        is_allowed, message = await anti_spam.check_user(admin_id)
        
        assert is_allowed
        assert message is None
    
    @pytest.mark.asyncio
    async def test_normal_user_allowed(self, anti_spam):
        """Test that normal users are initially allowed"""
        is_allowed, message = await anti_spam.check_user(99999)
        
        assert is_allowed
        assert message is None
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, anti_spam):
        """Test rate limiting functionality"""
        user_id = 99999
        
        # Send multiple requests quickly
        for _ in range(Config.RATE_LIMIT_MAX_REQUESTS + 2):
            is_allowed, message = await anti_spam.check_user(user_id)
        
        # User should be rate limited
        assert not is_allowed
        assert message is not None
        assert 'Rate Limit' in message or 'rate' in message.lower()
    
    @pytest.mark.asyncio
    async def test_temporary_block(self, anti_spam):
        """Test temporary blocking"""
        user_id = 99999
        
        # Generate warnings to trigger block
        for _ in range(10):
            await anti_spam.check_user(user_id)
        
        # User should be blocked
        is_allowed, message = await anti_spam.check_user(user_id)
        assert not is_allowed
        assert 'block' in message.lower()
    
    @pytest.mark.asyncio
    async def test_warning_reset(self, anti_spam):
        """Test that warnings reset after time"""
        user_id = 99999
        
        # Send requests until warned
        for _ in range(Config.RATE_LIMIT_MAX_REQUESTS + 1):
            await anti_spam.check_user(user_id)
        
        # Manually reset last warning to old date
        from datetime import datetime, timedelta
        anti_spam.last_warning[user_id] = datetime.now() - timedelta(minutes=10)
        anti_spam.warning_counts[user_id] = 2
        
        # Next request should be allowed and reset warnings
        is_allowed, message = await anti_spam.check_user(user_id)
        assert is_allowed
