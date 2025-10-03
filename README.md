Usage:
[Initialize DB and Run Scraper to gather data] python src/init_db.py; python src/scrape_events.py
[View 10 soonest events] python src/scrape_events.py --view
[Run Event Analyzer] python src/analyze_events.py

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
[X] Expand on Database Analyzer somehow
- Technical Debt
[X] Make sure that events that have already passed are removed.
[X] Make it so that events without a specified time or location return a null value instead of a blank string? I have a feeling a blank entry may cause some issues later on.
- Bugs
[X] None (so far)