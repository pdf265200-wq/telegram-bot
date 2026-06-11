"""
Tests for database manager
"""

import pytest
from datetime import datetime, timedelta
from bot.database.db_manager import DatabaseManager
from bot.database.models import User, UsageStat, BroadcastMessage

class TestDatabaseManager:
    """Test database manager functionality"""
    
    def test_create_user(self, db_manager):
        """Test user creation"""
        user = db_manager.get_or_create_user(
            user_id=12345,
            username="testuser",
            first_name="Test",
            last_name="User"
        )
        
        assert user is not None
        assert user.user_id == 12345
        assert user.username == "testuser"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert not user.is_banned
    
    def test_get_existing_user(self, db_manager):
        """Test getting existing user"""
        # Create user first
        db_manager.get_or_create_user(user_id=12345)
        
        # Get user again
        user = db_manager.get_or_create_user(
            user_id=12345,
            username="updated_user"
        )
        
        assert user is not None
        assert user.user_id == 12345
        assert user.username == "updated_user"
    
    def test_ban_unban_user(self, db_manager):
        """Test ban and unban functionality"""
        user_id = 12345
        db_manager.get_or_create_user(user_id=user_id)
        
        # Ban user
        assert db_manager.ban_user(user_id)
        assert db_manager.is_user_banned(user_id)
        
        # Unban user
        assert db_manager.unban_user(user_id)
        assert not db_manager.is_user_banned(user_id)
    
    def test_log_usage(self, db_manager):
        """Test logging command usage"""
        user_id = 12345
        db_manager.get_or_create_user(user_id=user_id)
        
        # Log usage
        db_manager.log_usage(user_id, 'test_command')
        
        # Verify stats
        stats = db_manager.get_command_stats()
        commands = {cmd: count for cmd, count in stats}
        assert 'test_command' in commands
        assert commands['test_command'] >= 1
    
    def test_get_total_users(self, db_manager):
        """Test getting total user count"""
        # Create multiple users
        for i in range(5):
            db_manager.get_or_create_user(user_id=1000 + i)
        
        total = db_manager.get_total_users()
        assert total == 5
    
    def test_get_active_users_today(self, db_manager):
        """Test getting today's active users"""
        user_id = 12345
        
        # Create user and log activity
        user = db_manager.get_or_create_user(user_id=user_id)
        user.last_activity = datetime.utcnow()
        db_manager.session.commit()
        
        active_today = db_manager.get_active_users_today()
        assert active_today >= 1
    
    def test_get_daily_stats(self, db_manager):
        """Test getting daily statistics"""
        user_id = 12345
        db_manager.get_or_create_user(user_id=user_id)
        
        # Log usage for today
        db_manager.log_usage(user_id, 'test_command')
        
        stats = db_manager.get_daily_stats(days=7)
        today = datetime.utcnow().strftime('%Y-%m-%d')
        assert today in stats
        assert stats[today] >= 1
    
    def test_broadcast_logging(self, db_manager):
        """Test broadcast message logging"""
        admin_id = 123456789
        message = "Test broadcast"
        recipients = 10
        
        db_manager.add_broadcast(admin_id, message, recipients)
        
        # Verify broadcast was logged
        broadcasts = db_manager.session.query(BroadcastMessage).all()
        assert len(broadcasts) == 1
        assert broadcasts[0].admin_id == admin_id
        assert broadcasts[0].message_text == message
        assert broadcasts[0].recipients_count == recipients
