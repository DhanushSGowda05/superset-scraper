# Superset Job Scraper

A Python-based automation tool that scrapes job listings from Superset and maintains an up-to-date Google Sheet.

## Features

- Scrapes job listings from Superset using Playwright
- Extracts key job information:
  - Company
  - Role
  - Job Type
  - Location
  - Posted Date
  - Category
  - Job Function
  - CTC
  - CGPA requirement
  - Eligibility
- Uses the last processed job as a checkpoint to detect new listings
- Adds new jobs to Google Sheets in chronological order
- Maintains a separate `Active Applications` sheet for applied jobs
- Preserves existing application and offer-status information
- Uses persistent browser data for Superset authentication
- Keeps credentials and environment variables out of Git

## Tech Stack

- Python
- Playwright
- gspread
- Google Sheets API
- python-dotenv

## How It Works

```text
Superset
   ↓
Playwright Scraper
   ↓
Detect New Jobs
   ↓
Google Sheets
   ↓
Active Applications