"""
Test script to verify data validation and error handling system
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from database.validation import EventValidator, DuplicateDetector, validate_batch_events
from database.error_handling import logger

def test_validation():
    """Test event validation with various scenarios"""
    print("=" * 60)
    print("Testing Event Validation System")
    print("=" * 60)
    
    # Test data with various issues
    test_events = [
        {
            'title': 'Valid Event',
            'date': '2025-12-15',
            'time': '14:00',
            'location': 'Building 1, Room 101',
            'link': 'https://www.olympic.edu/event/123',
            'description': 'This is a properly formatted event with all required fields and sufficient detail.'
        },
        {
            'title': '',  # Invalid: empty title
            'date': '2025-12-15',
            'time': '14:00',
            'location': 'Building 1, Room 101',
            'link': 'https://www.olympic.edu/event/124',
            'description': 'Missing title event'
        },
        {
            'title': 'Invalid Date Event',
            'date': '2025-13-45',  # Invalid: bad date format
            'time': '14:00',
            'location': 'Building 1, Room 101',
            'link': 'https://www.olympic.edu/event/125',
            'description': 'This event has an invalid date'
        },
        {
            'title': 'Past Event',
            'date': '2020-01-01',  # Invalid: past date
            'time': '14:00',
            'location': 'Building 1, Room 101',
            'link': 'https://www.olympic.edu/event/126',
            'description': 'This event is in the past'
        },
        {
            'title': 'Invalid Time Event',
            'date': '2025-12-15',
            'time': '25:99',  # Invalid: bad time format
            'location': 'Building 1, Room 101',
            'link': 'https://www.olympic.edu/event/127',
            'description': 'This event has invalid time'
        },
        {
            'title': '   Extra   Whitespace   Event   ',  # Should be cleaned
            'date': '2025-12-16',
            'time': '10:00',
            'location': '  Building 2  ',
            'link': 'https://www.olympic.edu/event/128',
            'description': '   This has extra whitespace   '
        }
    ]
    
    print(f"\nTesting {len(test_events)} events...\n")
    
    # Run batch validation
    valid_events, invalid_events, stats = validate_batch_events(test_events)
    
    print("\n" + "=" * 60)
    print("VALIDATION RESULTS")
    print("=" * 60)
    
    print(f"\nValid Events: {len(valid_events)}")
    for event in valid_events:
        print(f"  ✓ {event['title']}")
    
    print(f"\nInvalid Events: {len(invalid_events)}")
    for invalid in invalid_events:
        print(f"  ✗ {invalid['data'].get('title', 'Unknown')}")
        for error in invalid['errors']:
            print(f"    - {error}")
    
    # Test individual validation
    print("\n" + "=" * 60)
    print("INDIVIDUAL VALIDATOR TESTS")
    print("=" * 60)
    
    validator = EventValidator()
    
    # Test title validation
    print("\nTitle Validation:")
    is_valid, cleaned = validator.validate_title("  Valid Title  ")
    print(f"  Input: '  Valid Title  '")
    print(f"  Valid: {is_valid}, Cleaned: '{cleaned}'")
    
    is_valid, cleaned = validator.validate_title("")
    print(f"  Input: ''")
    print(f"  Valid: {is_valid}, Errors: {validator.validation_errors}")
    
    # Test date validation
    print("\nDate Validation:")
    is_valid, cleaned = validator.validate_date("2025-12-15")
    print(f"  Input: '2025-12-15'")
    print(f"  Valid: {is_valid}")
    
    is_valid, cleaned = validator.validate_date("2020-01-01")
    print(f"  Input: '2020-01-01' (past)")
    print(f"  Valid: {is_valid}, Errors: {validator.validation_errors}")
    
    # Test time validation
    print("\nTime Validation:")
    is_valid, cleaned = validator.validate_time("14:30")
    print(f"  Input: '14:30'")
    print(f"  Valid: {is_valid}")
    
    is_valid, cleaned = validator.validate_time("25:99")
    print(f"  Input: '25:99'")
    print(f"  Valid: {is_valid}, Errors: {validator.validation_errors}")
    
    print("\n" + "=" * 60)
    print("Test completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    test_validation()
