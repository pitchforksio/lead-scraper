"""
Lead Scraper - Apify Integration

Scrapes B2B leads using Apify's leads-finder actor and exports to Google Sheets.
Supports test mode (25 leads) for quality validation before full scrape.

Usage:
    python scrape_leads.py <<'EOF'
    {
        "contact_job_title": ["Owner", "Founder", "CEO"],
        "company_industry": ["real estate"],
        "company_keywords": ["residential", "commercial"],
        "contact_location": ["united states"],
        "test_mode": true
    }
    EOF
"""

import os
import sys
import json
import time
import pickle
from datetime import datetime
from typing import Dict, Any, List, Optional

from apify_client import ApifyClient
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
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
APIFY_ACTOR_ID = "code_crafter/leads-finder"

# Google Sheets OAuth token storage
TOKEN_PATH = os.path.expanduser("~/.gemini/google_sheets_token.pickle")

# Google Sheets scopes
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# Default lead count
DEFAULT_LEAD_COUNT = 1000
TEST_MODE_LEAD_COUNT = 25

# Google Sheet columns - matches the structure from the reference
SHEET_COLUMNS = [
    "first_name",
    "last_name",
    "full_name",
    "job_title",
    "headline",
    "functional_level",
    "seniority_level",
    "email",
    "linkedin",
    "city",
    "state",
    "country",
    "company_name",
    "company_domain",
    "company_website",
    "company_linkedin",
    "company_size",
    "industry",
    "company_description",
    "company_annual_revenue",
    "company_total_funding",
    "company_phone_number",
    "company_city",
    "company_keywords",
    "company_tech_stack",
    "casual_company_name"
]


def print_lead_summary(leads: List[Dict[str, Any]], limit: int = 25):
    """Print a summary of ALL leads for quality evaluation in test mode."""
    actual_limit = min(len(leads), limit)
    print(f"\n{'='*60}")
    print(f"Lead Summary (All {actual_limit} of {len(leads)})")
    print('='*60)
    
    for i, lead in enumerate(leads[:actual_limit]):
        print(f"\n{i+1}. {lead.get('full_name', 'N/A')} - {lead.get('job_title', 'N/A')}")
        print(f"   Company: {lead.get('company_name', 'N/A')} ({lead.get('industry', 'N/A')})")
        print(f"   Location: {lead.get('city', '')}, {lead.get('state', '')}, {lead.get('country', '')}")
        print(f"   Email: {lead.get('email', 'N/A')}")
        print("-" * 40)
    
    if len(leads) > limit:
        print(f"\n📊 {len(leads) - limit} more leads available in the Google Sheet.")


def run_apify_actor(filters: Dict[str, Any]) -> Dict[str, Any]:
    """Run the Apify leads-finder actor with specified filters."""
    if not APIFY_API_TOKEN:
        raise ValueError("APIFY_API_TOKEN not found in environment variables")
    
    client = ApifyClient(APIFY_API_TOKEN)
    run_id = None
    
    try:
        print(f"Starting Apify actor with filters: {json.dumps(filters, indent=2)}")
        
        # Build the actor input
        actor_input = build_actor_input(filters)
        
        # Run the actor
        run = client.actor(APIFY_ACTOR_ID).call(run_input=actor_input)
        run_id = run.get("id")
        
        print(f"Actor run started with ID: {run_id}")
        
        # Get the results from the dataset
        dataset_id = run.get("defaultDatasetId")
        if not dataset_id:
            raise ValueError("No dataset ID returned from actor run")
        
        # Fetch results
        items = list(client.dataset(dataset_id).iterate_items())
        print(f"Retrieved {len(items)} leads from Apify")
        
        return {
            "success": True,
            "run_id": run_id,
            "leads": items,
            "count": len(items)
        }
        
    except Exception as e:
        print(f"Error running Apify actor: {e}")
        return {
            "success": False,
            "error": str(e),
            "run_id": run_id,
            "leads": [],
            "count": 0
        }


def build_actor_input(filters: Dict[str, Any]) -> Dict[str, Any]:
    """Build the Apify actor input from user filters."""
    test_mode = filters.get("test_mode", False)
    max_leads = TEST_MODE_LEAD_COUNT if test_mode else filters.get("max_leads", DEFAULT_LEAD_COUNT)
    
    actor_input = {
        "maxLeads": max_leads
    }
    
    # Map filter fields to actor input
    # Contact job titles
    if "contact_job_title" in filters:
        titles = filters["contact_job_title"]
        if isinstance(titles, list):
            actor_input["jobTitles"] = titles
        else:
            actor_input["jobTitles"] = [titles]
    
    # Company industry (must be lowercase)
    if "company_industry" in filters:
        industries = filters["company_industry"]
        if isinstance(industries, list):
            actor_input["industries"] = [i.lower() for i in industries]
        else:
            actor_input["industries"] = [industries.lower()]
    
    # Company keywords
    if "company_keywords" in filters:
        keywords = filters["company_keywords"]
        if isinstance(keywords, list):
            actor_input["keywords"] = keywords
        else:
            actor_input["keywords"] = [keywords]
    
    # Contact location (must be lowercase)
    if "contact_location" in filters:
        locations = filters["contact_location"]
        if isinstance(locations, list):
            actor_input["locations"] = [loc.lower() for loc in locations]
        else:
            actor_input["locations"] = [locations.lower()]
    
    # Seniority levels
    if "seniority_level" in filters:
        levels = filters["seniority_level"]
        if isinstance(levels, list):
            actor_input["seniorityLevels"] = levels
        else:
            actor_input["seniorityLevels"] = [levels]
    
    # Company size
    if "company_size" in filters:
        sizes = filters["company_size"]
        if isinstance(sizes, list):
            actor_input["companySizes"] = sizes
        else:
            actor_input["companySizes"] = [sizes]
    
    return actor_input


def normalize_lead(raw_lead: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a lead from Apify format to our standard format."""
    # Handle nested person data
    person = raw_lead.get("person", raw_lead)
    company = raw_lead.get("company", {})
    
    # If the data is flat (not nested), use raw_lead directly
    if not raw_lead.get("person"):
        person = raw_lead
        company = raw_lead
    
    normalized = {
        "first_name": person.get("firstName", person.get("first_name", "")),
        "last_name": person.get("lastName", person.get("last_name", "")),
        "full_name": person.get("fullName", person.get("full_name", "")),
        "job_title": person.get("jobTitle", person.get("job_title", person.get("title", ""))),
        "headline": person.get("headline", ""),
        "functional_level": person.get("functionalLevel", person.get("functional_level", "")),
        "seniority_level": person.get("seniorityLevel", person.get("seniority_level", "")),
        "email": person.get("email", ""),
        "linkedin": person.get("linkedinUrl", person.get("linkedin", person.get("linkedin_url", ""))),
        "city": person.get("city", ""),
        "state": person.get("state", ""),
        "country": person.get("country", ""),
        "company_name": company.get("name", company.get("company_name", "")),
        "company_domain": company.get("domain", company.get("company_domain", "")),
        "company_website": company.get("website", company.get("company_website", "")),
        "company_linkedin": company.get("linkedinUrl", company.get("company_linkedin", "")),
        "company_size": company.get("size", company.get("company_size", "")),
        "industry": company.get("industry", ""),
        "company_description": company.get("description", company.get("company_description", "")),
        "company_annual_revenue": company.get("annualRevenue", company.get("company_annual_revenue", "")),
        "company_total_funding": company.get("totalFunding", company.get("company_total_funding", "")),
        "company_phone_number": company.get("phone", company.get("company_phone_number", "")),
        "company_city": company.get("city", company.get("company_city", "")),
        "company_keywords": ", ".join(company.get("keywords", [])) if isinstance(company.get("keywords"), list) else company.get("company_keywords", ""),
        "company_tech_stack": ", ".join(company.get("techStack", [])) if isinstance(company.get("techStack"), list) else company.get("company_tech_stack", ""),
        "casual_company_name": ""  # Will be filled by casualize script
    }
    
    # Build full name if not provided
    if not normalized["full_name"] and (normalized["first_name"] or normalized["last_name"]):
        normalized["full_name"] = f"{normalized['first_name']} {normalized['last_name']}".strip()
    
    return normalized


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


def create_google_sheet(leads: List[Dict[str, Any]], title: Optional[str] = None) -> str:
    """
    Create a new Google Sheet with the leads data.
    
    Args:
        leads: List of normalized lead dictionaries
        title: Optional sheet title (defaults to timestamped name)
        
    Returns:
        str: URL of the created Google Sheet
    """
    gc = get_google_sheets_client()
    
    # Generate title if not provided
    if not title:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        title = f"Leads_{timestamp}"
    
    print(f"Creating Google Sheet: {title}")
    
    # Create the spreadsheet
    spreadsheet = gc.create(title)
    worksheet = spreadsheet.sheet1
    
    # Set up headers
    worksheet.update('A1', [SHEET_COLUMNS])
    
    # Format header row (bold)
    worksheet.format('A1:Z1', {
        'textFormat': {'bold': True},
        'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
    })
    
    # Prepare data rows
    rows = []
    for lead in leads:
        row = [str(lead.get(col, "")) for col in SHEET_COLUMNS]
        rows.append(row)
    
    # Write all data at once (more efficient)
    if rows:
        end_row = len(rows) + 1
        worksheet.update(f'A2:Z{end_row}', rows)
    
    # Auto-resize columns (best effort)
    try:
        worksheet.columns_auto_resize(0, len(SHEET_COLUMNS))
    except Exception:
        pass  # Column resize may not be supported in all cases
    
    sheet_url = spreadsheet.url
    print(f"✅ Created Google Sheet: {sheet_url}")
    
    return sheet_url


def main():
    """Main entry point for the lead scraper."""
    # Read JSON input from stdin
    print("Reading filter configuration from stdin...")
    
    try:
        input_data = sys.stdin.read()
        if not input_data.strip():
            print("Error: No input provided. Please provide JSON configuration via stdin.")
            print("\nExample:")
            print('python scrape_leads.py <<\'EOF\'')
            print('{')
            print('    "contact_job_title": ["Owner", "CEO"],')
            print('    "company_industry": ["real estate"],')
            print('    "contact_location": ["united states"],')
            print('    "test_mode": true')
            print('}')
            print('EOF')
            return 1
        
        filters = json.loads(input_data)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}")
        return 1
    
    test_mode = filters.get("test_mode", False)
    print(f"\n{'='*60}")
    print(f"Lead Scraper - {'TEST MODE (25 leads)' if test_mode else 'FULL MODE'}")
    print('='*60)
    
    # Run the Apify actor
    result = run_apify_actor(filters)
    
    if not result["success"]:
        print(f"\n❌ Failed to scrape leads: {result.get('error')}")
        return 1
    
    leads = result["leads"]
    if not leads:
        print("\n⚠️ No leads found with the specified filters.")
        print("Try adjusting your filters (broader industry, different job titles, etc.)")
        return 0
    
    # Normalize the leads
    print(f"\nNormalizing {len(leads)} leads...")
    normalized_leads = [normalize_lead(lead) for lead in leads]
    
    # Print summary for evaluation (especially important in test mode)
    print_lead_summary(normalized_leads)
    
    # Export to Google Sheets
    try:
        sheet_title = None
        if "sheet_title" in filters:
            sheet_title = filters["sheet_title"]
        elif test_mode:
            sheet_title = f"TEST_Leads_{datetime.now().strftime('%Y-%m-%d_%H-%M')}"
        
        sheet_url = create_google_sheet(normalized_leads, sheet_title)
        
        print(f"\n{'='*60}")
        print("✅ SCRAPE COMPLETE")
        print('='*60)
        print(f"Total Leads: {len(normalized_leads)}")
        print(f"Google Sheet: {sheet_url}")
        
        if test_mode:
            print("\n📋 NEXT STEPS:")
            print("1. Review ALL 25 leads in the Google Sheet")
            print("2. Count how many are relevant (right decision makers + correct industry)")
            print("3. If ≥85% relevance (21+ leads), run full scrape")
            print("4. If <85% relevance, adjust filters and re-run test")
        
        # Output result as JSON for orchestration layer
        result_json = {
            "success": True,
            "lead_count": len(normalized_leads),
            "sheet_url": sheet_url,
            "test_mode": test_mode
        }
        print(f"\n__RESULT_JSON__:{json.dumps(result_json)}")
        
    except Exception as e:
        print(f"\n❌ Failed to create Google Sheet: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

