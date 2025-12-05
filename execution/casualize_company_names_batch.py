"""
Casualize Company Names

Converts formal company names to casual versions for cold email personalization.
Examples:
    - "CKJ & Associates LLC" → "CKJ"
    - "Johnson Medical Group Inc." → "Johnson Medical"
    - "ABC Technologies Corporation" → "ABC Technologies"
    - "The Smith Company" → "Smith"

Usage:
    python casualize_company_names_batch.py <<'EOF'
    {
        "sheet_url": "https://docs.google.com/spreadsheets/d/xxx/edit"
    }
    EOF
"""

import os
import sys
import json
import re
import pickle
from typing import Dict, Any, List, Optional

import gspread
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# Try to load dotenv if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Google Sheets OAuth token storage
TOKEN_PATH = os.path.expanduser("~/.gemini/google_sheets_token.pickle")

# Business suffixes to remove (ordered by specificity)
BUSINESS_SUFFIXES = [
    # Full forms first
    r'\bLimited Liability Company\b',
    r'\bLimited Liability Partnership\b',
    r'\bProfessional Corporation\b',
    r'\bProfessional Limited Liability Company\b',
    r'\bLimited Partnership\b',
    r'\bGeneral Partnership\b',
    r'\bIncorporated\b',
    r'\bCorporation\b',
    r'\bCompany\b',
    r'\bLimited\b',
    r'\bPartnership\b',
    r'\bAssociates\b',
    r'\bEnterprise[s]?\b',
    r'\bHoldings?\b',
    r'\bGroup\b',
    r'\bSolutions\b',
    r'\bServices\b',
    r'\bConsulting\b',
    r'\bAdvisors?\b',
    r'\bVentures\b',
    r'\bCapital\b',
    r'\bInternational\b',
    r'\bGlobal\b',
    r'\bWorldwide\b',
    # Abbreviations
    r'\bPLLC\b',
    r'\bPLLC\.\b',
    r'\bP\.L\.L\.C\.\b',
    r'\bLLC\b',
    r'\bLLC\.\b',
    r'\bL\.L\.C\.\b',
    r'\bLLP\b',
    r'\bLLP\.\b',
    r'\bL\.L\.P\.\b',
    r'\bLP\b',
    r'\bL\.P\.\b',
    r'\bPC\b',
    r'\bP\.C\.\b',
    r'\bPA\b',
    r'\bP\.A\.\b',
    r'\bInc\b',
    r'\bInc\.\b',
    r'\bCorp\b',
    r'\bCorp\.\b',
    r'\bCo\b',
    r'\bCo\.\b',
    r'\bLtd\b',
    r'\bLtd\.\b',
    r'\bPte\b',
    r'\bPte\.\b',
    r'\bPLC\b',
    r'\bP\.L\.C\.\b',
    r'\bGmbH\b',
    r'\bAG\b',
    r'\bS\.A\.\b',
    r'\bS\.L\.\b',
    r'\bB\.V\.\b',
    r'\bN\.V\.\b',
    r'\bOy\b',
    r'\bA/S\b',
    r'\bAS\b',
    r'\bAB\b',
]

# Prefixes to consider removing
PREFIXES_TO_REMOVE = [
    r'^The\s+',
]

# Words that indicate we should keep more of the name
IMPORTANT_DESCRIPTORS = [
    'medical', 'dental', 'legal', 'law', 'tech', 'digital', 'creative',
    'financial', 'insurance', 'real estate', 'realty', 'property',
    'construction', 'engineering', 'design', 'marketing', 'media',
    'health', 'wellness', 'fitness', 'beauty', 'auto', 'automotive'
]


def casualize_company_name(formal_name: str) -> str:
    """
    Convert a formal company name to a casual version for cold email.
    
    Args:
        formal_name: The formal company name (e.g., "CKJ & Associates LLC")
        
    Returns:
        str: Casual version of the name (e.g., "CKJ")
    """
    if not formal_name or not formal_name.strip():
        return ""
    
    name = formal_name.strip()
    original = name
    
    # Remove business suffixes (case-insensitive)
    for suffix_pattern in BUSINESS_SUFFIXES:
        name = re.sub(suffix_pattern, '', name, flags=re.IGNORECASE)
    
    # Clean up punctuation artifacts
    name = re.sub(r'\s*,\s*$', '', name)  # Trailing comma
    name = re.sub(r'\s*&\s*$', '', name)  # Trailing ampersand
    name = re.sub(r'\s+', ' ', name)  # Multiple spaces
    name = name.strip()
    
    # Remove common prefixes like "The"
    for prefix_pattern in PREFIXES_TO_REMOVE:
        name = re.sub(prefix_pattern, '', name, flags=re.IGNORECASE)
    
    name = name.strip()
    
    # If the name is now empty or just punctuation, return original minus obvious suffixes
    if not name or not re.search(r'[a-zA-Z0-9]', name):
        # Fallback: just remove the most obvious suffixes
        fallback = re.sub(r'\s*(LLC|Inc|Corp|Ltd|Co)\.*\s*$', '', original, flags=re.IGNORECASE)
        return fallback.strip() or original
    
    # Check if name contains important descriptors - if so, keep them
    name_lower = name.lower()
    has_descriptor = any(desc in name_lower for desc in IMPORTANT_DESCRIPTORS)
    
    # If the name is a single word or has an important descriptor, keep it as is
    words = name.split()
    if len(words) <= 2 or has_descriptor:
        return name
    
    # For longer names without descriptors, consider shortening
    # e.g., "ABC XYZ Technology Group" → "ABC XYZ Technology" (Group already removed)
    # But "John Smith Financial Services" should keep the descriptor
    
    return name


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
    # Handle various URL formats
    patterns = [
        r'/spreadsheets/d/([a-zA-Z0-9-_]+)',
        r'id=([a-zA-Z0-9-_]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    # If no pattern matches, assume the input is the ID itself
    if re.match(r'^[a-zA-Z0-9-_]+$', url):
        return url
    
    raise ValueError(f"Could not extract spreadsheet ID from: {url}")


def process_sheet(sheet_url: str) -> Dict[str, Any]:
    """
    Process a Google Sheet, casualizing all company names.
    
    Args:
        sheet_url: URL or ID of the Google Sheet
        
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
    
    if not all_data:
        return {
            "success": True,
            "processed": 0,
            "message": "Sheet is empty"
        }
    
    # Find the company_name and casual_company_name columns
    headers = worksheet.row_values(1)
    
    company_name_col = None
    casual_name_col = None
    
    for i, header in enumerate(headers):
        header_lower = header.lower().strip()
        if header_lower == "company_name":
            company_name_col = i + 1  # 1-indexed
        elif header_lower == "casual_company_name":
            casual_name_col = i + 1
    
    if company_name_col is None:
        raise ValueError("Column 'company_name' not found in sheet")
    
    if casual_name_col is None:
        # Add the casual_company_name column
        casual_name_col = len(headers) + 1
        worksheet.update_cell(1, casual_name_col, "casual_company_name")
        print(f"Added 'casual_company_name' column at position {casual_name_col}")
    
    # Process each row
    updates = []
    processed = 0
    
    print(f"\nProcessing {len(all_data)} rows...")
    
    for i, row in enumerate(all_data):
        row_num = i + 2  # Account for header row and 1-indexing
        company_name = row.get("company_name", "")
        
        if company_name:
            casual_name = casualize_company_name(company_name)
            updates.append({
                "range": f"{gspread.utils.rowcol_to_a1(row_num, casual_name_col)}",
                "values": [[casual_name]]
            })
            processed += 1
            
            # Print progress every 50 rows
            if processed % 50 == 0:
                print(f"  Processed {processed} rows...")
    
    # Batch update all casual names
    if updates:
        print(f"\nUpdating {len(updates)} cells...")
        worksheet.batch_update(updates)
    
    # Print some examples
    print(f"\n{'='*60}")
    print("Sample Conversions:")
    print('='*60)
    
    sample_count = min(10, len(all_data))
    for i, row in enumerate(all_data[:sample_count]):
        company = row.get("company_name", "N/A")
        casual = casualize_company_name(company) if company else "N/A"
        print(f"  {company[:40]:<40} → {casual}")
    
    return {
        "success": True,
        "processed": processed,
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
            print('python casualize_company_names_batch.py <<\'EOF\'')
            print('{')
            print('    "sheet_url": "https://docs.google.com/spreadsheets/d/xxx/edit"')
            print('}')
            print('EOF')
            return 1
        
        config = json.loads(input_data)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}")
        return 1
    
    sheet_url = config.get("sheet_url")
    if not sheet_url:
        print("Error: 'sheet_url' is required in the configuration")
        return 1
    
    print(f"\n{'='*60}")
    print("Casualize Company Names")
    print('='*60)
    
    try:
        result = process_sheet(sheet_url)
        
        print(f"\n{'='*60}")
        print("✅ PROCESSING COMPLETE")
        print('='*60)
        print(f"Rows Processed: {result['processed']}")
        print(f"Sheet URL: {result['sheet_url']}")
        
        # Output result as JSON for orchestration layer
        print(f"\n__RESULT_JSON__:{json.dumps(result)}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0


# Allow direct testing of the casualization function
def test_casualization():
    """Test the casualization function with sample names."""
    test_names = [
        "CKJ & Associates LLC",
        "Johnson Medical Group Inc.",
        "ABC Technologies Corporation",
        "The Smith Company",
        "XYZ Consulting, LLC",
        "First National Bank",
        "Acme Industries Ltd.",
        "Global Tech Solutions International Inc",
        "Dr. Williams Dental Practice PC",
        "Thompson & Thompson Law Firm LLP",
        "123 Main Street Properties LLC",
        "Summit Real Estate Group",
        "Premier Auto Sales, Inc.",
        "Sunshine Health & Wellness Center",
        "Metro Construction Co.",
        "",
        "Single",
    ]
    
    print("Testing casualization:")
    print('='*60)
    for name in test_names:
        casual = casualize_company_name(name)
        print(f"  {name[:40]:<40} → {casual}")


if __name__ == "__main__":
    # Check if running in test mode
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_casualization()
    else:
        exit(main())

