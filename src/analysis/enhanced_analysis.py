import sys
from pathlib import Path
from datetime import datetime
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

sys.path.append(str(Path(__file__).parent.parent))
from database.db_utils import get_db_connection as connect_db

def get_event_stats():
    """Gather comprehensive event statistics"""
    conn = connect_db()
    cursor = conn.cursor()
    
    stats = {}
    
    # Get total event count
    cursor.execute("SELECT COUNT(*) FROM events")
    stats['total_events'] = cursor.fetchone()[0]
    
    # Get events by building
    cursor.execute("""
        SELECT 
            CASE 
                WHEN location LIKE '%Bldg%' THEN 
                    SUBSTR(location, INSTR(location, 'Bldg'), 
                          CASE 
                              WHEN INSTR(SUBSTR(location, INSTR(location, 'Bldg')), ',') = 0 
                              THEN LENGTH(SUBSTR(location, INSTR(location, 'Bldg')))
                              ELSE INSTR(SUBSTR(location, INSTR(location, 'Bldg')), ',') - 1
                          END)
                ELSE location 
            END as building,
            COUNT(*) as count
        FROM events
        WHERE location IS NOT NULL
        GROUP BY building
        HAVING building LIKE 'Bldg%'
        ORDER BY count DESC
    """)
    stats['events_by_building'] = cursor.fetchall()
    
    # Get recurring events (events with same title but different dates)
    cursor.execute("""
        WITH event_counts AS (
            SELECT title, COUNT(*) as occurrences
            FROM events
            GROUP BY title
            HAVING COUNT(*) > 1
        )
        SELECT title, occurrences
        FROM event_counts
        ORDER BY occurrences DESC
        LIMIT 5
    """)
    stats['recurring_events'] = cursor.fetchall()
    
    # Get busiest time blocks
    cursor.execute("""
        SELECT 
            CASE 
                WHEN time < '12:00' THEN 'Morning (before noon)'
                WHEN time < '17:00' THEN 'Afternoon (12-5 PM)'
                ELSE 'Evening (after 5 PM)'
            END as time_block,
            COUNT(*) as count
        FROM events
        WHERE time IS NOT NULL
        GROUP BY time_block
        ORDER BY count DESC
    """)
    stats['time_blocks'] = cursor.fetchall()
    
    # Get event categories (based on keywords)
    cursor.execute("""
        SELECT 
            CASE
                WHEN LOWER(title) LIKE '%workshop%' OR LOWER(title) LIKE '%training%' THEN 'Workshop/Training'
                WHEN LOWER(title) LIKE '%information session%' OR LOWER(title) LIKE '%info session%' THEN 'Information Session'
                WHEN LOWER(title) LIKE '%deadline%' OR LOWER(title) LIKE '%due%' THEN 'Academic Deadline'
                WHEN LOWER(title) LIKE '%holiday%' OR LOWER(title) LIKE '%closed%' THEN 'Holiday/Closure'
                WHEN LOWER(title) LIKE '%series%' OR LOWER(title) LIKE '%weekly%' THEN 'Recurring Series'
                ELSE 'Other'
            END as event_type,
            COUNT(*) as count
        FROM events
        GROUP BY event_type
        ORDER BY count DESC
    """)
    stats['event_types'] = cursor.fetchall()
    
    conn.close()
    return stats

def generate_insights(stats):
    """Use Gemma 2B to generate natural language insights from the statistics"""
    # Initialize model
    tokenizer = AutoTokenizer.from_pretrained("google/gemma-2b")
    model = AutoModelForCausalLM.from_pretrained("google/gemma-2b", device_map="auto")
    
    # Create a prompt with the statistics
    prompt = """Analyze these Olympic College event statistics and provide 3-4 key insights about patterns, 
potential improvements, or interesting findings. Consider aspects like:
- Building usage efficiency
- Student accessibility of events
- Distribution of academic vs social events
- Opportunities for better scheduling

Key insights:\n"""
    
    prompt += f"Total events: {stats['total_events']}\n\n"
    
    prompt += "Events by building:\n"
    for building, count in stats['events_by_building']:
        prompt += f"- {building}: {count} events\n"
    
    prompt += "\nRecurring events:\n"
    for title, occurrences in stats['recurring_events']:
        prompt += f"- {title}: occurs {occurrences} times\n"
    
    prompt += "\nTime block distribution:\n"
    for block, count in stats['time_blocks']:
        prompt += f"- {block}: {count} events\n"
    
    prompt += "\nEvent types:\n"
    for type_, count in stats['event_types']:
        prompt += f"- {type_}: {count} events\n"
    
    # Generate insights
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(
        **inputs,
        max_new_tokens=500,  # Generate up to 500 new tokens
        temperature=0.7,
        top_p=0.9,
        do_sample=True,
        num_beams=4,
        no_repeat_ngram_size=2
    )
    
    insights = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return insights.split("Key insights:")[1] if "Key insights:" in insights else insights

def enhanced_analysis():
    """Run enhanced analysis combining statistics and AI insights"""
    print("Running Enhanced Event Analysis...\n")
    
    # Get statistics
    stats = get_event_stats()
    
    # Display building statistics
    print("Building Usage Analysis:")
    print("-----------------------")
    for building, count in stats['events_by_building']:
        print(f"{building}: {count} events")
    print()
    
    # Display recurring events
    print("Top Recurring Events:")
    print("--------------------")
    for title, occurrences in stats['recurring_events']:
        print(f"'{title}' occurs {occurrences} times")
    print()
    
    # Display time block distribution
    print("Time Block Distribution:")
    print("----------------------")
    for block, count in stats['time_blocks']:
        print(f"{block}: {count} events")
    print()
    
    # Display event types
    print("Event Type Distribution:")
    print("----------------------")
    for type_, count in stats['event_types']:
        print(f"{type_}: {count} events")
    print()
    
    # Generate and display AI insights
    print("AI-Generated Insights:")
    print("--------------------")
    insights = generate_insights(stats)
    print(insights)

if __name__ == "__main__":
    enhanced_analysis()