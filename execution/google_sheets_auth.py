"""
Google Sheets OAuth Authentication Script

Run this script once to authorize the application to access Google Sheets.
The token will be stored at ~/.gemini/google_sheets_token.pickle

Prerequisites:
1. Create a Google Cloud project
2. Enable Google Sheets API and Google Drive API
3. Create OAuth 2.0 credentials (Desktop App)
4. Download credentials.json to ~/.gemini/credentials.json
"""

import os
import pickle
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Scopes required for Google Sheets and Drive access
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# Default paths
DEFAULT_CREDENTIALS_PATH = os.path.expanduser("~/.gemini/credentials.json")
DEFAULT_TOKEN_PATH = os.path.expanduser("~/.gemini/google_sheets_token.pickle")


def get_credentials_path() -> str:
    """Get the path to credentials.json from env or default."""
    path = os.getenv("GOOGLE_CREDENTIALS_PATH", DEFAULT_CREDENTIALS_PATH)
    return os.path.expanduser(path)


def get_token_path() -> str:
    """Get the path where token will be stored."""
    return DEFAULT_TOKEN_PATH


def ensure_directory_exists(path: str) -> None:
    """Create directory if it doesn't exist."""
    directory = os.path.dirname(path)
    if directory:
        Path(directory).mkdir(parents=True, exist_ok=True)


def authenticate() -> Credentials:
    """
    Perform OAuth authentication for Google Sheets.
    
    Returns:
        Credentials: The authenticated credentials object
    """
    creds = None
    token_path = get_token_path()
    credentials_path = get_credentials_path()
    
    # Check if we have a saved token
    if os.path.exists(token_path):
        print(f"Loading existing token from {token_path}")
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    
    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Token expired, refreshing...")
            creds.refresh(Request())
        else:
            # Need to perform OAuth flow
            if not os.path.exists(credentials_path):
                print(f"\n❌ Error: credentials.json not found at {credentials_path}")
                print("\nTo set up Google Sheets authentication:")
                print("1. Go to https://console.cloud.google.com/apis/credentials")
                print("2. Create or select a project")
                print("3. Enable 'Google Sheets API' and 'Google Drive API'")
                print("4. Create OAuth 2.0 credentials (Application type: Desktop App)")
                print("5. Download the credentials.json file")
                print(f"6. Save it to: {credentials_path}")
                print("\nThen run this script again.")
                raise FileNotFoundError(f"credentials.json not found at {credentials_path}")
            
            print(f"Starting OAuth flow using {credentials_path}")
            print("\nA browser window will open for authentication.")
            print("Please authorize the application to access Google Sheets.\n")
            
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for future use
        ensure_directory_exists(token_path)
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
        print(f"\n✅ Token saved to {token_path}")
    
    return creds


def verify_connection(creds: Credentials) -> bool:
    """
    Verify the credentials work by listing spreadsheets.
    
    Args:
        creds: The credentials to verify
        
    Returns:
        bool: True if connection is successful
    """
    import gspread
    
    try:
        gc = gspread.authorize(creds)
        # Try to list spreadsheets (this verifies the connection)
        spreadsheets = gc.openall()
        print(f"\n✅ Successfully connected to Google Sheets!")
        print(f"   Found {len(spreadsheets)} accessible spreadsheets")
        return True
    except Exception as e:
        print(f"\n❌ Failed to connect: {e}")
        return False


def main():
    """Main entry point for authentication."""
    print("=" * 50)
    print("Google Sheets OAuth Authentication")
    print("=" * 50)
    
    try:
        creds = authenticate()
        verify_connection(creds)
        print("\n✅ Authentication complete! You can now use the lead scraper.")
    except FileNotFoundError:
        # Error message already printed in authenticate()
        return 1
    except Exception as e:
        print(f"\n❌ Authentication failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

