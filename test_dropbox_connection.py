"""
Test Dropbox connection and provide detailed diagnostics
"""

import os
import dropbox
from dropbox.exceptions import AuthError

def test_dropbox_connection():
    """Test Dropbox connection with detailed error reporting"""
    token = os.environ.get('DROPBOX_ACCESS_TOKEN')
    
    if not token:
        print("ERROR: DROPBOX_ACCESS_TOKEN not found in environment")
        return False
    
    print(f"Token found: {token[:10]}..." if len(token) > 10 else "Token found but very short")
    
    try:
        dbx = dropbox.Dropbox(token)
        account = dbx.users_get_current_account()
        print(f"SUCCESS: Connected to Dropbox account: {account.name.display_name}")
        print(f"Account email: {account.email}")
        return True
        
    except AuthError as e:
        print(f"AUTH ERROR: {e}")
        print("The token may be expired or invalid. Please generate a new token from:")
        print("https://www.dropbox.com/developers/apps")
        return False
        
    except Exception as e:
        print(f"CONNECTION ERROR: {e}")
        return False

if __name__ == "__main__":
    test_dropbox_connection()