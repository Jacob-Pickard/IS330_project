import re
import sqlite3
import sys
import os
from typing import List, Dict, Tuple
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_utils import get_db_connection

class ContentEnhancer:
    def __init__(self):
        """Initialize the content enhancement tools"""
        # Download required NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
            nltk.download('averaged_perceptron_tagger')
            nltk.download('maxent_ne_chunker')
            nltk.download('words')

        # Initialize NLP models
        self.nlp = spacy.load('en_core_web_sm')
        self.keyword_model = KeyBERT()
        self.summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        
        # Connect to database
        self.db_conn = get_db_connection()

    def enhance_description(self, title: str, description: str) -> str:
        """
        Enhance event description by adding relevant details and improving clarity
        """
        # Process the input text
        doc = self.nlp(description)
        
        # Extract key information
        entities = [(ent.text, ent.label_) for ent in doc.ents]
        
        # Generate a summary if the description is long
        if len(description.split()) > 50:
            summary = self.summarizer(description, max_length=130, min_length=30, do_sample=False)
            enhanced_desc = summary[0]['summary_text']
        else:
            enhanced_desc = description

        # Add structured information if found
        info_sections = []
        
        # Add speaker/organizer information if found
        speakers = [ent.text for ent in doc.ents if ent.label_ == 'PERSON']
        if speakers:
            info_sections.append("Speaker(s): " + ", ".join(speakers))

        # Add organization information if found
        orgs = [ent.text for ent in doc.ents if ent.label_ == 'ORG']
        if orgs:
            info_sections.append("Organization(s): " + ", ".join(orgs))

        # Combine enhanced description with structured information
        if info_sections:
            enhanced_desc = enhanced_desc + "\n\n" + "\n".join(info_sections)

        return enhanced_desc

    def extract_keywords(self, text: str, num_keywords: int = 5) -> List[str]:
        """
        Extract the most relevant keywords from the text
        """
        keywords = self.keyword_model.extract_keywords(text, 
                                                     keyphrase_ngram_range=(1, 2),
                                                     stop_words='english',
                                                     top_n=num_keywords)
        return [keyword for keyword, _ in keywords]

    def generate_tags(self, title: str, description: str) -> List[str]:
        """
        Generate relevant tags for the event
        """
        # Combine title and description for better context
        full_text = f"{title} {description}"
        
        # Extract keywords
        keywords = self.extract_keywords(full_text)
        
        # Process text with spaCy
        doc = self.nlp(full_text)
        
        # Extract named entities
        entities = [ent.text for ent in doc.ents]
        
        # Combine and clean tags
        tags = list(set(keywords + entities))
        
        # Clean and format tags
        cleaned_tags = [slugify(tag) for tag in tags]
        cleaned_tags = [tag for tag in cleaned_tags if tag]  # Remove empty tags
        
        return cleaned_tags[:10]  # Limit to top 10 tags

    def suggest_seo_improvements(self, title: str, description: str) -> Dict[str, List[str]]:
        """
        Suggest SEO improvements for the event content
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
            
        # Check if title has key event information
        title_doc = self.nlp(title)
        if not any(token.like_num for token in title_doc):
            suggestions['title_suggestions'].append("Consider adding date/time information in the title.")
            
        # Description analysis
        if len(description) < 100:
            suggestions['description_suggestions'].append("Description is quite short. Add more details about the event.")
        
        # Check for key event elements in description
        desc_doc = self.nlp(description.lower())
        key_elements = {
            'time': ['time', 'am', 'pm', 'o\'clock'],
            'location': ['room', 'building', 'hall', 'center'],
            'contact': ['contact', 'email', 'phone', 'information']
        }
        
        for element, keywords in key_elements.items():
            if not any(keyword in description.lower() for keyword in keywords):
                suggestions['description_suggestions'].append(f"Add {element} information to the description.")

        # General SEO suggestions
        keywords = self.extract_keywords(f"{title} {description}")
        if keywords:
            suggestions['general_suggestions'].append(f"Consider emphasizing these key terms: {', '.join(keywords)}")
            
        return suggestions

    def enhance_event(self, event_id: int) -> Dict[str, any]:
        """
        Enhance all content aspects of an event
        """
        # Fetch event details
        cursor = self.db_conn.cursor()
        cursor.execute("""
            SELECT title, description
            FROM events
            WHERE id = ?
        """, (event_id,))
        
        event = cursor.fetchone()
        if not event:
            raise ValueError(f"Event with ID {event_id} not found")
            
        title, description = event
        
        # Generate enhancements
        enhanced_content = {
            'enhanced_description': self.enhance_description(title, description),
            'tags': self.generate_tags(title, description),
            'seo_suggestions': self.suggest_seo_improvements(title, description),
            'keywords': self.extract_keywords(f"{title} {description}")
        }
        
        return enhanced_content

def main():
    """Main function to demonstrate content enhancement"""
    enhancer = ContentEnhancer()
    
    # Example event
    example_event = {
        'title': 'Student Leadership Workshop',
        'description': 'Join us for an interactive workshop on leadership skills. Learn about team management, communication, and project planning. Guest speaker Dr. Sarah Johnson from the Business Department will share insights from her 15 years of experience in corporate leadership. The workshop includes hands-on activities and networking opportunities.'
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
    
    print("\nExtracting keywords...")
    keywords = enhancer.extract_keywords(
        f"{example_event['title']} {example_event['description']}"
    )
    print(keywords)
    
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