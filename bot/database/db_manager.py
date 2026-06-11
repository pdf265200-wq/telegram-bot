from sqlalchemy import func
from datetime import datetime, timedelta
from bot.database.models import User, UsageStat, BroadcastMessage, Session, init_db
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        init_db()
        self.session = Session()
    
    def get_or_create_user(self, user_id, username=None, first_name=None, last_name=None):
        """Get existing user or create new one"""
        user = self.session.query(User).filter_by(user_id=user_id).first()
        if not user:
            user = User(
                user_id=user_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            self.session.add(user)
            self.session.commit()
            logger.info(f"New user created: {user_id}")
        else:
            user.last_activity = datetime.utcnow()
            if username:
                user.username = username
            if first_name:
                user.first_name = first_name
            if last_name:
                user.last_name = last_name
            self.session.commit()
        return user
    
    def is_user_banned(self, user_id):
        """Check if user is banned"""
        user = self.session.query(User).filter_by(user_id=user_id).first()
        return user and user.is_banned
    
    def ban_user(self, user_id):
        """Ban a user"""
        user = self.session.query(User).filter_by(user_id=user_id).first()
        if user:
            user.is_banned = True
            self.session.commit()
            return True
        return False
    
    def unban_user(self, user_id):
        """Unban a user"""
        user = self.session.query(User).filter_by(user_id=user_id).first()
        if user:
            user.is_banned = False
            self.session.commit()
            return True
        return False
    
    def log_usage(self, user_id, command, success=True):
        """Log command usage"""
        stat = UsageStat(user_id=user_id, command=command, success=success)
        self.session.add(stat)
        
        # Update user request count
        user = self.session.query(User).filter_by(user_id=user_id).first()
        if user:
            user.total_requests += 1
            user.last_activity = datetime.utcnow()
        
        self.session.commit()
    
    def get_total_users(self):
        """Get total number of users"""
        return self.session.query(User).count()
    
    def get_active_users_today(self):
        """Get number of active users today"""
        today = datetime.utcnow().date()
        return self.session.query(User).filter(
            func.date(User.last_activity) == today
        ).count()
    
    def get_daily_stats(self, days=7):
        """Get daily usage statistics"""
        stats = {}
        for i in range(days):
            date = (datetime.utcnow() - timedelta(days=i)).date()
            count = self.session.query(UsageStat).filter(
                func.date(UsageStat.timestamp) == date
            ).count()
            stats[date.strftime('%Y-%m-%d')] = count
        return stats
    
    def get_command_stats(self):
        """Get command usage statistics"""
        return self.session.query(
            UsageStat.command, func.count(UsageStat.id)
        ).group_by(UsageStat.command).all()
    
    def add_broadcast(self, admin_id, message_text, recipients_count):
        """Log broadcast message"""
        broadcast = BroadcastMessage(
            admin_id=admin_id,
            message_text=message_text,
            recipients_count=recipients_count
        )
        self.session.add(broadcast)
        self.session.commit()
    
    def get_all_users(self):
        """Get all users"""
        return self.session.query(User).all()
