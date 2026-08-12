# System Design v0

## Project flow (rough)

NHL API (Automate using AWS Step Functions, Lambda, Glue)

↓

Bronze Storage (S3)

↓

Cleaning

↓

Silver Tables (S3)

↓

Feature Engineering/Machine learning

↓

Gold Tables (S3)

↓

PostgreSQL

↓

FastAPI

↓

Streamlit Website

↓

User


## NHL API purpose
- Collect raw NHL api Data (play by play, schedule, etc)

# Medaliion Architecture 
- https://www.databricks.com/blog/what-is-medallion-architecture

## Bronze S3 layer purpose (raw data)
- Raw NHL api data lands here (in JSON format)

## Silver S3 layer purpose (cleansed and conformed data)
- Clean data: Missing values, player IDs, Duplicate rows, Date formats, standardize data

## Gold S3 layer purpose (curated business-level tables)
- Feature engineering 
- Calculate advanced analytics 
- Build xG model
- Build Fantasy point projections 


## PostgreSQL purpose 
- Build fast queries for when someone opens up website 

## FastAPI
- https://drishinfo.com/fastapi-postgres-integration-guide/
- Higher website security
- Hide the database
- Stronger data integrity and reliability 

## Streamlit
- Display information 
- 1: Call API, 2: Receive data from API, 3: Display tables, 4: Display charts 

# Define website pages 
- What should each page on the website contain?

## Fantasy Rankings 
- Be able to input league settings so fantasy rankings can adjust accordingly 
- Value above replacement player (VORP)
- All simulated/predicted stats: goals, assists, shots, ice time, etc 


## Player Profile 
- Player advanced analytics (can select any season)
- Season totals
- Shot maps 
- Game logs
- Compare players tab
- Rolling average of last 5/10 games (implement after inital MVP)

## Team Statistics 
- Similar to player profile but team based stats and advanced analytics 

## Pipeline Status 
- Last ingestion time 
- Laset successful ETL run
- Number of games processed
- Latest season loaded
- Pipeline status
- Countdown to next xG model retrain, and previous retrain time stamp 

## Github milestones 
1. Local ingestion 
2. AWS ingestion 
3. Silver Tables
4. Gold Tables
5. PostgreSQL
6. FastAPI
7. Streamlit
8. Deployment
9. Documentation 