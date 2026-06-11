#!/usr/bin/env python
"""
Database backup script
"""

import os
import sys
import shutil
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bot.config import Config

def backup_database():
    """Create database backup"""
    try:
        # Source database
        source = Path(Config.DATA_DIR) / 'bot.db'
        
        if not source.exists():
            print(f"Database not found at {source}")
            return False
        
        # Create backup directory
        backup_dir = Path(Config.DATA_DIR) / 'backups'
        backup_dir.mkdir(exist_ok=True)
        
        # Create backup with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = backup_dir / f'bot_backup_{timestamp}.db'
        
        shutil.copy2(source, backup_file)
        print(f"Database backed up to {backup_file}")
        
        # Clean old backups (keep last 7)
        backups = sorted(backup_dir.glob('bot_backup_*.db'))
        if len(backups) > 7:
            for old_backup in backups[:-7]:
                old_backup.unlink()
                print(f"Removed old backup: {old_backup}")
        
        return True
        
    except Exception as e:
        print(f"Backup failed: {e}")
        return False

if __name__ == '__main__':
    backup_database()
