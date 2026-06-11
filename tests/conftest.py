"""
Pytest configuration and fixtures
"""

import pytest
import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update, Message, User, Chat
from telegram.ext import ContextTypes, Application
from bot.config import Config
from bot.database.db_manager import DatabaseManager
from bot.database.models import Base, engine, Session

# Use test database
os.environ['DATABASE_URL'] = 'sqlite:///test_bot.db'
os.environ['BOT_TOKEN'] = 'test_token'
os.environ['ADMIN_IDS'] = '123456789'

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def db_manager():
    """Create a test database manager"""
    # Create all tables
    Base.metadata.create_all(engine)
    
    db = DatabaseManager()
    yield db
    
    # Clean up
    Base.metadata.drop_all(engine)

@pytest.fixture
def mock_update():
    """Create a mock Telegram Update"""
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock(spec=User)
    update.effective_user.id = 123456789
    update.effective_user.username = "testuser"
    update.effective_user.first_name = "Test"
    update.effective_user.last_name = "User"
    update.effective_chat = MagicMock(spec=Chat)
    update.effective_chat.id = 123456789
    update.effective_message = MagicMock(spec=Message)
    update.effective_message.message_id = 1
    update.effective_message.text = "Test message"
    return update

@pytest.fixture
def mock_context():
    """Create a mock Context"""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot = MagicMock()
    context.bot.send_message = AsyncMock()
    context.bot.send_photo = AsyncMock()
    context.bot.send_document = AsyncMock()
    context.bot.send_voice = AsyncMock()
    context.user_data = {}
    context.chat_data = {}
    context.args = []
    return context

@pytest.fixture
def mock_application():
    """Create a mock Application"""
    app = MagicMock(spec=Application)
    app.bot = MagicMock()
    return app

@pytest.fixture
def clean_temp_dir():
    """Clean temporary directory before and after tests"""
    import shutil
    from pathlib import Path
    
    temp_dir = Path('temp')
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    
    yield
    
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
