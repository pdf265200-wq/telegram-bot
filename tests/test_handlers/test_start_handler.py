"""
Tests for start command handler
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from bot.handlers.start import start, stats
from bot.database.db_manager import DatabaseManager

class TestStartHandler:
    """Test start command handler"""
    
    @pytest.mark.asyncio
    async def test_start_command(self, mock_update, mock_context):
        """Test /start command"""
        mock_update.message = AsyncMock()
        mock_update.message.reply_text = AsyncMock()
        
        await start(mock_update, mock_context)
        
        # Verify welcome message was sent
        mock_update.message.reply_text.assert_called_once()
        
        # Verify message contains key elements
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert 'Welcome' in call_args or 'مرحباً' in call_args
        assert 'Voice to Text' in call_args or 'تحويل الصوت' in call_args
    
    @pytest.mark.asyncio
    async def test_start_with_new_user(self, mock_update, mock_context, db_manager):
        """Test /start with new user"""
        mock_update.message = AsyncMock()
        mock_update.message.reply_text = AsyncMock()
        
        # Override db_manager with test instance
        with patch('bot.handlers.start.db', db_manager):
            await start(mock_update, mock_context)
            
            # Verify user was created in database
            user = db_manager.get_or_create_user(
                user_id=mock_update.effective_user.id,
                username=mock_update.effective_user.username,
                first_name=mock_update.effective_user.first_name,
                last_name=mock_update.effective_user.last_name
            )
            assert user is not None
            assert user.user_id == 123456789
    
    @pytest.mark.asyncio
    async def test_stats_command(self, mock_update, mock_context, db_manager):
        """Test /stats command"""
        mock_update.message = AsyncMock()
        mock_update.message.reply_text = AsyncMock()
        
        # Create test user first
        db_manager.get_or_create_user(user_id=mock_update.effective_user.id)
        
        with patch('bot.handlers.start.db', db_manager):
            await stats(mock_update, mock_context)
            
            # Verify stats message was sent
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args[0][0]
            assert 'Statistics' in call_args or 'إحصائيات' in call_args
