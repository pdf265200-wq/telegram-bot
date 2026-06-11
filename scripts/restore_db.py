#!/usr/bin/env python
"""
Database restore script
"""

import sys
import shutil
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bot.config import Config

def restore_database(backup_file: str):
    """Restore database from backup"""
    try:
        source = Path(backup_file)
        if not source.exists():
            print(f"Backup file not found: {backup_file}")
            return False
        
        # Target database
        target = Path(Config.DATA_DIR) / 'bot.db'
        
        # Create backup of current database
        if target.exists():
            current_backup = target.with_suffix('.db.bak')
            shutil.copy2(target, current_backup)
            print(f"Current database backed up to {current_backup}")
        
        # Restore from backup
        shutil.copy2(source, target)
        print(f"Database restored from {source}")
        
        return True
        
    except Exception as e:
        print(f"Restore failed: {e}")
        return False

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python restore_db.py <backup_file>")
        sys.exit(1)
    
    restore_database(sys.argv[1])
