# Agent Tools Reference

This document defines the execution tools available to the agent.

## Tool: scrape_leads

**Description**: Scrape B2B leads using Apify and export to Google Sheets

**Script**: `execution/scrape_leads.py`

**Input Schema**:
```json
{
  "contact_job_title": ["string"],     // Job titles to target
  "company_industry": ["string"],       // Industries (MUST be lowercase)
  "company_keywords": ["string"],       // Company keywords
  "contact_location": ["string"],       // Locations (MUST be lowercase)
  "seniority_level": ["string"],        // Optional: owner, c_suite, vp, etc.
  "company_size": ["string"],           // Optional: 1-10, 11-50, etc.
  "test_mode": true,                    // true for 25 leads, false for full
  "max_leads": 1000,                    // Max leads for full mode
  "sheet_title": "string"               // Optional: Custom sheet name
}
```

**Output**:
```json
{
  "success": true,
  "lead_count": 25,
  "sheet_url": "https://docs.google.com/spreadsheets/d/xxx/edit",
  "test_mode": true
}
```

**Required Environment**:
- `APIFY_API_TOKEN` in .env
- Google Sheets OAuth token

---

## Tool: enrich_leads

**Description**: Enrich lead data using Apollo.io API

**Script**: `execution/enrich_leads_bulk.py`

**Input Schema**:
```json
{
  "sheet_url": "string",           // Google Sheet URL or ID (required)
  "batch_size": 10,                // Rows per batch (optional)
  "enrich_empty_only": true        // Only fill empty fields (optional)
}
```

**Output**:
```json
{
  "success": true,
  "processed": 100,
  "enriched": 85,
  "errors": 15,
  "sheet_url": "https://docs.google.com/spreadsheets/d/xxx/edit"
}
```

**Required Environment**:
- `APOLLO_API_KEY` in .env
- Google Sheets OAuth token

---

## Tool: casualize_company_names

**Description**: Convert formal company names to casual versions for cold email

**Script**: `execution/casualize_company_names_batch.py`

**Input Schema**:
```json
{
  "sheet_url": "string"    // Google Sheet URL or ID (required)
}
```

**Output**:
```json
{
  "success": true,
  "processed": 100,
  "sheet_url": "https://docs.google.com/spreadsheets/d/xxx/edit"
}
```

**Required Environment**:
- Google Sheets OAuth token

---

## Tool: google_sheets_auth

**Description**: One-time OAuth setup for Google Sheets access

**Script**: `execution/google_sheets_auth.py`

**Input**: None (run directly)

**Output**: OAuth token saved to `~/.gemini/google_sheets_token.pickle`

**Required Environment**:
- `~/.gemini/credentials.json` (Google Cloud OAuth credentials)

---

## Execution Pattern

All tools read JSON configuration from stdin:

```bash
python execution/tool_name.py <<'EOF'
{
  "param": "value"
}
EOF
```

## Error Handling

Scripts return non-zero exit codes on failure. Check for:
- Exit code 1: Configuration or input error
- Exit code 2: API error (Apify, Apollo, Google)
- Exit code 3: Authentication error

Parse `__RESULT_JSON__:` line from output for structured results.

## Rate Limits

- **Apify**: Depends on subscription, typically no per-minute limit
- **Apollo.io**: 50-200 requests/minute depending on plan
- **Google Sheets**: 100 requests/100 seconds per user

Scripts handle rate limiting internally with delays and retries.

