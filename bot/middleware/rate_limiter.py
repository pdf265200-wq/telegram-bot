"""
Rate limiter middleware
"""

from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List
from bot.config import Config
import threading
import time
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Rate limiter with different strategies:
    - Fixed window
    - Sliding window (default)
    - Token bucket
    """
    
    def __init__(self, strategy: str = 'sliding_window'):
        self.strategy = strategy
        self.requests: Dict[int, List[datetime]] = defaultdict(list)
        self.tokens: Dict[int, float] = defaultdict(lambda: Config.RATE_LIMIT_MAX_REQUESTS)
        self.last_refill: Dict[int, float] = defaultdict(time.time)
        self.lock = threading.Lock()
        
    def is_allowed(self, user_id: int) -> bool:
        """
        Check if request is allowed
        
        Returns:
            True if request is allowed, False otherwise
        """
        if self.strategy == 'fixed_window':
            return self._fixed_window_check(user_id)
        elif self.strategy == 'sliding_window':
            return self._sliding_window_check(user_id)
        elif self.strategy == 'token_bucket':
            return self._token_bucket_check(user_id)
        else:
            return True
    
    def _fixed_window_check(self, user_id: int) -> bool:
        """Fixed window rate limiting"""
        now = datetime.now()
        window_start = now.replace(second=0, microsecond=0)
        
        with self.lock:
            user_requests = self.requests[user_id]
            
            # Clean old requests
            user_requests = [req for req in user_requests if req >= window_start]
            self.requests[user_id] = user_requests
            
            if len(user_requests) >= Config.RATE_LIMIT_MAX_REQUESTS:
                return False
            
            user_requests.append(now)
            return True
    
    def _sliding_window_check(self, user_id: int) -> bool:
        """Sliding window rate limiting"""
        now = datetime.now()
        window_start = now - timedelta(seconds=Config.RATE_LIMIT_SECONDS)
        
        with self.lock:
            user_requests = self.requests[user_id]
            
            # Remove requests outside the window
            user_requests = [req for req in user_requests if req > window_start]
            self.requests[user_id] = user_requests
            
            # Check burst limit
            if len(user_requests) >= Config.RATE_LIMIT_BURST:
                return False
            
            # Check rate limit
            if len(user_requests) >= Config.RATE_LIMIT_MAX_REQUESTS:
                # Add to burst if not exceeded
                if len(user_requests) < Config.RATE_LIMIT_BURST:
                    user_requests.append(now)
                return False
            
            user_requests.append(now)
            return True
    
    def _token_bucket_check(self, user_id: int) -> bool:
        """Token bucket rate limiting"""
        now = time.time()
        
        with self.lock:
            # Refill tokens
            time_passed = now - self.last_refill[user_id]
            new_tokens = time_passed * (Config.RATE_LIMIT_MAX_REQUESTS / Config.RATE_LIMIT_SECONDS)
            self.tokens[user_id] = min(
                Config.RATE_LIMIT_BURST,
                self.tokens[user_id] + new_tokens
            )
            self.last_refill[user_id] = now
            
            # Check if token available
            if self.tokens[user_id] >= 1:
                self.tokens[user_id] -= 1
                return True
            
            return False
    
    def get_user_stats(self, user_id: int) -> dict:
        """Get rate limit statistics for a user"""
        now = datetime.now()
        user_requests = self.requests.get(user_id, [])
        recent_requests = [req for req in user_requests if req > now - timedelta(minutes=1)]
        
        return {
            'requests_last_minute': len(recent_requests),
            'total_requests': len(user_requests),
            'tokens_available': self.tokens.get(user_id, 0),
            'is_limited': not self.is_allowed(user_id)
        }
    
    def reset_user(self, user_id: int):
        """Reset rate limit for a user"""
        with self.lock:
            self.requests[user_id] = []
            self.tokens[user_id] = Config.RATE_LIMIT_MAX_REQUESTS
            self.last_refill[user_id] = time.time()
            logger.info(f"Rate limit reset for user {user_id}")
    
    def cleanup(self):
        """Clean up old request data"""
        now = datetime.now()
        with self.lock:
            for user_id in list(self.requests.keys()):
                self.requests[user_id] = [
                    req for req in self.requests[user_id]
                    if req > now - timedelta(hours=1)
                ]
                if not self.requests[user_id]:
                    del self.requests[user_id]
                    del self.tokens[user_id]
                    del self.last_refill[user_id]
