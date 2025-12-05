# Enrich Leads Workflow

**description:** Enrich lead data using Apollo.io API

---

## Overview

This workflow enriches existing lead data in a Google Sheet using Apollo.io's People Enrichment API. It adds missing information like job titles, company details, and contact information.

---

## Prerequisites

1. **Apollo.io API Key** - Set in `.env` as `APOLLO_API_KEY`
2. **Google Sheet with leads** - Must have at least one of:
   - Email address
   - LinkedIn URL
   - First name + Company name

---

## Workflow Steps

### 1. Gather Requirements

Ask the user for:
- Google Sheet URL containing leads to enrich
- Whether to only enrich rows with missing data (default: yes)
- Batch size for processing (default: 10)

### 2. Validate Setup

Before running, verify:
- `APOLLO_API_KEY` is set in environment
- Google Sheet is accessible
- Sheet has required columns (email, linkedin, first_name, company_name)

### 3. Execute Enrichment

Run the enrichment script:

```bash
python execution/enrich_leads_bulk.py <<'EOF'
{
    "sheet_url": "https://docs.google.com/spreadsheets/d/xxx/edit",
    "batch_size": 10,
    "enrich_empty_only": true
}
EOF
```

**Parameters:**
- `sheet_url` (required): Google Sheet URL or ID
- `batch_size` (optional, default: 10): Rows to process before saving
- `enrich_empty_only` (optional, default: true): Only fill empty fields

### 4. Monitor Progress

The script will output:
- Row-by-row progress
- Success/failure for each enrichment
- Running totals

### 5. Report Results

After completion, report to user:
- Total rows processed
- Successfully enriched count
- Failed/not found count
- Link to updated Google Sheet

---

## Script Reference

**Script:** `execution/enrich_leads_bulk.py`

**Input (JSON via stdin):**
```json
{
  "sheet_url": "https://docs.google.com/spreadsheets/d/xxx/edit",
  "batch_size": 10,
  "enrich_empty_only": true
}
```

**Output:**
- Console: Progress updates and summary
- Google Sheet: Updated with enriched data
- JSON result for orchestration

---

## Fields Enriched

The following fields can be enriched from Apollo:

### Person Fields
- `first_name` - First name
- `last_name` - Last name
- `full_name` - Full name
- `job_title` - Current job title
- `headline` - LinkedIn headline
- `seniority_level` - Seniority (C-Suite, VP, Manager, etc.)
- `linkedin` - LinkedIn profile URL
- `city` - City
- `state` - State/Region
- `country` - Country

### Company Fields
- `company_name` - Company name
- `company_domain` - Company website domain
- `company_website` - Full website URL
- `company_linkedin` - Company LinkedIn page
- `company_size` - Employee count range
- `industry` - Primary industry
- `company_description` - Company description
- `company_annual_revenue` - Annual revenue estimate
- `company_phone_number` - Company phone
- `company_city` - Company headquarters city
- `company_keywords` - Industry keywords
- `company_tech_stack` - Technologies used

---

## Rate Limiting

Apollo.io has rate limits based on your plan:
- Free: 50 requests/minute
- Basic: 100 requests/minute
- Professional: 200 requests/minute

The script automatically rate-limits to avoid errors. For large datasets, expect:
- 1000 leads ≈ 20-40 minutes
- Processing happens in batches with saves

---

## Troubleshooting

**"APOLLO_API_KEY not found":**
- Add your API key to `.env`: `APOLLO_API_KEY=your_key_here`
- Restart your terminal/IDE

**"Rate limited" errors:**
- Script will automatically wait and retry
- Consider processing during off-peak hours

**Low match rate:**
- Ensure email addresses are valid
- LinkedIn URLs improve match rates
- First name + company name can work without email

**Missing fields after enrichment:**
- Apollo may not have data for all contacts
- Some fields depend on company data availability
- Premium Apollo plans have more data access

---

## Best Practices

1. **Run after scraping** - Enrich freshly scraped leads for best results
2. **Use `enrich_empty_only: true`** - Avoid overwriting good data
3. **Start with small batches** - Test with 10-20 leads first
4. **Monitor API usage** - Check Apollo dashboard for credits
5. **Combine with casualize** - Run casualize after enrichment for complete data

