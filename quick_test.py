#!/usr/bin/env python
"""Quick essential tests before deployment"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from bot.config import Config
from bot.database.db_manager import DatabaseManager
from bot.services.qr_service import QRService
from bot.middleware.anti_spam import AntiSpamMiddleware

async def quick_tests():
    """Run critical tests only"""
    print("🔍 Running essential tests...")
    errors = []
    
    # Test 1: Configuration
    print("1. Testing configuration...")
    try:
        if not Config.BOT_TOKEN or Config.BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
            print("   ⚠️  BOT_TOKEN not set (expected for testing)")
        assert Config.ADMIN_IDS, "❌ ADMIN_IDS missing!"
        print("   ✅ Configuration valid")
    except Exception as e:
        errors.append(f"Config: {e}")
        print(f"   ❌ {e}")
    
    # Test 2: Database
    print("2. Testing database...")
    try:
        db = DatabaseManager()
        test_user = db.get_or_create_user(999999)
        assert test_user, "❌ Cannot create user!"
        print("   ✅ Database working")
    except Exception as e:
        errors.append(f"Database: {e}")
        print(f"   ❌ {e}")
    
    # Test 3: QR Service
    print("3. Testing QR generator...")
    try:
        qr = QRService()
        qr_code, error = qr.generate_qr("test")
        assert qr_code and not error, f"❌ QR failed: {error}"
        print("   ✅ QR generator working")
    except Exception as e:
        errors.append(f"QR: {e}")
        print(f"   ❌ {e}")
    
    # Test 4: Anti-spam
    print("4. Testing anti-spam...")
    try:
        anti_spam = AntiSpamMiddleware()
        allowed, _ = await anti_spam.check_user(999999)
        assert allowed, "❌ Anti-spam blocking!"
        print("   ✅ Anti-spam working")
    except Exception as e:
        errors.append(f"Anti-spam: {e}")
        print(f"   ❌ {e}")
    
    if errors:
        print(f"\n💥 {len(errors)} test(s) failed!")
        return False
    
    print("\n🎉 All essential tests passed! Bot is ready for deployment.")
    return True

if __name__ == '__main__':
    success = asyncio.run(quick_tests())
    sys.exit(0 if success else 1)
