# Scrape Leads Workflow

**description:** Scrape B2B leads for a specific industry using Apify

---

## Gather Industry Information

The user may provide information in one of two formats:

**Option A: Simple Industry Name**
- Just the industry (e.g., "SaaS", "Real Estate", "Healthcare")
- The script will automatically generate appropriate filters

**Option B: Detailed Configuration**
- Industry name (required)
- Location/region (optional, default: "United States")
- Number of leads (optional, default: 1000)
- Specific job titles (optional override)
- Seniority levels (optional override)
- Company size (optional override)
- Any other Apify actor filters (optional)

If no industry is provided, ask the user for it.

---

## Scrape Leads Workflow

This workflow scrapes B2B leads using Apify and exports them to Google Sheets. It uses an iterative process to ensure high lead quality before scaling up.

### 1. Gather Requirements

Ask the user for:
- Target Industry/Audience (e.g., "Dentists in US", "SaaS Founders in UK")
- Any specific job titles or keywords?
- (Optional) Location overrides (default: US + Commonwealth)

### 2. Generate Filters & Test Run (Iterative Loop)

**Goal:** Achieve ≥85% relevance on a small sample (25 leads) before full scrape.

1. **Generate JSON Payload:**
   - Based on user request, create a JSON object with:
     - `contact_job_title`: Specific titles (e.g., ["Owner", "Dentist", "Partner"])
     - `company_industry`: Relevant industries (lowercase, e.g., ["medical practice", "hospital & health care"])
     - `company_keywords`: Specific keywords (e.g., ["dental", "orthodontics"])
     - `contact_location`: Target countries (lowercase, e.g., ["united states"])
     - `test_mode`: `true` (This sets fetch_count to 25)
   - **CRITICAL:** Ensure all values are **LOWERCASE** where possible (except maybe job titles if Apify allows, but industries/locations MUST be lowercase).

2. **Run Test Scrape:**
   - Execute: `python execution/scrape_leads.py <<'EOF' ... JSON ... EOF`
   - The script will print a "Lead Summary" to the console and create a test Google Sheet.

3. **Evaluate ALL 25 Results:**
   - Open the Google Sheet created by the test scrape
   - Review **ALL 25 leads** (not just the first 5-10)
   - Count how many are relevant (right decision makers + correct industry)
   - Calculate relevance percentage

4. **Decision Point:**
   - **If ≥85% relevance (21+ of 25 leads are good):**
     - Proceed to full scrape
     - Set `test_mode: false` and specify desired `max_leads`
   - **If <85% relevance:**
     - Analyze which leads were off-target
     - Adjust filters:
       - Add more specific `company_keywords`
       - Narrow `company_industry` values
       - Add negative keywords if supported
       - Adjust `contact_job_title` to be more specific
     - Re-run test with updated filters
     - Repeat until quality threshold is met

### 3. Full Scrape

Once test passes quality gate:

1. **Update Configuration:**
   ```json
   {
     "contact_job_title": ["..."],
     "company_industry": ["..."],
     "company_keywords": ["..."],
     "contact_location": ["..."],
     "test_mode": false,
     "max_leads": 1000
   }
   ```

2. **Execute Full Scrape:**
   ```bash
   python execution/scrape_leads.py <<'EOF'
   { ... full config ... }
   EOF
   ```

3. **Report Results:**
   - Total leads scraped
   - Google Sheet URL
   - Summary of lead quality

### 4. Post-Scrape Actions

After successful scrape, ask user if they want to:
- **Casualize company names** - Run `casualize_company_names_batch.py`
- **Enrich leads** - Run `enrich_leads_bulk.py` (requires Apollo.io API key)

---

## Script Reference

**Script:** `execution/scrape_leads.py`

**Input (JSON via stdin):**
```json
{
  "contact_job_title": ["Owner", "CEO", "Founder"],
  "company_industry": ["real estate", "property management"],
  "company_keywords": ["residential", "commercial"],
  "contact_location": ["united states"],
  "seniority_level": ["owner", "c_suite", "vp"],
  "company_size": ["1-10", "11-50"],
  "test_mode": true,
  "max_leads": 1000,
  "sheet_title": "Optional Custom Sheet Name"
}
```

**Output:**
- Console: Lead summary with quality details
- Google Sheet: Full lead data with all columns
- JSON result for orchestration

---

## Common Industry Filters

### Real Estate
```json
{
  "contact_job_title": ["Owner", "Broker", "Agent", "Realtor", "Managing Director"],
  "company_industry": ["real estate", "property management"],
  "company_keywords": ["residential", "commercial", "property"],
  "contact_location": ["united states"]
}
```

### Dental
```json
{
  "contact_job_title": ["Owner", "Dentist", "Partner", "Managing Partner"],
  "company_industry": ["medical practice", "hospital & health care", "health care"],
  "company_keywords": ["dental", "dentist", "orthodontics", "oral"],
  "contact_location": ["united states"]
}
```

### SaaS/Tech
```json
{
  "contact_job_title": ["Founder", "CEO", "CTO", "VP Engineering"],
  "company_industry": ["computer software", "information technology"],
  "company_keywords": ["saas", "software", "platform", "cloud"],
  "contact_location": ["united states"]
}
```

### Law Firms
```json
{
  "contact_job_title": ["Partner", "Managing Partner", "Founding Partner", "Attorney"],
  "company_industry": ["law practice", "legal services"],
  "company_keywords": ["law", "attorney", "legal"],
  "contact_location": ["united states"]
}
```

---

## Troubleshooting

**No leads returned:**
- Broaden industry filters
- Use more general job titles
- Check that all values are lowercase

**Low quality leads:**
- Add more specific keywords
- Narrow industry selection
- Add seniority level filters

**API errors:**
- Verify APIFY_API_TOKEN is set correctly
- Check Apify account credits/limits

