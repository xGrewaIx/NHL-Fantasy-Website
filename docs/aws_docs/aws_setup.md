# AWS Setup

This document describes the AWS configuration and infrastructure used by the NHL Fantasy Platform.

The project uses AWS to provide cloud-based storage, data processing, monitoring, and application infrastructure.

## 1. AWS Configuration

- Cloud Provider: AWS 
- Primary Region: ca-west-1
- Environment: Development 
- CLI: AWS CLI v2 
- Authentication: IAM (Do not use root user) 
- Project: NHL Fantasy Website/Platform

## 2. Authentication & Security

The AWS root account is used only for account-level configuration. Day-to-day development is performed using an IAM development identity.

Security practices:

- Root account protected with MFA
- IAM used for development access
- Assigne specific permissions to IAM (only the one the IAM needs)
- AWS credentials kept outside the repository
- No credentials hard-coded in application code
- S3 buckets kept private
- S3 Block Public Access enabled

### Secrets

The following must never be committed to GitHub:

- AWS access keys
- AWS secret keys
- AWS session tokens
- Database passwords
- API keys
- .env files containing secrets
- Private certificates or keys


## 3. AWS Architecture

The platform follows a layered cloud architecture:

```text
                    NHL API
                       |
                       v
               Data Ingestion
                       |
                       v
              +----------------+
              |   S3 Bronze    |
              |    Raw Data    |
              +----------------+
                       |
                       v
              +----------------+
              |   S3 Silver    |
              | Cleaned Data   |
              +----------------+
                       |
                       v
              +----------------+
              |    S3 Gold     |
              | Analytics Data |
              +----------------+
                       |
             +---------+---------+
             |                   |
             v                   v
       PostgreSQL              Models
             |                   |
             +---------+---------+
                       |
                       v
                    FastAPI
                       |
                       v
                  Streamlit
```

## 4. AWS Services used or to be used

- Amazon s3: Object Storage
- AWS IAM: Authentication + Authorization
- Amazon CloudWatch: Monitoring and Logging
- Amazon RDS: PostgreSQL Database
- AWS compute: Containerized application deplyment
- AWS Lambda: Event driven code workloads 

## 5. Cost management 

- Only use one AWS region
- Only use services that are needed
- Created an AWS budget

## 6. Resource naming

Follow a consistent naming convention:


