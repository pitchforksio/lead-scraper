# Lead Scraper Agent

A 3-layer agentic workflow system for B2B lead generation, enrichment, and cold email preparation.

## Architecture

```
┌─────────────────────────────────────┐
│           DIRECTIVE LAYER           │
│    /directives/*.md (SOPs)          │
└──────────────────┬──────────────────┘
                   ▼
┌─────────────────────────────────────┐
│        ORCHESTRATION LAYER          │
│   AI Agent (Cursor) reads SOPs,     │
│   plans tasks, executes scripts     │
└──────────────────┬──────────────────┘
                   ▼
┌─────────────────────────────────────┐
│          EXECUTION LAYER            │
│    /execution/*.py (Tools)          │
└─────────────────────────────────────┘
```

## Quick Start

### 1. Install Dependencies
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Set Up Google Sheets OAuth
```bash
# Place your Google Cloud credentials.json at ~/.gemini/credentials.json
python execution/google_sheets_auth.py
```

### 4. Use with Cursor
Open this folder in Cursor and use the chat to run workflows:
- "Scrape 200 realtors in Texas"
- "Enrich the leads in [sheet URL]"
- "Casualize company names in [sheet URL]"

## Workflows

### Scrape Leads (`scrape_leads`)
Scrapes B2B leads using Apify's leads-finder actor.
- Input: Industry, location, job titles, keywords
- Output: Google Sheet with lead data
- Features: Test mode (25 leads) for quality validation

### Enrich Leads (`enrich_leads`)  
Enriches lead data using Apollo.io API.
- Input: Google Sheet URL with leads
- Output: Updated sheet with enriched data

### Casualize Company Names (`casualize_company_names`)
Converts formal company names to casual versions for cold email.
- "CKJ & Associates LLC" → "CKJ"
- "Johnson Medical Group Inc." → "Johnson Medical"

## File Structure

```
lead-scraper/
├── .agent/              # Agent configuration for Cursor
├── directives/          # Workflow SOPs (markdown)
│   ├── scrape_leads.md
│   ├── enrich_leads.md
│   └── casualize_company_names.md
├── execution/           # Python execution scripts
│   ├── google_sheets_auth.py
│   ├── scrape_leads.py
│   ├── enrich_leads_bulk.py
│   └── casualize_company_names_batch.py
├── tmp/                 # Temporary working files
├── .env                 # Environment variables (create from .env.example)
├── requirements.txt     # Python dependencies
└── README.md
```

## API Keys Required

1. **Apify API Token**: Get from [Apify Console](https://console.apify.com/account/integrations)
2. **Apollo.io API Key**: Get from [Apollo Settings](https://app.apollo.io/#/settings/integrations/api)
3. **Google Cloud OAuth**: Create credentials in [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
   - Enable Google Sheets API and Google Drive API
   - Create OAuth 2.0 Client ID (Desktop App)
   - Download credentials.json

