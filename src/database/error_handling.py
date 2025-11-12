"""
Error Handling and Logging System

This module provides comprehensive error handling including:
- Graceful error handling for scraping failures
- Database transaction management with rollback
- Comprehensive error logging
- Recovery procedures for failed operations
"""

import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, Any, Tuple, List
from functools import wraps
import sqlite3


# Setup logging
LOG_DIR = Path(__file__).parent.parent.parent / 'logs'
LOG_DIR.mkdir(exist_ok=True)

# Configure logger
logger = logging.getLogger('EventManager')
logger.setLevel(logging.DEBUG)

# File handler for all logs
file_handler = logging.FileHandler(
    LOG_DIR / f'event_manager_{datetime.now().strftime("%Y%m%d")}.log'
)
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
file_handler.setFormatter(file_formatter)

# File handler for errors only
error_handler = logging.FileHandler(
    LOG_DIR / f'errors_{datetime.now().strftime("%Y%m%d")}.log'
)
error_handler.setLevel(logging.ERROR)
error_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s\n%(exc_info)s'
)
error_handler.setFormatter(error_formatter)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)

logger.addHandler(file_handler)
logger.addHandler(error_handler)
logger.addHandler(console_handler)


class DatabaseError(Exception):
    """Custom exception for database errors"""
    pass


class ScrapingError(Exception):
    """Custom exception for scraping errors"""
    pass


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


def with_error_handling(operation_name: str = "Operation"):
    """
    Decorator for comprehensive error handling
    
    Args:
        operation_name: Name of the operation for logging
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                logger.info(f"Starting {operation_name}: {func.__name__}")
                result = func(*args, **kwargs)
                logger.info(f"Completed {operation_name}: {func.__name__}")
                return result
            
            except ValidationError as e:
                logger.error(f"Validation error in {func.__name__}: {str(e)}")
                logger.debug(traceback.format_exc())
                raise
            
            except ScrapingError as e:
                logger.error(f"Scraping error in {func.__name__}: {str(e)}")
                logger.debug(traceback.format_exc())
                raise
            
            except DatabaseError as e:
                logger.error(f"Database error in {func.__name__}: {str(e)}")
                logger.debug(traceback.format_exc())
                raise
            
            except Exception as e:
                logger.critical(
                    f"Unexpected error in {func.__name__}: {type(e).__name__}: {str(e)}"
                )
                logger.debug(traceback.format_exc())
                raise
        
        return wrapper
    return decorator


class DatabaseTransaction:
    """Context manager for database transactions with automatic rollback"""
    
    def __init__(self, connection: sqlite3.Connection, operation_name: str = "Database Operation"):
        self.conn = connection
        self.operation_name = operation_name
        self.cursor = None
    
    def __enter__(self):
        """Start transaction"""
        logger.debug(f"Starting transaction: {self.operation_name}")
        self.cursor = self.conn.cursor()
        return self.cursor
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Commit or rollback transaction"""
        if exc_type is None:
            # No exception, commit
            try:
                self.conn.commit()
                logger.debug(f"Transaction committed: {self.operation_name}")
            except Exception as e:
                logger.error(f"Error committing transaction: {str(e)}")
                self.conn.rollback()
                logger.info(f"Transaction rolled back: {self.operation_name}")
                raise DatabaseError(f"Failed to commit transaction: {str(e)}")
        else:
            # Exception occurred, rollback
            self.conn.rollback()
            logger.warning(
                f"Transaction rolled back due to {exc_type.__name__}: {self.operation_name}"
            )
            logger.debug(f"Error details: {exc_val}")
        
        return False  # Re-raise exception


class ScrapingErrorHandler:
    """Handles errors during web scraping with retry logic"""
    
    def __init__(self, max_retries: int = 3, retry_delay: int = 5):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.failed_urls = []
    
    def scrape_with_retry(
        self,
        scrape_func: Callable,
        url: str,
        *args,
        **kwargs
    ) -> Optional[Any]:
        """
        Execute scraping function with retry logic
        
        Args:
            scrape_func: Function to execute
            url: URL being scraped
            *args, **kwargs: Arguments for scrape_func
        
        Returns:
            Result from scrape_func or None if all retries failed
        """
        import time
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Scraping attempt {attempt + 1}/{self.max_retries}: {url}")
                result = scrape_func(url, *args, **kwargs)
                
                if attempt > 0:
                    logger.info(f"Successfully scraped after {attempt + 1} attempts: {url}")
                
                return result
            
            except Exception as e:
                logger.warning(
                    f"Scraping attempt {attempt + 1} failed for {url}: {type(e).__name__}: {str(e)}"
                )
                
                if attempt < self.max_retries - 1:
                    logger.info(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"All scraping attempts failed for {url}")
                    self.failed_urls.append({
                        'url': url,
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # Don't raise exception, allow scraping to continue
                    return None
        
        return None
    
    def get_failed_urls(self) -> list:
        """Get list of URLs that failed to scrape"""
        return self.failed_urls
    
    def save_failed_urls(self, filepath: Optional[Path] = None):
        """Save failed URLs to a file for later retry"""
        import json
        
        if not self.failed_urls:
            logger.info("No failed URLs to save")
            return
        
        if filepath is None:
            filepath = LOG_DIR / f'failed_scrapes_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        try:
            with open(filepath, 'w') as f:
                json.dump(self.failed_urls, f, indent=2)
            
            logger.info(f"Saved {len(self.failed_urls)} failed URLs to {filepath}")
        
        except Exception as e:
            logger.error(f"Failed to save failed URLs: {str(e)}")


class RecoveryManager:
    """Manages recovery procedures for failed operations"""
    
    def __init__(self, db_connection):
        self.conn = db_connection
    
    def create_backup(self, backup_name: Optional[str] = None) -> Path:
        """
        Create a backup of the database
        
        Returns:
            Path to backup file
        """
        import shutil
        
        if backup_name is None:
            backup_name = f'backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        
        backup_dir = Path(__file__).parent.parent.parent / 'data' / 'backups'
        backup_dir.mkdir(exist_ok=True)
        
        db_path = Path(__file__).parent.parent.parent / 'data' / 'olympic_college.db'
        backup_path = backup_dir / backup_name
        
        try:
            shutil.copy2(db_path, backup_path)
            logger.info(f"Database backup created: {backup_path}")
            return backup_path
        
        except Exception as e:
            logger.error(f"Failed to create database backup: {str(e)}")
            raise DatabaseError(f"Backup failed: {str(e)}")
    
    def restore_backup(self, backup_path: Path) -> bool:
        """
        Restore database from backup
        
        Args:
            backup_path: Path to backup file
        
        Returns:
            True if successful
        """
        import shutil
        
        db_path = Path(__file__).parent.parent.parent / 'data' / 'olympic_college.db'
        
        try:
            # Close current connection
            self.conn.close()
            
            # Restore backup
            shutil.copy2(backup_path, db_path)
            logger.info(f"Database restored from backup: {backup_path}")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to restore database backup: {str(e)}")
            raise DatabaseError(f"Restore failed: {str(e)}")
    
    def verify_database_integrity(self) -> Tuple[bool, List[str]]:
        """
        Verify database integrity
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        try:
            cursor = self.conn.cursor()
            
            # Run SQLite integrity check
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            
            if result[0] != 'ok':
                errors.append(f"Database integrity check failed: {result[0]}")
            
            # Check for required tables
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name IN ('events', 'enhanced_content', 'event_tags')
            """)
            tables = cursor.fetchall()
            
            required_tables = {'events', 'enhanced_content', 'event_tags'}
            existing_tables = {t[0] for t in tables}
            
            missing = required_tables - existing_tables
            if missing:
                errors.append(f"Missing required tables: {', '.join(missing)}")
            
            # Check for orphaned records
            cursor.execute("""
                SELECT COUNT(*) FROM enhanced_content ec
                WHERE NOT EXISTS (SELECT 1 FROM events e WHERE e.id = ec.event_id)
            """)
            orphaned = cursor.fetchone()[0]
            
            if orphaned > 0:
                errors.append(f"Found {orphaned} orphaned enhanced_content records")
            
            is_valid = len(errors) == 0
            
            if is_valid:
                logger.info("Database integrity check passed")
            else:
                logger.warning(f"Database integrity issues found: {errors}")
            
            return is_valid, errors
        
        except Exception as e:
            logger.error(f"Error during integrity check: {str(e)}")
            errors.append(f"Integrity check error: {str(e)}")
            return False, errors
    
    def cleanup_orphaned_records(self) -> int:
        """
        Clean up orphaned records in related tables
        
        Returns:
            Number of records cleaned up
        """
        with DatabaseTransaction(self.conn, "Cleanup orphaned records") as cursor:
            # Delete orphaned enhanced_content records
            cursor.execute("""
                DELETE FROM enhanced_content
                WHERE event_id NOT IN (SELECT id FROM events)
            """)
            enhanced_deleted = cursor.rowcount
            
            # Delete orphaned event_tags records
            cursor.execute("""
                DELETE FROM event_tags
                WHERE event_id NOT IN (SELECT id FROM events)
            """)
            tags_deleted = cursor.rowcount
            
            total_deleted = enhanced_deleted + tags_deleted
            
            logger.info(f"Cleaned up {total_deleted} orphaned records")
            logger.debug(f"Enhanced content: {enhanced_deleted}, Tags: {tags_deleted}")
            
            return total_deleted


def log_operation_stats(operation_name: str, stats: dict):
    """
    Log operation statistics
    
    Args:
        operation_name: Name of the operation
        stats: Dictionary of statistics
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"{operation_name} - Statistics")
    logger.info(f"{'='*60}")
    
    for key, value in stats.items():
        logger.info(f"{key}: {value}")
    
    logger.info(f"{'='*60}\n")


# Example usage and helper functions
def safe_execute(conn, query: str, params: tuple = (), operation_name: str = "Query"):
    """
    Safely execute a database query with error handling
    
    Args:
        conn: Database connection
        query: SQL query
        params: Query parameters
        operation_name: Name for logging
    
    Returns:
        Query results or None if error occurred
    """
    try:
        with DatabaseTransaction(conn, operation_name) as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    
    except Exception as e:
        logger.error(f"Error executing {operation_name}: {str(e)}")
        return None
