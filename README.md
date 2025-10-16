# Olympic College Event Manager

A comprehensive system for scraping, managing, and analyzing Olympic College events.

## Project Structure

```
src/
├── analysis/           # Event analysis tools
│   ├── basic_analysis.py   # Basic statistical analysis
│   └── enhanced_analysis.py # AI-powered analysis
├── database/          # Database management
│   ├── db_utils.py    # Common database operations
│   ├── init_db.py     # Database initialization
│   └── check_db.py    # Database validation tools
├── scraping/         # Web scraping tools
│   └── scrape_events.py # Event scraper
└── utils/           # Utility scripts
    └── check_past.py  # Past event checker
```

## Features

- Database & Data Management
  [X] SQLite database with events, categories, and scraping history tables
  [X] Automatic cleanup of past events before each scrape
  [X] Prevention of duplicate events using unique event URLs
  [X] Proper null value handling for missing times/locations
  [X] Sample data and categories for testing

- Event Scraping
  [X] Automated event scraping from Olympic College website
  [X] Multi-page scraping support
  [X] Detailed event information capture (title, date, time, location, description)

- Basic Analysis & Viewing
  [X] View 10 soonest upcoming events
  [X] Events by day of week breakdown
  [X] Monthly event distribution
  [X] Time specification statistics

- Enhanced Analysis (AI-Powered)
  [X] Building Usage Analysis:
      - Track events per building
      - Identify most/least used facilities
      - Building utilization patterns
  [X] Event Pattern Recognition:
      - Identify recurring events and their frequency
      - Time block distribution (morning/afternoon/evening)
      - Automatic event type categorization
  [X] Smart Insights:
      - AI-generated analysis of usage patterns
      - Facility utilization assessment
      - Event scheduling optimization suggestions

- Development Tools
  [X] Database checker for past events and duplicates
  [X] Comprehensive usage documentation
  [X] VSCode and Claude integration
  [X] Efficient development environment setup


Usage:

Basic Operations:
```bash
# Initialize database and scrape events (this will also clean up any past events)
python src/database/init_db.py; python src/scraping/scrape_events.py

# View the 10 soonest upcoming events
python src/scraping/scrape_events.py --view
```

Analysis Tools:
```bash
# Run basic statistical analysis
python src/analysis/basic_analysis.py

# Run enhanced AI-powered analysis
# Features:
# - Building usage patterns
# - Recurring event identification
# - Time block distribution
# - Event type categorization
# - AI-generated insights
python src/enhanced_analysis.py
```

Database Maintenance:
```bash
# Check for past events and duplicates in database
python src/database/check_db.py

# Reinitialize database and rescrape all events (useful if database becomes corrupted)
rm data/olympic_college.db
python src/database/init_db.py
python src/scraping/scrape_events.py
```


10/16
    [X] Improved the README file with expanded usage docs and implemented features
    [X] Removed excess files needed for initial testing of gemma 2b (generate_poem.py)
    [X] Added enhanced AI-powered analysis capabilities:
        - Building usage tracking and patterns
        - Recurring event identification
        - Time block distribution analysis
        - Smart event categorization
        - AI-generated insights for facility usage
    [X] Improved project structure:
        - Organized code into logical modules (analysis, database, scraping, utils)
        - Created centralized database utilities
        - Added proper Python package structure
        - Updated all import paths and documentation


10/12
    [X] Fixed duplicate event entries in database by removing redundant event appending in scraper
    [X] Added cleanup_past_events() function to automatically remove past events before each scrape
    [X] Changed uniqueness constraint to use event link instead of title/date/time combination
    [X] Verified that both past events and duplicates are being properly handled

10/3
    [X] Implemented my old program which actually scrapes the data and had it input into my database.
    [X] Added a function to view the 10 soonest events that are occurring.
    [X] Created a simple program to do some data analysis. Shows top 5 event locations, how many events are on a certain day of the week, number of events by month, and which events have time a time specified.
    [X] Added usage info to make it easier for new users or whoever wants to check out the prototype (Professor mainly)

9/25
    [X] Created a python program that initializes my database for my project. I've decided to continue with my original idea of integrating it with my OC Student Resource Page site.
    [X] Stored sample data that fits with my original schema from last quarters resource page. 

9/23
    [X] Swapped out the gemma 7b model for the 3b model, and configured it to run on both cpu and gpu which improved performance drastically.
    [X] gemma was able to consistently create poems for me in a very short amount of time.

9/22
    [X] Setup development environment with VSCode and Claude, successfully ran gemma 7b model, but not without significant performance hits.

Backlog
- Features
    [X] Setup output to my resource page somehow, whether that be through lambda or S3, etc.
    [X] Expand on Database Analyzer somehow  - DONE (10/16)

- Technical Debt
    [X] Make it so that events without a specified time or location return a null value instead of a blank string. I have a feeling a blank entry may cause some issues later on. (Turns out this was already implemented, just shows up differently inside sql than I thought it would) - DONE (10/12)
    [X] Make sure that events that have already passed are removed - DONE (10/12)
    [X] Changed uniqueness constraint to use event link instead of title/date/time combination  - DONE (10/12)
    [X] Verified that both past events and duplicates are being properly handled  - DONE (10/12)

- Bugs
    [X] Fixed: Duplicate events being added to database - FIXED (10/12)
