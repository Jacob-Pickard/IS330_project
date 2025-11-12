# Olympic College Event Manager

A comprehensive system for scraping, managing, analyzing, and enhancing Olympic College events with automated conflict detection, data validation, and intelligent scheduling recommendations.

## Key Features at a Glance

- 🔄 **Automated Web Scraping** - Multi-page event extraction with retry logic
- ✅ **Data Validation** - Field-level validation with fuzzy duplicate detection
- 🛡️ **Error Handling** - Transaction management, automatic backups, comprehensive logging
- 🤖 **AI Enhancement** - SEO scoring, auto-tagging, content improvement
- ⚠️ **Conflict Detection** - Venue double-booking and building conflict identification
- 💡 **Smart Recommendations** - Automated scheduling suggestions stored in database
- 📊 **Analytics** - Statistical and AI-powered usage pattern analysis
- 📤 **Export Functionality** - CSV and iCalendar format export with filtering
- 🎯 **CLI Interface** - Unified command-line tool for all operations

---

## 1. Installation, Setup & CLI Usage Guide

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)
- Virtual environment (recommended)

### Installation Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Jacob-Pickard/IS330_project.git
   cd IS330_project
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   
   # On Windows:
   .venv\Scripts\activate
   
   # On Unix/macOS:
   source .venv/bin/activate
   ```

3. **Install required packages:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database and scrape initial data:**
   ```bash
   python src/cli.py --init-db
   python src/cli.py --scrape
   python src/cli.py --enhance-all
   ```

### Project Structure

```
IS330_project/
├── src/
│   ├── analysis/              # Event analysis tools
│   │   ├── basic_analysis.py     # Statistical analysis
│   │   ├── enhanced_analysis.py  # AI-powered insights
│   │   ├── conflict_detection.py # Scheduling conflict detection
│   │   └── recommendations.py    # Event scheduling recommendations
│   ├── content_enhancement/   # Content enhancement system
│   │   └── content_enhancer.py   # Enhancement logic
│   ├── database/             # Database management
│   │   ├── db_utils.py          # Common operations
│   │   ├── init_db.py           # Database initialization
│   │   ├── check_db.py          # Validation tools
│   │   ├── enhance_db.py        # Content enhancement DB operations
│   │   ├── validation.py        # Event validation & duplicate detection
│   │   └── error_handling.py    # Error handling, logging, recovery
│   ├── scraping/             # Web scraping tools
│   │   └── scrape_events.py     # Event scraper with validation
│   ├── utils/                # Utility scripts
│   │   └── check_past.py        # Past event checker
│   └── cli.py                # Command-line interface
├── data/                     # Database storage
│   └── backups/              # Automatic database backups
├── logs/                     # Application logs
│   ├── event_manager_*.log   # General application logs
│   └── errors_*.log          # Error-only logs
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

### CLI Command Reference

The Event Manager CLI provides comprehensive access to all system features.

#### Setup & Maintenance Commands

```bash
# Initialize or reset the database
python src/cli.py --init-db

# Scrape new events from the Olympic College website
# Note: Conflict detection runs automatically after scraping
python src/cli.py --scrape

# Enhance all events with AI-powered content analysis
python src/cli.py --enhance-all
```

#### Event Viewing Commands

```bash
# List upcoming events (default: next 10)
python src/cli.py --list

# List all events in the database
python src/cli.py --list-all

# View detailed information for a specific event
python src/cli.py --event <event_id>
```

#### Event Filtering Options

Filter events using various criteria with `--list` or `--list-all`:

```bash
# Filter by event type
python src/cli.py --list --type Academic
python src/cli.py --list --type "Student Life"

# Filter by location
python src/cli.py --list --location "Student Center"
python src/cli.py --list --location "Bldg 10"

# Filter by date range
python src/cli.py --list --date-from 2025-11-01
python src/cli.py --list --date-to 2025-12-31
python src/cli.py --list --date-from 2025-11-01 --date-to 2025-12-31

# Combine multiple filters
python src/cli.py --list --type "Arts" --location "Theater" --date-from 2025-11-01
```

#### Analysis Commands

```bash
# Run basic statistical analysis
python src/cli.py --basic-analysis
# Shows:
# - Event distribution by day of week
# - Top event locations
# - Time specification statistics

# Run AI-powered enhanced analysis
python src/cli.py --enhanced-analysis
# Shows:
# - Building usage patterns with utilization metrics
# - Recurring event pattern detection
# - AI-generated insights and recommendations
# - SEO score analysis

# Manually run conflict detection (also runs automatically after scraping)
python src/cli.py --detect-conflicts
# Shows:
# - Venue double-bookings
# - Building conflicts (multiple events in same building)
# - Recurring event timing issues
# - Alternative time slot suggestions for conflicts
# - Detailed conflict reports with recommendations

# Generate scheduling recommendations for all events
python src/cli.py --generate-recommendations
# Automatically generates:
# - Conflict severity assessments (high/medium/low)
# - Recommended actions for conflicting events
# - Alternative time slot suggestions
# - Event optimization recommendations
# - Stored in database for quick access
```

#### Export Commands

Export events in multiple formats for calendar integration or data analysis:

```bash
# Export all upcoming events to CSV
python src/cli.py --export-csv events.csv

# Export with enhanced content included (SEO, tags, descriptions)
python src/cli.py --export-csv enhanced_events.csv --include-enhanced

# Export to iCalendar format (compatible with Google Calendar, Outlook, Apple Calendar)
python src/cli.py --export-ical events.ics

# Export a single event to iCalendar format
python src/cli.py --export-event-ical 644

# Export with filters (works with both CSV and iCal)
python src/cli.py --export-csv academic.csv --type Academic
python src/cli.py --export-ical december.ics --date-from 2025-12-01 --date-to 2025-12-31
python src/cli.py --export-csv student_center.csv --location "Student Center"

# Combine multiple filters
python src/cli.py --export-ical filtered.ics --type "Arts" --location "Theater" --date-from 2025-11-01
```

**Using Exported Files:**

- **CSV Files**: Open in Excel, Google Sheets, or any spreadsheet application for data analysis, filtering, and reporting.
- **iCal Files (.ics)**: 
  - **Google Calendar**: Settings → Import & Export → Import
  - **Outlook**: File → Open & Export → Import/Export → Import an iCalendar (.ics)
  - **Apple Calendar**: File → Import
  - **Or simply double-click** the .ics file to import into your default calendar application

### Understanding Analysis Features

#### Basic Analysis
Provides statistical insights including:
- **Event Distribution**: Breakdown of events by day of week
- **Top Locations**: Most frequently used venues
- **Time Statistics**: Events with/without specific times
- **Monthly Patterns**: Event distribution across months

#### Enhanced Analysis (AI-Powered)
Provides intelligent insights including:
- **Building Usage Patterns**: Utilization metrics for each venue
- **Recurring Events**: Identification of regular event series
- **Peak Times**: Most active time blocks for each building
- **SEO Analysis**: Average, minimum, and maximum SEO scores
- **AI Insights**: Automated recommendations for optimization

### Content Enhancement System

The enhancement system automatically improves event data quality:

#### SEO Scoring (0-100)
Events are scored based on:
- Title quality and descriptiveness (length, keywords)
- Description completeness and detail
- Time and location information specificity
- Contact details presence
- Registration/RSVP information availability

#### Auto-Generated Tags
Automatically categorizes events by:
- Event type (Academic, Student Life, Arts, etc.)
- Topic extraction from descriptions
- Location-based categorization
- Time-based classification (morning, afternoon, evening)

#### Content Improvement Suggestions
The system identifies and suggests improvements for:
- Missing critical information (time, location, contact)
- Incomplete descriptions
- Lack of registration/RSVP details
- Unclear location specifications
- Vague time and date information

### Common Workflows

#### Automated Scraping Workflow
When you run `python src/cli.py --scrape`, the system automatically:

1. **Cleanup** - Removes past events and duplicates
2. **Scrape** - Fetches events from Olympic College website (with retry logic)
3. **Validate** - Checks all event data for quality and format
4. **Backup** - Creates database backup before changes
5. **Save** - Stores validated events (with transaction rollback on errors)
6. **Detect Conflicts** - Identifies scheduling conflicts
7. **Generate Recommendations** - Creates actionable suggestions
8. **Verify** - Checks database integrity
9. **Log** - Records all operations with statistics

All of this happens automatically with one command!

#### Daily Update Workflow
```bash
# 1. Scrape new events (automatic: validation, conflicts, recommendations)
python src/cli.py --scrape

# 2. Enhance new content
python src/cli.py --enhance-all

# 3. Review analytics
python src/cli.py --enhanced-analysis
```

#### Event Discovery Workflow
```bash
# 1. List upcoming events
python src/cli.py --list

# 2. Filter by interest
python src/cli.py --list --type "Academic" --date-from 2025-11-01

# 3. View detailed event info
python src/cli.py --event 42
```

#### Database Maintenance
```bash
# Check for issues
python src/utils/check_past.py

# Reset and rebuild
python src/cli.py --init-db
python src/cli.py --scrape
python src/cli.py --enhance-all
```

---

## 2. Development History

### November 12, 2025 - Data Quality & Validation, Error Handling & Recovery, Event Recommendations
- ✅ **Event Recommendation System**
  - Created automatic recommendation generation module (`recommendations.py`)
  - Added `event_recommendations` table to database schema
  - Integrated automatic recommendation generation into scraping workflow
  - Recommendations stored in database for persistent access
  - Severity-based conflict assessment (high/medium/low/none)
  - Recommended actions for each event
  - Alternative time slot suggestions
  - Event optimization recommendations
  - Integrated recommendations into CLI event detail views
  - Added `--generate-recommendations` CLI command
  
- ✅ **Data Quality & Validation System**
  - Created comprehensive event validation module (`validation.py`)
  - Implemented field-level validation (title, date, time, location, link, description)
  - Added data cleaning and normalization functions
  - Built duplicate detection with fuzzy matching (Levenshtein distance, 85% threshold)
  - Integrated validation into scraping workflow
  - Automatic validation before database insertion
  - Batch event validation with detailed statistics
  
- ✅ **Error Handling & Recovery**
  - Comprehensive error handling system with decorators (`error_handling.py`)
  - Database transaction management with automatic rollback
  - Scraping retry logic with configurable attempts (3 retries, 5-second delay)
  - Detailed logging system (general logs + error-only logs)
  - Database backup creation before major operations
  - Database integrity verification tools
  - Orphaned record cleanup procedures
  - Failed URL tracking and recovery
  - Multi-level logging (DEBUG, INFO, ERROR) with daily rotation
  - Custom exception types (DatabaseError, ScrapingError, ValidationError)

### October 31, 2025 - Content Enhancement, Cleanup & Conflict Detection
- ✅ **Event Enhancement System**
  - Implemented AI-powered content enhancement module
  - Created enhanced database schema with automatic triggers
  - Developed CLI integration for enhancement features
  - Added SEO scoring system (0-100 scale)
  - Implemented automatic tag generation
  - Added smart content improvement suggestions
  
- ✅ **Conflict Detection System**
  - Implemented venue double-booking detection
  - Added building conflict identification
  - Created recurring event timing analysis
  - Built time overlap detection algorithms
  - Integrated conflict detection into CLI
  - Generated detailed conflict reports
  - Added alternative time slot suggestions (8 AM - 7 PM blocks)
  - Automatic execution after scraping
  
- ✅ **Enhanced Database Architecture**
  - Added `enhanced_content` table for processed event data
  - Added `event_tags` table for categorization
  - Implemented automatic content processing triggers
  - Created bulk enhancement processing capability
  - Added event quality metrics tracking
  
- ✅ **CLI Improvements**
  - Unified all functionality into single CLI tool
  - Added comprehensive filtering options
  - Enhanced event display with detailed analysis
  - Added bulk processing capabilities
  - Improved user experience with clear output formatting
  
- ✅ **Code Cleanup**
  - Removed unimplemented popularity prediction feature
  - Cleaned up unused functions and imports
  - Updated documentation to reflect current features
  - Verified all components working correctly

### October 16, 2025 - Code Organization & Enhanced Analysis
- ✅ **Project Structure Improvement**
  - Reorganized code into logical modules (analysis, database, scraping, utils)
  - Created centralized database utilities
  - Added proper Python package structure with `__init__.py` files
  - Updated all import paths throughout codebase
  - Improved code maintainability and readability
  
- ✅ **AI-Powered Analysis System**
  - Building usage tracking and pattern analysis
  - Recurring event identification algorithms
  - Time block distribution analysis
  - Smart event categorization logic
  - AI-generated insights for facility usage optimization
  
- ✅ **Documentation Enhancement**
  - Expanded README with detailed usage examples
  - Added comprehensive CLI command reference
  - Improved code comments and docstrings
  - Removed obsolete testing files

### October 12, 2025 - Data Integrity
- ✅ **Database Quality Improvements**
  - Fixed duplicate event entry issues
  - Implemented automatic past event cleanup
  - Enhanced uniqueness constraints using event URLs
  - Added data validation and verification tools
  - Created database checking utilities

### October 3, 2025 - Core Functionality
- ✅ **Initial System Implementation**
  - Event scraping system with multi-page support
  - Basic event viewer (displays 10 soonest events)
  - Statistical analysis tools
  - SQLite database integration
  - Initial documentation and usage guide

### September 25, 2025 - Foundation
- ✅ **Project Initialization**
  - Database schema design and implementation
  - Sample data creation for testing
  - Integration planning with OC Student Resource Page
  - Repository setup and version control

### September 22-23, 2025 - Development Environment
- ✅ **Development Tools Setup**
  - VSCode and Claude AI integration
  - Gemma model configuration and testing
  - Performance optimization for AI processing
  - Development workflow establishment

---

## 3. Completed Features

### Core Event Management
- ✅ **Event Scraping System**
  - Automated scraping from Olympic College events calendar
  - Multi-page pagination support
  - Extraction of title, date, time, location, description, and links
  - Duplicate detection and prevention
  - Automatic past event filtering

- ✅ **Database Management**
  - SQLite database with normalized schema
  - **Core Tables:**
    - `events` - Main event data
    - `categories` - Event categories
    - `event_categories` - Event-category relationships
    - `scraping_history` - Scraping audit trail
  - **Enhancement Tables:**
    - `enhanced_content` - AI-processed event data
    - `event_tags` - Auto-generated tags
  - **Analysis Tables:**
    - `event_recommendations` - Scheduling recommendations
  - Automatic triggers for data processing
  - Database validation and checking tools
  - Automatic backup creation before major operations
  - Integrity verification and recovery procedures

### Content Enhancement
- ✅ **AI-Powered Enhancement**
  - Automatic event description improvement
  - Smart event categorization (Academic, Student Life, Arts, etc.)
  - SEO optimization scoring (0-100 scale)
  - Intelligent keyword and tag extraction
  - Quality assessment and suggestions
  - Bulk processing capabilities

- ✅ **Content Quality Features**
  - SEO scoring based on multiple factors
  - Automatic tag generation from content
  - Missing information detection
  - Improvement recommendations
  - Quality metrics tracking

### Analysis Tools
- ✅ **Basic Statistical Analysis**
  - Event distribution by day of week
  - Top event locations ranking
  - Time specification statistics
  - Monthly event distribution
  - Comprehensive event categorization

- ✅ **Enhanced AI Analysis**
  - Building usage patterns and utilization metrics
  - Recurring event pattern detection
  - Peak time identification per venue
  - Event type distribution analysis
  - AI-generated insights and recommendations
  - SEO score analysis (average, min, max)

- ✅ **Conflict Detection System**
  - Automatic execution after event scraping
  - Venue double-booking detection
  - Building conflict identification (multiple events in same building)
  - Recurring event timing analysis
  - Time overlap detection
  - **Alternative time slot suggestions** for conflicting events
  - Smart scheduling validation with standard time blocks (8 AM - 7 PM)
  - Detailed conflict reports with event details
  - Manual execution option available

- ✅ **Event Recommendation System**
  - **Automatic generation** after scraping and stored in database
  - Conflict severity assessment (high/medium/low/none)
  - Recommended actions for scheduling improvements
  - Alternative time slot suggestions for conflicts
  - Event optimization recommendations
  - Integrated into event detail views
  - Persistent storage for quick access
  - Manual regeneration available via CLI

### Command-Line Interface
- ✅ **Comprehensive CLI Tool**
  - Unified interface for all operations
  - Database initialization and maintenance
  - Event scraping and enhancement
  - Event listing with multiple filter options
  - Detailed event information display
  - Basic and enhanced analysis commands
  - Export commands for CSV and iCal formats
  - User-friendly output formatting

### Data Export & Integration
- ✅ **Export Functionality** (November 12, 2025)
  - CSV export with optional enhanced content
  - iCalendar (.ics) export for universal calendar compatibility
  - Single event export to iCal format
  - Filtering support for all export types (type, location, date range)
  - Google Calendar, Outlook, and Apple Calendar compatibility
  - Bulk export capabilities
  - Detailed export statistics and instructions

### Data Integrity
- ✅ **Quality Assurance**
  - Duplicate event detection using URLs and fuzzy matching
  - Automatic past event cleanup
  - Comprehensive data validation on input
  - Field-level validation (title, date, time, location, link, description)
  - Data cleaning and normalization
  - Database integrity checks
  - Database backup and recovery procedures
  - Transaction management with automatic rollback
  - Comprehensive error handling and logging

### Error Handling & Reliability
- ✅ **Robust Error Management**
  - Automatic retry logic for scraping failures (3 attempts)
  - Database transaction rollback on errors
  - Comprehensive logging system (logs/ directory)
  - Failed operation tracking and recovery
  - Database backup before major operations
  - Integrity verification after data changes
  - Orphaned record cleanup
  - Detailed error messages with stack traces

### Code Organization
- ✅ **Professional Structure**
  - Modular architecture (analysis, database, scraping, utils)
  - Proper Python package structure
  - Centralized database utilities
  - Standardized import paths
  - Clean separation of concerns
  - Comprehensive documentation

---

## 4. Backlog

### High Priority

#### Scheduling Intelligence
- [x] **Conflict Detection** ✅ COMPLETED
  - ✅ Identify venue double-bookings
  - ✅ Detect time conflicts for recurring events
  - ✅ Alert on scheduling overlaps
  - ✅ Suggest alternative time slots

- [ ] **Schedule Optimization**
  - Event spacing recommendations
  - Underutilized time slot identification
  - Venue load balancing
  - Peak time distribution analysis

#### Data Quality & Validation
- [x] **Input Validation System** ✅ COMPLETED
  - ✅ Validate all scraped data fields
  - ✅ Implement data cleaning procedures
  - ✅ Enhanced duplicate detection algorithms with fuzzy matching

- [x] **Error Handling** ✅ COMPLETED
  - ✅ Graceful handling of scraping failures with retry logic
  - ✅ Database transaction rollback on errors
  - ✅ Comprehensive error logging (general + error-only logs)
  - ✅ Recovery procedures for failed operations (backup/restore)

### Medium Priority

#### Visualization & Reporting
- [ ] **Dashboard Features**
  - Venue utilization visualizations
  - Schedule density heatmaps
  - Event distribution charts
  - Trend analysis graphs

- [ ] **Export Capabilities**
  - ✅ CSV export for event data (November 12, 2025)
  - ✅ iCal (.ics) export for calendar integration (November 12, 2025)
  - [ ] PDF report generation

#### Advanced Content Features
- [ ] **Enhanced Search**
  - Natural language event search
  - Advanced filtering combinations
  - Saved search preferences
  - Search result ranking

- [ ] **Recommendation Engine**
  - Personalized event suggestions
  - Similar event recommendations
  - Interest-based filtering
  - Attendance pattern analysis

#### Calendar Integration
- [x] **Export Formats** (November 12, 2025)
  - ✅ iCal (.ics) export with filtering support
  - ✅ Google Calendar compatibility via .ics import
  - ✅ Outlook calendar compatibility via .ics import
  - ✅ Apple Calendar compatibility via .ics import
  - ✅ Bulk calendar export
  - ✅ Single event export

- [ ] **Sync Features**
  - Real-time calendar updates
  - Conflict detection with personal calendars
  - Event change notifications

### Low Priority

#### Capacity Management
- [ ] **Venue Information**
  - Room capacity tracking
  - Venue suitability matching
  - Resource allocation optimization
  - Space utilization monitoring

- [ ] **Resource Management**
  - Equipment tracking
  - Room setup requirements
  - Catering coordination
  - AV equipment scheduling

#### User Experience
- [ ] **Web Interface**
  - Browser-based event viewer
  - Interactive calendar view
  - Event registration integration
  - Mobile-responsive design

- [ ] **Multi-language Support**
  - Spanish language support
  - Translation for event descriptions
  - Multilingual search capabilities

#### Advanced Analytics
- [ ] **Predictive Analytics**
  - Event attendance prediction (requires historical data)
  - Trend forecasting
  - Seasonal pattern analysis
  - Venue popularity metrics

- [ ] **Performance Metrics**
  - Event success metrics
  - Venue utilization efficiency
  - Peak time analysis
  - ROI calculations for events

### Future Considerations

#### Integration Opportunities
- [ ] **External Systems**
  - Student information system integration
  - Campus directory integration
  - Email notification system
  - Social media posting automation

- [ ] **API Development**
  - RESTful API for event data
  - Webhook support for event updates
  - Third-party integration capabilities
  - API documentation and versioning

#### Content Enhancement
- [ ] **Media Processing**
  - Event flyer image extraction
  - OCR for event poster information
  - Image optimization for web
  - Video event preview support

- [ ] **Advanced NLP**
  - Topic modeling for event categorization
  - Sentiment analysis for event descriptions
  - Automatic summary generation
  - Smart event matching algorithms

---

## Contributing

This is an academic project for IS330 at Olympic College. For questions or suggestions, please contact the project maintainer.

## License

This project is part of coursework for IS330 at Olympic College.

---

**Last Updated:** November 12, 2025