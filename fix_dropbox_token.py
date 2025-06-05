"""
Manual Dropbox token verification and connection test
"""

import os
import dropbox
from dropbox.exceptions import AuthError

def test_specific_token():
    """Test the specific Dropbox token provided by user"""
    
    # The exact token provided by user
    token = "sl.u.AFwQXQ5olL7TEmNKMiYmqPqPI7TyFUgHHJ1TsqzBej0t_HzbJyFuwKWCuLyqp0Soz-EXlvxPgTYcGlK_Mn3hKPLkY1wKsITzCU_mb_HCtFyxaQIOlgXbPDflBTX8G_l8cGMO4bEZGJa-1Z4rXaTKeEdc_J46HGPuB_NTqiFASVBeZB33dJtEkRWeuHOKRN6qJKyF3ckwFs17Yrx0_VMY7Z5-keQf_8s76W0b2mHNKkkZp1_Bw-h1PrerVbSS1rpWcFs16hisl9nqxy5xGYJAfD-K4lOpq0O_4fNAEwVe_lA7jCDx-uHkiF5Rg8CMmKWnAWD-DcbFAVKuqxCVVU6Vm-BcsEwxoan5VIZKNAaTVaj6ZIe8CaIsQRhYjtB5O2dkUBMoQ9EDgZKhh97v2RuhAt3oqIE7avUCiKb1HsY9qc7Oa-w-QKhczvbfWnpMqkPsaqJNuIX-MixD3Lw87x92PrWkZPM57j1b9XU8bIBsvrOIgmJtFEdNojmsfc8aqYLXpMbAzKWOhAEDuKVhuZMfPmWhn54dCJScmd3PVlupBCLsBXiyUCUmkLA6JRBASFEFziTUzXjXLM2Fi1RhXx57x98FztcCI6DUvSFp5hcN25LZhnVDjMKJCBKA_K-hNN6Zs34bCKmJctGij78siZe0RsuuivVZyy_VcwkECwar9EfktCQQWwcJFgmOGQsoON-Lm2LtknvYEKG8VlmMKynKwSEnyb15Tz-MaMpGxgpbiQI9hCchUCpgOTqC0NnFmqQRmhDTSJwWd-wipQ7KQ42YblKBSYL5E6iz36bBgnEQR4CsWw83cSXGmQLZQ31MXdN8GbPEQxcR_spWqJbS1Gxh1hkFpyCj-5kIOHANl3rFeRKwi27dXGY7Wj9Ittdk46YsYcpNcve4xhNN1BvAwNT2qCpoeBzk_Lzw13z_kihTBGKH-WnKzGiA9SqkgfIwnV019O0N6phYZHFYW33J5s_SENfwMPx0gl8iZR9HyJp6_RV9-nhIxC6GZzsm0XQ4tT8nKRRUZGzowAtnL4gD4R0AmvEJmSj7yXOKJI1zqGK2IzG9eb6wpduJc7lOOJj13CF3S6ZQLV3Nf5HH8CqgOXZtIL_UcdqdI7NOiiw7Ef3zcAzl8X8qhzq804v3p6fBDMGRUoDRUGJF-hMwWuR5vXT_wjxxl0PJFnk5xte48aiX216ehy1JIXUw6EqIrWr_iOl0MvxqrmeDguNbOvpDRlgBHRTbWlieaBdWSh6_vtFW_yUfK1COI7qMF3Jsd8XgOYE4NvHuzfuzxM_9CRrpHxsg0aKn0EwejpPiq6ueRn32TM8SCgWOKSZBjkfVYLMLCVLBYCoNfoAFYKmOLBfodgRiayEb"
    
    print(f"Testing token: {token[:20]}...")
    print(f"Token length: {len(token)}")
    
    try:
        dbx = dropbox.Dropbox(token)
        account = dbx.users_get_current_account()
        print(f"SUCCESS: Connected to {account.name.display_name}")
        print(f"Email: {account.email}")
        
        # Test folder access
        try:
            files = dbx.files_list_folder('/apps/otter')
            print(f"Folder access successful: {len(files.entries)} files found")
            return True
        except Exception as e:
            print(f"Folder access error: {e}")
            return False
            
    except AuthError as e:
        print(f"AUTH ERROR: {e}")
        return False
    except Exception as e:
        print(f"CONNECTION ERROR: {e}")
        return False

def test_env_token():
    """Test environment token"""
    env_token = os.environ.get('DROPBOX_ACCESS_TOKEN')
    if env_token:
        print(f"Environment token: {env_token[:20]}...")
        print(f"Environment token length: {len(env_token)}")
    else:
        print("No environment token found")

if __name__ == "__main__":
    print("=== Testing User-Provided Token ===")
    test_specific_token()
    print("\n=== Testing Environment Token ===")
    test_env_token()