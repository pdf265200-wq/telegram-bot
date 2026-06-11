"""
Anti-spam middleware
"""

from datetime import datetime, timedelta
from collections import defaultdict
from typing import Tuple, Optional
from bot.middleware.rate_limiter import RateLimiter
from bot.database.db_manager import DatabaseManager
from bot.database.models import User, Session
from bot.config import Config
import logging

logger = logging.getLogger(__name__)

class AntiSpamMiddleware:
    """Middleware for preventing spam and abuse"""
    
    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.db = DatabaseManager()
        self.blocked_users = set()
        self.warning_counts = defaultdict(int)
        self.last_warning = defaultdict(lambda: datetime.min)
        
    async def check_user(self, user_id: int) -> Tuple[bool, Optional[str]]:
        """
        Check if user is allowed to use the bot
        
        Returns:
            Tuple of (is_allowed, error_message)
        """
        # Skip checks for admins
        if Config.is_admin(user_id):
            return True, None
        
        # Check if user is blocked in memory
        if user_id in self.blocked_users:
            return False, "You are temporarily blocked due to excessive requests."
        
        # Check if user is banned in database
        if self.db.is_user_banned(user_id):
            return False, "You are banned from using this bot. Contact admin if you think this is a mistake."
        
        # Check rate limit
        if Config.ENABLE_RATE_LIMITING:
            if not self.rate_limiter.is_allowed(user_id):
                # Increment warning count
                self.warning_counts[user_id] += 1
                now = datetime.now()
                
                # Reset warning count if last warning was more than 5 minutes ago
                if now - self.last_warning[user_id] > timedelta(minutes=5):
                    self.warning_counts[user_id] = 1
                
                self.last_warning[user_id] = now
                
                # Block user if too many warnings
                if self.warning_counts[user_id] >= 3:
                    self.blocked_users.add(user_id)
                    logger.warning(f"User {user_id} temporarily blocked for spamming")
                    return False, (
                        "⚠️ *Temporary Block*\n\n"
                        "You've been temporarily blocked for 5 minutes due to excessive requests.\n"
                        "Please wait before trying again."
                    )
                
                # Calculate wait time
                wait_time = Config.RATE_LIMIT_SECONDS * self.warning_counts[user_id]
                
                return False, (
                    "⚠️ *Rate Limit Exceeded*\n\n"
                    f"Please wait {wait_time} seconds before sending another request.\n"
                    f"Warning {self.warning_counts[user_id]}/3"
                )
        
        # Reset warning count for valid requests
        if user_id in self.warning_counts:
            if datetime.now() - self.last_warning[user_id] > timedelta(minutes=5):
                self.warning_counts[user_id] = 0
        
        return True, None
    
    def block_user(self, user_id: int, duration_minutes: int = 5):
        """Temporarily block a user"""
        self.blocked_users.add(user_id)
        logger.info(f"User {user_id} blocked for {duration_minutes} minutes")
        
        # Schedule unblock
        import asyncio
        async def unblock():
            await asyncio.sleep(duration_minutes * 60)
            self.blocked_users.discard(user_id)
            logger.info(f"User {user_id} automatically unblocked")
        
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(unblock())
        except:
            pass
    
    def unblock_user(self, user_id: int):
        """Manually unblock a user"""
        self.blocked_users.discard(user_id)
        logger.info(f"User {user_id} manually unblocked")
    
    def get_stats(self) -> dict:
        """Get anti-spam statistics"""
        return {
            'blocked_users': len(self.blocked_users),
            'warned_users': len(self.warning_counts),
            'total_warnings': sum(self.warning_counts.values())
        }
