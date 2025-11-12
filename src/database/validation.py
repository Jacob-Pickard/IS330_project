"""
Data Validation System for Event Data

This module provides comprehensive validation for scraped event data including:
- Field validation (required fields, format checks)
- Data cleaning and normalization
- Duplicate detection
- Data integrity checks
"""

import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


class EventValidator:
    """Validates and cleans event data"""
    
    # Required fields for events
    REQUIRED_FIELDS = ['title', 'date', 'link']
    
    # Optional fields that should be validated if present
    OPTIONAL_FIELDS = ['time', 'location', 'description']
    
    def __init__(self):
        self.validation_errors = []
        self.warnings = []
    
    def validate_title(self, title: str) -> Tuple[bool, str]:
        """
        Validate event title
        
        Returns:
            Tuple of (is_valid, cleaned_title)
        """
        if not title or not isinstance(title, str):
            self.validation_errors.append("Title is required")
            return False, ""
        
        # Clean title
        cleaned = title.strip()
        
        # Check minimum length
        if len(cleaned) < 3:
            self.validation_errors.append(f"Title too short: '{cleaned}'")
            return False, cleaned
        
        # Check maximum length
        if len(cleaned) > 200:
            self.warnings.append(f"Title exceeds 200 characters, truncating")
            cleaned = cleaned[:200]
        
        # Remove excessive whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return True, cleaned
    
    def validate_date(self, date_str: str) -> Tuple[bool, Optional[str]]:
        """
        Validate and normalize date string
        
        Returns:
            Tuple of (is_valid, normalized_date)
        """
        if not date_str or not isinstance(date_str, str):
            self.validation_errors.append("Date is required")
            return False, None
        
        # Try to parse date in expected format (YYYY-MM-DD)
        try:
            date_obj = datetime.strptime(date_str.strip(), '%Y-%m-%d')
            normalized = date_obj.strftime('%Y-%m-%d')
            return True, normalized
        except ValueError:
            pass
        
        # Try alternative formats
        alt_formats = ['%m/%d/%Y', '%d-%m-%Y', '%Y/%m/%d']
        for fmt in alt_formats:
            try:
                date_obj = datetime.strptime(date_str.strip(), fmt)
                normalized = date_obj.strftime('%Y-%m-%d')
                self.warnings.append(f"Date converted from {fmt} to YYYY-MM-DD")
                return True, normalized
            except ValueError:
                continue
        
        self.validation_errors.append(f"Invalid date format: '{date_str}'")
        return False, None
    
    def validate_time(self, time_str: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validate and normalize time string
        
        Returns:
            Tuple of (is_valid, normalized_time)
        """
        if not time_str:
            return True, None  # Time is optional
        
        if not isinstance(time_str, str):
            self.warnings.append("Invalid time type, skipping")
            return True, None
        
        # Clean time string
        cleaned = time_str.strip()
        
        # Try to parse time in HH:MM format
        try:
            time_obj = datetime.strptime(cleaned, '%H:%M')
            normalized = time_obj.strftime('%H:%M')
            return True, normalized
        except ValueError:
            pass
        
        # Try 12-hour format
        for fmt in ['%I:%M %p', '%I:%M%p', '%I %p']:
            try:
                time_obj = datetime.strptime(cleaned, fmt)
                normalized = time_obj.strftime('%H:%M')
                self.warnings.append(f"Time converted from 12-hour to 24-hour format")
                return True, normalized
            except ValueError:
                continue
        
        self.warnings.append(f"Invalid time format: '{time_str}', skipping")
        return True, None
    
    def validate_location(self, location: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validate and clean location string
        
        Returns:
            Tuple of (is_valid, cleaned_location)
        """
        if not location:
            return True, None  # Location is optional
        
        if not isinstance(location, str):
            self.warnings.append("Invalid location type, skipping")
            return True, None
        
        # Clean location
        cleaned = location.strip()
        
        # Remove excessive whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Check maximum length
        if len(cleaned) > 200:
            self.warnings.append(f"Location exceeds 200 characters, truncating")
            cleaned = cleaned[:200]
        
        return True, cleaned if cleaned else None
    
    def validate_link(self, link: str) -> Tuple[bool, str]:
        """
        Validate event link/URL
        
        Returns:
            Tuple of (is_valid, cleaned_link)
        """
        if not link or not isinstance(link, str):
            self.validation_errors.append("Link is required")
            return False, ""
        
        cleaned = link.strip()
        
        # Basic URL validation
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or IP
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE
        )
        
        if not url_pattern.match(cleaned):
            self.validation_errors.append(f"Invalid URL format: '{cleaned}'")
            return False, cleaned
        
        return True, cleaned
    
    def validate_description(self, description: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validate and clean description
        
        Returns:
            Tuple of (is_valid, cleaned_description)
        """
        if not description:
            return True, None  # Description is optional
        
        if not isinstance(description, str):
            self.warnings.append("Invalid description type, skipping")
            return True, None
        
        # Clean description
        cleaned = description.strip()
        
        # Remove excessive whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Check maximum length (for database storage)
        if len(cleaned) > 5000:
            self.warnings.append(f"Description exceeds 5000 characters, truncating")
            cleaned = cleaned[:5000]
        
        return True, cleaned if cleaned else None
    
    def validate_event(self, event_data: Dict) -> Tuple[bool, Dict, List[str]]:
        """
        Validate complete event data
        
        Args:
            event_data: Dictionary containing event fields
        
        Returns:
            Tuple of (is_valid, cleaned_data, error_messages)
        """
        self.validation_errors = []
        self.warnings = []
        
        cleaned_data = {}
        
        # Validate required fields
        for field in self.REQUIRED_FIELDS:
            if field not in event_data:
                self.validation_errors.append(f"Missing required field: {field}")
        
        # Validate title
        if 'title' in event_data:
            valid, cleaned = self.validate_title(event_data['title'])
            if valid:
                cleaned_data['title'] = cleaned
        
        # Validate date
        if 'date' in event_data:
            valid, cleaned = self.validate_date(event_data['date'])
            if valid:
                cleaned_data['date'] = cleaned
        
        # Validate link
        if 'link' in event_data:
            valid, cleaned = self.validate_link(event_data['link'])
            if valid:
                cleaned_data['link'] = cleaned
        
        # Validate optional fields
        if 'time' in event_data:
            valid, cleaned = self.validate_time(event_data.get('time'))
            if valid and cleaned:
                cleaned_data['time'] = cleaned
        
        if 'location' in event_data:
            valid, cleaned = self.validate_location(event_data.get('location'))
            if valid and cleaned:
                cleaned_data['location'] = cleaned
        
        if 'description' in event_data:
            valid, cleaned = self.validate_description(event_data.get('description'))
            if valid and cleaned:
                cleaned_data['description'] = cleaned
        
        # Combine errors and warnings
        messages = []
        if self.validation_errors:
            messages.extend([f"ERROR: {e}" for e in self.validation_errors])
        if self.warnings:
            messages.extend([f"WARNING: {w}" for w in self.warnings])
        
        is_valid = len(self.validation_errors) == 0
        
        return is_valid, cleaned_data, messages


class DuplicateDetector:
    """Enhanced duplicate detection for events"""
    
    def __init__(self, db_connection):
        self.conn = db_connection
    
    def is_duplicate(self, event_data: Dict) -> Tuple[bool, Optional[int], str]:
        """
        Check if event is a duplicate
        
        Returns:
            Tuple of (is_duplicate, existing_event_id, reason)
        """
        cursor = self.conn.cursor()
        
        # Method 1: Exact link match (most reliable)
        if 'link' in event_data:
            cursor.execute(
                "SELECT id FROM events WHERE link = ?",
                (event_data['link'],)
            )
            result = cursor.fetchone()
            if result:
                return True, result[0], "Exact link match"
        
        # Method 2: Title + Date match
        if 'title' in event_data and 'date' in event_data:
            cursor.execute(
                "SELECT id FROM events WHERE title = ? AND date = ?",
                (event_data['title'], event_data['date'])
            )
            result = cursor.fetchone()
            if result:
                return True, result[0], "Title and date match"
        
        # Method 3: Fuzzy title match on same date (similarity check)
        if 'title' in event_data and 'date' in event_data:
            cursor.execute(
                "SELECT id, title FROM events WHERE date = ?",
                (event_data['date'],)
            )
            existing_events = cursor.fetchall()
            
            for event_id, existing_title in existing_events:
                similarity = self._calculate_similarity(
                    event_data['title'].lower(),
                    existing_title.lower()
                )
                if similarity > 0.85:  # 85% similarity threshold
                    return True, event_id, f"High similarity match ({similarity:.0%})"
        
        return False, None, ""
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate similarity between two strings using Levenshtein distance
        
        Returns:
            Similarity ratio (0.0 to 1.0)
        """
        # Simple implementation - could use python-Levenshtein for better performance
        if str1 == str2:
            return 1.0
        
        if len(str1) == 0 or len(str2) == 0:
            return 0.0
        
        # Create distance matrix
        rows = len(str1) + 1
        cols = len(str2) + 1
        distance = [[0 for _ in range(cols)] for _ in range(rows)]
        
        # Initialize first row and column
        for i in range(1, rows):
            distance[i][0] = i
        for j in range(1, cols):
            distance[0][j] = j
        
        # Calculate distances
        for i in range(1, rows):
            for j in range(1, cols):
                if str1[i-1] == str2[j-1]:
                    cost = 0
                else:
                    cost = 1
                
                distance[i][j] = min(
                    distance[i-1][j] + 1,      # deletion
                    distance[i][j-1] + 1,      # insertion
                    distance[i-1][j-1] + cost  # substitution
                )
        
        # Calculate similarity ratio
        max_len = max(len(str1), len(str2))
        similarity = 1 - (distance[rows-1][cols-1] / max_len)
        
        return similarity


def validate_batch_events(events: List[Dict]) -> Tuple[List[Dict], List[Dict], Dict]:
    """
    Validate a batch of events
    
    Args:
        events: List of event dictionaries
    
    Returns:
        Tuple of (valid_events, invalid_events, statistics)
    """
    validator = EventValidator()
    valid_events = []
    invalid_events = []
    
    stats = {
        'total': len(events),
        'valid': 0,
        'invalid': 0,
        'warnings': 0,
        'errors': []
    }
    
    for i, event in enumerate(events):
        is_valid, cleaned_data, messages = validator.validate_event(event)
        
        if is_valid:
            valid_events.append(cleaned_data)
            stats['valid'] += 1
        else:
            invalid_events.append({
                'index': i,
                'data': event,
                'errors': messages
            })
            stats['invalid'] += 1
            stats['errors'].extend(messages)
        
        # Count warnings
        stats['warnings'] += sum(1 for m in messages if m.startswith('WARNING'))
    
    return valid_events, invalid_events, stats
