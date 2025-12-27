# Lyftr AI – Backend Assignment

## Overview

A production-style FastAPI service that ingests signed webhook messages,
stores them idempotently, and exposes analytics, metrics, and health endpoints.
The service is fully Dockerized and designed with security, correctness,
and observability in mind.

## Tech Stack

- Python 3.11
- FastAPI
- SQLite
- Docker & Docker Compose

## Project Structure

app/
├── main.py            # FastAPI application and routes  
├── models.py          # Database initialization and connection  
├── storage.py         # Message persistence and queries  
├── metrics.py         # In-memory metrics counters  
├── logging_utils.py   # Structured JSON logging  
├── config.py          # Environment configuration  
Dockerfile  
docker-compose.yml  
requirements.txt  
README.md  

## How to Run

docker compose up -d --build
The service will be available at:

arduino
Copy code
http://localhost:8000
Interactive API documentation:

bash
Copy code
http://localhost:8000/docs
API Endpoints
POST /webhook
Validates HMAC signature using X-Signature

Validates request payload schema

Validates E.164 phone numbers

Stores messages idempotently

Returns 200 OK for duplicate messages

GET /messages
Supports pagination (limit, offset)

Supports filtering by sender, timestamp, and text query

GET /stats
Returns aggregate analytics:

Total messages

Unique senders

Top senders

First and last message timestamps

GET /metrics
Exposes in-memory counters in text/plain format

Designed for Prometheus-style scraping

Health Checks
/health/live — Liveness probe

/health/ready — Readiness probe (checks DB and environment)

Environment Variables
Variable	Description
DATABASE_URL	SQLite database path
WEBHOOK_SECRET	Secret used for HMAC verification
LOG_LEVEL	Logging level (default: INFO)
