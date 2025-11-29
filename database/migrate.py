#!/usr/bin/env python3
"""Database migration script for Supabase."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.logger import logger

def run_migrations():
    """Run all SQL migrations in order."""
    migrations_dir = Path(__file__).parent / "migrations"
    migration_files = sorted(migrations_dir.glob("*.sql"))
    
    if not migration_files:
        logger.warning("No migration files found")
        return
    
    logger.info("=== Database Migrations ===\n")
    
    for migration_file in migration_files:
        logger.info(f"Migration: {migration_file.name}")
        sql = migration_file.read_text()
        print(sql)
        print("\n" + "="*80 + "\n")
    
    logger.info("To apply these migrations:")
    logger.info("1. Copy the SQL above")
    logger.info("2. Go to Supabase Dashboard > SQL Editor")
    logger.info("3. Paste and run the SQL")

if __name__ == "__main__":
    run_migrations()
