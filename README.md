# NHL Fantasy Platform

> **Work in Progress — Active Development**

An end-to-end NHL data engineering, analytics, and fantasy hockey platform designed to demonstrate a production-style data pipeline from data ingestion to analytics and application serving.

The project is currently under active development. Features and architecture will be added incrementally as development progresses.

## Planned Features

- NHL data ingestion
- Bronze / Silver / Gold data architecture
- PySpark and Spark SQL data processing
- xG (Expected Goals) modeling
- Player and team analytics
- Fantasy hockey rankings
- Fantasy trade analysis
- Linemate analysis
- FastAPI backend
- Streamlit frontend
- PostgreSQL analytical warehouse
- AWS-based data pipeline
- Automated and near-real-time data updates
- Data quality checks and testing
- Dockerized applications

## Current Status

The project is currently focused on building the **data ingestion and raw data storage layer**.

Current development includes:

- NHL API client
- Schedule ingestion
- Date-level schedule extraction
- Boxscore ingestion
- Play-by-play ingestion
- Local Bronze data storage
- Integration testing
- Logging and ingestion summaries

Future development will progressively add the transformation, analytics, machine learning, database, API, frontend, cloud, and orchestration layers.

## Development Setup

### Requirements

- Python 3.12
- [uv](https://docs.astral.sh/uv/)

### Install uv

```bash
python -m pip install uv