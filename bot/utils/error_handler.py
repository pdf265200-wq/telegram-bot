"""
Advanced error handling utilities
"""

import functools
import logging
import traceback
import asyncio
from typing import Callable, Any, Optional, Type, Tuple, Dict
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import (
    TelegramError,
    NetworkError,
    TimedOut,
    RetryAfter,
    BadRequest,
    Forbidden,
    Unauthorized,
    ChatMigrated
)
from bot.config import Config

logger = logging.getLogger(__name__)

class ErrorHandler:
    """Advanced error handling decorators and utilities"""
    
    # Error types that should be retried
    RETRYABLE_ERRORS = (
        NetworkError,
        TimedOut,
        RetryAfter,
    )
    
    # Error messages for users
    USER_ERROR_MESSAGES = {
        Forbidden: "Bot doesn't have permission to perform this action.",
        BadRequest: "Invalid request. Please try again with different parameters.",
        ChatMigrated: "This chat has been migrated. Please use the new chat.",
        NetworkError: "Network error. Please try again later.",
        TimedOut: "Request timed out. Please try again.",
        RetryAfter: "Too many requests. Please wait a moment.",
    }
    
    @staticmethod
    def retry_on_error(
        max_retries: int = 3,
        delay: float = 1.0,
        backoff_factor: float = 2.0,
        exceptions: Tuple[Type[Exception], ...] = (NetworkError, TimedOut)
    ):
        """
        Decorator to retry function on specific errors
        
        Args:
            max_retries: Maximum number of retries
            delay: Initial delay between retries
            backoff_factor: Multiply delay by this factor after each retry
            exceptions: Exception types to retry on
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                last_exception = None
                current_delay = delay
                
                for attempt in range(max_retries + 1):
                    try:
                        return await func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        
                        if attempt < max_retries:
                            logger.warning(
                                f"Retry {attempt + 1}/{max_retries} for {func.__name__}: {e}"
                            )
                            await asyncio.sleep(current_delay)
                            current_delay *= backoff_factor
                        else:
                            logger.error(
                                f"All retries failed for {func.__name__}: {e}"
                            )
                
                raise last_exception
            
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                last_exception = None
                current_delay = delay
                
                for attempt in range(max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        
                        if attempt < max_retries:
                            logger.warning(
                                f"Retry {attempt + 1}/{max_retries} for {func.__name__}: {e}"
                            )
                            import time
                            time.sleep(current_delay)
                            current_delay *= backoff_factor
                        else:
                            logger.error(
                                f"All retries failed for {func.__name__}: {e}"
                            )
                
                raise last_exception
            
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper
        
        return decorator
    
    @staticmethod
    def handle_telegram_errors(
        func: Optional[Callable] = None,
        *,
        notify_admin: bool = True,
        log_traceback: bool = True
    ):
        """
        Decorator to handle Telegram API errors gracefully
        
        Args:
            func: The function to decorate
            notify_admin: Whether to notify admin on critical errors
            log_traceback: Whether to log the full traceback
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
                try:
                    return await func(update, context, *args, **kwargs)
                except RetryAfter as e:
                    logger.warning(f"Rate limited. Retry after {e.retry_after} seconds")
                    await asyncio.sleep(e.retry_after)
                    return await func(update, context, *args, **kwargs)
                except (Forbidden, Unauthorized) as e:
                    logger.warning(f"Permission error: {e}")
                    await ErrorHandler._notify_user(update, "permission_error")
                except BadRequest as e:
                    logger.error(f"Bad request: {e}")
                    await ErrorHandler._notify_user(update, "bad_request")
                except ChatMigrated as e:
                    logger.info(f"Chat migrated to {e.new_chat_id}")
                    await ErrorHandler._handle_chat_migration(update, e.new_chat_id)
                except TelegramError as e:
                    logger.error(f"Telegram error: {e}")
                    if log_traceback:
                        logger.debug(traceback.format_exc())
                    if notify_admin:
                        await ErrorHandler._notify_admin(context, e, update)
                    await ErrorHandler._notify_user(update, "general_error")
                except Exception as e:
                    logger.error(f"Unexpected error: {e}")
                    if log_traceback:
                        logger.debug(traceback.format_exc())
                    if notify_admin:
                        await ErrorHandler._notify_admin(context, e, update)
                    await ErrorHandler._notify_user(update, "unexpected_error")
            return wrapper
        return decorator
    
    @staticmethod
    async def _notify_user(update: Update, error_type: str):
        """Send error message to user"""
        messages = {
            'permission_error': "❌ Bot doesn't have permission to perform this action.",
            'bad_request': "❌ Invalid request. Please try again.",
            'general_error': "❌ An error occurred. Please try again later.",
            'unexpected_error': "❌ An unexpected error occurred. The error has been logged."
        }
        
        try:
            if update and update.effective_message:
                await update.effective_message.reply_text(
                    messages.get(error_type, messages['general_error'])
                )
        except:
            pass
    
    @staticmethod
    async def _notify_admin(context: ContextTypes.DEFAULT_TYPE, error: Exception, update: Update = None):
        """Notify admin about errors"""
        try:
            error_msg = (
                f"⚠️ *Error Alert*\n\n"
                f"*Type:* `{type(error).__name__}`\n"
                f"*Message:* `{str(error)[:200]}`\n"
                f"*Time:* `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n"
            )
            
            if update:
                error_msg += (
                    f"*User:* `{update.effective_user.id if update.effective_user else 'N/A'}`\n"
                    f"*Chat:* `{update.effective_chat.id if update.effective_chat else 'N/A'}`"
                )
            
            for admin_id in Config.ADMIN_IDS:
                await context.bot.send_message(chat_id=admin_id, text=error_msg)
        except:
            pass
    
    @staticmethod
    async def _handle_chat_migration(update: Update, new_chat_id: int):
        """Handle chat migration"""
        try:
            if update and update.effective_message:
                await update.effective_message.reply_text(
                    f"This chat has been migrated. Please use chat ID: {new_chat_id}"
                )
        except:
            pass
    
    @staticmethod
    def safe_execute(func: Callable) -> Callable:
        """
        Execute function safely with full error handling
        
        This is a general-purpose wrapper for any bot operation
        """
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}")
                logger.debug(traceback.format_exc())
                return None
        return wrapper


class PerformanceMonitor:
    """Monitor function performance"""
    
    def __init__(self):
        self.execution_times: Dict[str, list] = {}
        self.error_counts: Dict[str, int] = {}
    
    def monitor(self, func: Callable) -> Callable:
        """Decorator to monitor function performance"""
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            func_name = func.__name__
            start_time = datetime.now()
            
            try:
                result = await func(*args, **kwargs)
                
                execution_time = (datetime.now() - start_time).total_seconds()
                if func_name not in self.execution_times:
                    self.execution_times[func_name] = []
                self.execution_times[func_name].append(execution_time)
                
                return result
                
            except Exception as e:
                self.error_counts[func_name] = self.error_counts.get(func_name, 0) + 1
                raise
        
        return wrapper
    
    def get_stats(self) -> Dict[str, Dict]:
        """Get performance statistics"""
        stats = {}
        for func_name, times in self.execution_times.items():
            if times:
                stats[func_name] = {
                    'avg_execution_time': sum(times) / len(times),
                    'min_execution_time': min(times),
                    'max_execution_time': max(times),
                    'total_calls': len(times),
                    'errors': self.error_counts.get(func_name, 0)
                }
        return stats

# Create global instances
error_handler = ErrorHandler()
performance_monitor = PerformanceMonitor()
