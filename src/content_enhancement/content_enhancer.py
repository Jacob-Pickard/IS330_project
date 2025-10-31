import re
import sqlite3
import sys
import os
from typing import List, Dict, Set
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_utils import get_db_connection

class ContentEnhancer:
    def __init__(self):
        """Initialize the content enhancement tools"""
        self.db_conn = get_db_connection()
        
        # Common keywords for different event types
        self.event_keywords = {
            'academic': ['lecture', 'seminar', 'workshop', 'study', 'research', 'academic', 'class', 'course'],
            'social': ['meetup', 'party', 'social', 'gathering', 'networking', 'mixer'],
            'career': ['career', 'job', 'employment', 'resume', 'interview', 'professional'],
            'sports': ['game', 'match', 'tournament', 'sports', 'athletics', 'fitness'],
            'arts': ['art', 'music', 'theater', 'performance', 'exhibition', 'creative'],
            'student_life': ['club', 'organization', 'student', 'campus', 'activity']
        }
        
        # Common location keywords
        self.location_keywords = [
            'room', 'hall', 'building', 'center', 'theatre', 'theater', 'gym', 'field',
            'library', 'commons', 'plaza', 'quad', 'classroom', 'lab', 'laboratory'
        ]

    def enhance_description(self, title: str, description: str) -> str:
        """
        Enhance event description by adding structure and relevant details
        """
        # Clean up the description
        description = description.strip()
        
        # Extract potential date/time information
        time_info = self._extract_time_info(description)
        
        # Extract potential location information
        location_info = self._extract_location_info(description)
        
        # Identify event type
        event_type = self._identify_event_type(title + " " + description)
        
        # Build enhanced description
        sections = []
        
        # Add original description
        sections.append(description)
        
        # Add structured information
        additional_info = []
        
        if time_info:
            additional_info.append(f"When: {time_info}")
            
        if location_info:
            additional_info.append(f"Where: {location_info}")
            
        if event_type:
            additional_info.append(f"Event Type: {event_type}")
            
        # Add any additional structured information
        if additional_info:
            sections.append("\n\nEvent Details:")
            sections.extend(additional_info)
            
        # Add standard footer
        sections.append("\nFor more information, please check the Olympic College website or contact the event organizer.")
        
        return "\n".join(sections)

    def generate_tags(self, title: str, description: str) -> List[str]:
        """
        Generate relevant tags for the event
        """
        tags = set()
        text = (title + " " + description).lower()
        
        # Add event type tags
        for category, keywords in self.event_keywords.items():
            if any(keyword in text for keyword in keywords):
                tags.add(category)
                # Add matching keywords as tags
                tags.update(keyword for keyword in keywords if keyword in text)
        
        # Add location-based tags
        for location in self.location_keywords:
            if location in text:
                tags.add(location)
        
        # Extract potential time-based tags
        time_tags = self._generate_time_tags(text)
        tags.update(time_tags)
        
        # Clean and format tags
        cleaned_tags = [tag.replace(' ', '-') for tag in tags]
        cleaned_tags = [tag for tag in cleaned_tags if tag]  # Remove empty tags
        
        return sorted(cleaned_tags)[:10]  # Return top 10 tags

    def suggest_seo_improvements(self, title: str, description: str) -> Dict[str, List[str]]:
        """
        Suggest improvements for better discoverability
        """
        suggestions = {
            'title_suggestions': [],
            'description_suggestions': [],
            'general_suggestions': []
        }
        
        # Title analysis
        if len(title) < 5:
            suggestions['title_suggestions'].append("Title is too short. Add more descriptive words.")
        elif len(title) > 70:
            suggestions['title_suggestions'].append("Title is too long. Keep it under 70 characters for better visibility.")
        
        if not any(char.isdigit() for char in title):
            suggestions['title_suggestions'].append("Consider adding the date to the title.")
        
        # Description analysis
        if len(description) < 100:
            suggestions['description_suggestions'].append("Description is quite short. Add more details about the event.")
        
        # Check for key information
        if not self._extract_time_info(description):
            suggestions['description_suggestions'].append("Add clear date and time information.")
        
        if not self._extract_location_info(description):
            suggestions['description_suggestions'].append("Add specific location information.")
        
        # Check for common event details
        missing_details = self._check_missing_details(description)
        if missing_details:
            suggestions['description_suggestions'].extend(missing_details)
        
        return suggestions

    def _extract_time_info(self, text: str) -> str:
        """Extract time information from text"""
        # Common time patterns
        time_patterns = [
            r'\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm)',
            r'\d{1,2}(?::\d{2})?\s*(?:to|-)\s*\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm)',
            r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?',
            r'\d{1,2}/\d{1,2}/\d{2,4}'
        ]
        
        found_times = []
        for pattern in time_patterns:
            matches = re.findall(pattern, text)
            found_times.extend(matches)
            
        return ', '.join(found_times) if found_times else ''

    def _extract_location_info(self, text: str) -> str:
        """Extract location information from text"""
        # Look for location keywords followed by potential room numbers
        location_pattern = r'(?:' + '|'.join(self.location_keywords) + r')\s+[A-Za-z0-9-]+(?:\s+[A-Za-z0-9-]+)?'
        
        matches = re.findall(location_pattern, text, re.IGNORECASE)
        return ', '.join(matches) if matches else ''

    def _identify_event_type(self, text: str) -> str:
        """Identify the type of event based on keywords"""
        text = text.lower()
        matches = []
        
        for category, keywords in self.event_keywords.items():
            if any(keyword in text for keyword in keywords):
                matches.append(category.replace('_', ' ').title())
                
        return ', '.join(matches) if matches else 'General Event'

    def _generate_time_tags(self, text: str) -> Set[str]:
        """Generate time-related tags"""
        tags = set()
        
        # Time of day
        if any(time in text for time in ['morning', 'am']):
            tags.add('morning')
        if any(time in text for time in ['afternoon', 'pm']):
            tags.add('afternoon')
        if any(time in text for time in ['evening', 'night']):
            tags.add('evening')
            
        # Day of week
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for day in days:
            if day in text:
                tags.add(day)
                
        return tags

    def _check_missing_details(self, description: str) -> List[str]:
        """Check for common missing event details"""
        missing = []
        text = description.lower()
        
        if not re.search(r'contact|email|phone|\@', text):
            missing.append("Add contact information for event inquiries.")
            
        if not re.search(r'free|cost|\$|dollar|price|fee', text):
            missing.append("Specify if the event is free or add cost information.")
            
        if not re.search(r'register|registration|sign[- ]?up|rsvp', text):
            missing.append("Add registration or RSVP information if required.")
            
        return missing

def main():
    """Main function to demonstrate content enhancement"""
    enhancer = ContentEnhancer()
    
    # Example event
    example_event = {
        'title': 'Student Leadership Workshop',
        'description': 'Join us on October 15th at 2:30 PM in the Student Center Room 105 for an interactive workshop on leadership skills. Learn about team management, communication, and project planning.'
    }
    
    # Demonstrate enhancements
    print("\nEnhancing event description...")
    enhanced_desc = enhancer.enhance_description(
        example_event['title'], 
        example_event['description']
    )
    print(enhanced_desc)
    
    print("\nGenerating tags...")
    tags = enhancer.generate_tags(
        example_event['title'], 
        example_event['description']
    )
    print(tags)
    
    print("\nAnalyzing SEO...")
    seo_suggestions = enhancer.suggest_seo_improvements(
        example_event['title'], 
        example_event['description']
    )
    for category, suggestions in seo_suggestions.items():
        if suggestions:
            print(f"\n{category.replace('_', ' ').title()}:")
            for suggestion in suggestions:
                print(f"- {suggestion}")

if __name__ == "__main__":
    main()