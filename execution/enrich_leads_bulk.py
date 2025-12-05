"""
Lead Enrichment - Apollo.io Integration

Enriches lead data using Apollo.io's People Enrichment API.
Reads leads from a Google Sheet, enriches them, and updates the sheet.

Usage:
    python enrich_leads_bulk.py <<'EOF'
    {
        "sheet_url": "https://docs.google.com/spreadsheets/d/xxx/edit",
        "batch_size": 10,
        "enrich_empty_only": true
    }
    EOF
"""

import os
import sys
import json
import re
import time
import pickle
from typing import Dict, Any, List, Optional

import requests
import gspread
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# Try to load dotenv if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Configuration
APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")
APOLLO_API_BASE = "https://api.apollo.io/v1"

# Google Sheets OAuth token storage
TOKEN_PATH = os.path.expanduser("~/.gemini/google_sheets_token.pickle")

# Rate limiting
REQUESTS_PER_MINUTE = 50  # Apollo's rate limit varies by plan
REQUEST_DELAY = 60 / REQUESTS_PER_MINUTE  # Delay between requests

# Fields that Apollo can enrich
APOLLO_ENRICHABLE_FIELDS = {
    # Person fields
    "first_name": "first_name",
    "last_name": "last_name",
    "full_name": "name",
    "job_title": "title",
    "headline": "headline",
    "seniority_level": "seniority",
    "linkedin": "linkedin_url",
    "city": "city",
    "state": "state",
    "country": "country",
    # Company fields
    "company_name": "organization.name",
    "company_domain": "organization.primary_domain",
    "company_website": "organization.website_url",
    "company_linkedin": "organization.linkedin_url",
    "company_size": "organization.estimated_num_employees",
    "industry": "organization.industry",
    "company_description": "organization.short_description",
    "company_annual_revenue": "organization.annual_revenue_printed",
    "company_phone_number": "organization.phone",
    "company_city": "organization.city",
    "company_keywords": "organization.keywords",
    "company_tech_stack": "organization.technologies",
}


def get_google_sheets_client() -> gspread.Client:
    """Get authenticated Google Sheets client."""
    if not os.path.exists(TOKEN_PATH):
        raise FileNotFoundError(
            f"Google Sheets token not found at {TOKEN_PATH}. "
            "Please run: python execution/google_sheets_auth.py"
        )
    
    with open(TOKEN_PATH, 'rb') as token:
        creds = pickle.load(token)
    
    # Refresh if expired
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_PATH, 'wb') as token:
            pickle.dump(creds, token)
    
    return gspread.authorize(creds)


def extract_sheet_id(url: str) -> str:
    """Extract the spreadsheet ID from a Google Sheets URL."""
    patterns = [
        r'/spreadsheets/d/([a-zA-Z0-9-_]+)',
        r'id=([a-zA-Z0-9-_]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    if re.match(r'^[a-zA-Z0-9-_]+$', url):
        return url
    
    raise ValueError(f"Could not extract spreadsheet ID from: {url}")


def enrich_person_apollo(email: str = None, linkedin_url: str = None, 
                         first_name: str = None, last_name: str = None,
                         company_name: str = None, company_domain: str = None) -> Optional[Dict[str, Any]]:
    """
    Enrich a person using Apollo.io API.
    
    Args:
        email: Person's email address
        linkedin_url: Person's LinkedIn URL
        first_name: Person's first name
        last_name: Person's last name
        company_name: Company name
        company_domain: Company domain
        
    Returns:
        Dict with enriched data or None if not found
    """
    if not APOLLO_API_KEY:
        raise ValueError("APOLLO_API_KEY not found in environment variables")
    
    # Build request payload
    payload = {}
    
    if email:
        payload["email"] = email
    if linkedin_url:
        payload["linkedin_url"] = linkedin_url
    if first_name:
        payload["first_name"] = first_name
    if last_name:
        payload["last_name"] = last_name
    if company_name:
        payload["organization_name"] = company_name
    if company_domain:
        payload["domain"] = company_domain
    
    if not payload:
        return None
    
    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
    }
    
    # Apollo API uses api_key in the payload for some endpoints
    payload["api_key"] = APOLLO_API_KEY
    
    try:
        response = requests.post(
            f"{APOLLO_API_BASE}/people/match",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("person")
        elif response.status_code == 429:
            # Rate limited - wait and return None
            print("  ⚠️ Rate limited, waiting 60 seconds...")
            time.sleep(60)
            return None
        else:
            print(f"  ⚠️ Apollo API error {response.status_code}: {response.text[:100]}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"  ⚠️ Request error: {e}")
        return None


def get_nested_value(data: Dict[str, Any], path: str) -> Any:
    """Get a nested value from a dictionary using dot notation."""
    keys = path.split(".")
    value = data
    
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return None
    
    return value


def extract_enriched_data(apollo_data: Dict[str, Any]) -> Dict[str, str]:
    """Extract relevant fields from Apollo response."""
    enriched = {}
    
    for sheet_field, apollo_path in APOLLO_ENRICHABLE_FIELDS.items():
        value = get_nested_value(apollo_data, apollo_path)
        
        if value is not None:
            # Handle lists (keywords, technologies)
            if isinstance(value, list):
                value = ", ".join(str(v) for v in value[:10])  # Limit to 10 items
            enriched[sheet_field] = str(value) if value else ""
    
    return enriched


def process_sheet(sheet_url: str, batch_size: int = 10, 
                  enrich_empty_only: bool = True) -> Dict[str, Any]:
    """
    Process a Google Sheet, enriching lead data with Apollo.io.
    
    Args:
        sheet_url: URL or ID of the Google Sheet
        batch_size: Number of rows to process at a time
        enrich_empty_only: Only enrich rows with missing data
        
    Returns:
        Dict with processing results
    """
    gc = get_google_sheets_client()
    
    # Extract sheet ID and open
    sheet_id = extract_sheet_id(sheet_url)
    print(f"Opening spreadsheet: {sheet_id}")
    
    spreadsheet = gc.open_by_key(sheet_id)
    worksheet = spreadsheet.sheet1
    
    # Get all data
    all_data = worksheet.get_all_records()
    headers = worksheet.row_values(1)
    
    if not all_data:
        return {
            "success": True,
            "processed": 0,
            "enriched": 0,
            "message": "Sheet is empty"
        }
    
    # Create column index mapping
    col_index = {header: i + 1 for i, header in enumerate(headers)}
    
    processed = 0
    enriched = 0
    errors = 0
    
    print(f"\nProcessing {len(all_data)} rows...")
    print(f"Batch size: {batch_size}")
    print(f"Enrich empty only: {enrich_empty_only}")
    print("-" * 40)
    
    updates = []
    
    for i, row in enumerate(all_data):
        row_num = i + 2  # Account for header row and 1-indexing
        
        # Check if row needs enrichment
        email = row.get("email", "")
        linkedin = row.get("linkedin", "")
        first_name = row.get("first_name", "")
        last_name = row.get("last_name", "")
        company_name = row.get("company_name", "")
        company_domain = row.get("company_domain", "")
        
        # Skip if no identifying info
        if not email and not linkedin and not (first_name and company_name):
            continue
        
        # Check if enrichment is needed
        if enrich_empty_only:
            # Check if key fields are already filled
            has_data = bool(
                row.get("job_title") and 
                row.get("company_size") and
                row.get("industry")
            )
            if has_data:
                continue
        
        # Enrich the lead
        print(f"  Row {row_num}: Enriching {first_name} {last_name} ({email or linkedin[:30] if linkedin else 'no email'})...")
        
        apollo_data = enrich_person_apollo(
            email=email,
            linkedin_url=linkedin,
            first_name=first_name,
            last_name=last_name,
            company_name=company_name,
            company_domain=company_domain
        )
        
        processed += 1
        
        if apollo_data:
            enriched_fields = extract_enriched_data(apollo_data)
            
            # Prepare updates for this row
            for field, value in enriched_fields.items():
                if field in col_index and value:
                    # Only update if field is empty or we're overwriting
                    current_value = row.get(field, "")
                    if not current_value or not enrich_empty_only:
                        updates.append({
                            "range": gspread.utils.rowcol_to_a1(row_num, col_index[field]),
                            "values": [[value]]
                        })
            
            enriched += 1
            print(f"    ✅ Enriched with {len(enriched_fields)} fields")
        else:
            errors += 1
            print(f"    ⚠️ No data found")
        
        # Batch update every batch_size rows
        if len(updates) >= batch_size * 5:  # Assuming ~5 fields per lead
            print(f"\n  Saving batch ({len(updates)} updates)...")
            worksheet.batch_update(updates)
            updates = []
        
        # Rate limiting
        time.sleep(REQUEST_DELAY)
        
        # Progress update
        if processed % 10 == 0:
            print(f"\n  Progress: {processed} processed, {enriched} enriched, {errors} not found\n")
    
    # Final batch update
    if updates:
        print(f"\n  Saving final batch ({len(updates)} updates)...")
        worksheet.batch_update(updates)
    
    return {
        "success": True,
        "processed": processed,
        "enriched": enriched,
        "errors": errors,
        "sheet_url": f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
    }


def main():
    """Main entry point."""
    # Read JSON input from stdin
    print("Reading configuration from stdin...")
    
    try:
        input_data = sys.stdin.read()
        if not input_data.strip():
            print("Error: No input provided. Please provide JSON configuration via stdin.")
            print("\nExample:")
            print('python enrich_leads_bulk.py <<\'EOF\'')
            print('{')
            print('    "sheet_url": "https://docs.google.com/spreadsheets/d/xxx/edit",')
            print('    "batch_size": 10,')
            print('    "enrich_empty_only": true')
            print('}')
            print('EOF')
            return 1
        
        config = json.loads(input_data)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}")
        return 1
    
    # Validate API key
    if not APOLLO_API_KEY:
        print("Error: APOLLO_API_KEY not found in environment variables")
        print("Please set it in your .env file or environment")
        return 1
    
    sheet_url = config.get("sheet_url")
    if not sheet_url:
        print("Error: 'sheet_url' is required in the configuration")
        return 1
    
    batch_size = config.get("batch_size", 10)
    enrich_empty_only = config.get("enrich_empty_only", True)
    
    print(f"\n{'='*60}")
    print("Lead Enrichment - Apollo.io")
    print('='*60)
    
    try:
        result = process_sheet(sheet_url, batch_size, enrich_empty_only)
        
        print(f"\n{'='*60}")
        print("✅ ENRICHMENT COMPLETE")
        print('='*60)
        print(f"Rows Processed: {result['processed']}")
        print(f"Successfully Enriched: {result['enriched']}")
        print(f"Not Found: {result.get('errors', 0)}")
        print(f"Sheet URL: {result['sheet_url']}")
        
        # Output result as JSON for orchestration layer
        print(f"\n__RESULT_JSON__:{json.dumps(result)}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

