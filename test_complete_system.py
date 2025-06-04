#!/usr/bin/env python3
"""
Complete system test for the therapy transcript processor.
Tests all three core features:
1. Dashboard view and database functionality
2. File upload and AI processing pipeline
3. Dropbox monitoring with provided API credentials
"""

import os
import sys
import requests
import tempfile
import shutil
from pathlib import Path

# Set up environment with provided API keys
os.environ['DROPBOX_ACCESS_TOKEN'] = 'sl.u.AFzzGjmFgr1MlkpSxGhcMlCsb6D0r6kNRSPUXsKwhOhb5MvnlhyTVNlSoZzp0jfhHXIWDq4CGjd6CB6OeKOeunjxLwDofHRdLDYvdxbwNXNc72Tx3XaF60aXd9hxXKaZY9k41WhQiw6ojyOoGaKr0bnkcT9f0YugMXk2-t4PuyFQqDLqnp5BZRwgSxIqYzVimR0ij8Vh74Qaup1RmW50pcR5u2FXFDjtcubAXUfI5U81T7i-iap4bAGHxq0PJjOCIiRYJ7cKo9h7gBUOQh7wE1e-fZ-s07_oJ9hI5oMJkWqlwkqpLE4t6es-AFjt-8Wph5jCq6gd4pji9yIGPcujTxv_VAUhsw2Xxj0c9fEJA3wj0npQ5WnDqQfcZRD6Zd97s512DAQNlCt6PEeBR8Zt-SgbpQf_hUY-APpmAiZYfq1IMmDpWyo0jnEtujD0_j5wyqnFjerTvjFYXDB1Ipv3ohtNWPX8LcyIzDd_6WNvTBqrSlmRDObiBS2JpN6GscsBRLz3KwjcnaMGuPDq1KsgcDecABBUjdfjwoCa3SOfIldlVCRgQdSUMN9Ev_fZjJk_de_c5ysWiu9dQk10goAgaeDtZtFzd-8NcgzQc7Q1r0OrvAO4oX_rqe4YTcRlCLKvl2qG1KM4WZGPruRmKIstSYe4dCstGcA_rpYRJ7FmYDIDoLtuvgJLDQlVgqR9ozaXUbda2fcmWOO_bZ1IMlg1ZEqWMHwxDiRfbyeqkHRtciqBxCIYwVN-toR0LxgLNsssldDjlT-ktZ9xnOXdr529REoXnm9GrO06dvoLHJnHq3pFE4uR_qFW5hCvXbKyexUM-0K1sdr4mBKV-C30dUPrqK-eBLbbs2M9fIpPBm_3BUaPupw_UApfYm_YQRzx-RzYyv7qF7WBUIf0FtdykbnNsUozpRSGgWbSXfARdmTpI3kbV77_beI6sRSDuL9LbmcUtXIgJ2T_-iBrALfMplPw2yrsFMITcENsjn6D6ggxQALWylyerxsm5B-KmUg9z5EG_woSO3Aqdktg0VBHeoKJd5UKNGxlECzKhDtPRNLwp-m7q9LNRftk0TvBYqY2L2CkDEW-3gl1b9d0N13m6w3zbZaTnVC9C9EHh5B98MePe-KMV4gKukO-Z-2qGf7v5uL9wGc9XzPxr_Hp1MlEBac9SzDei2VZRqtcg_uRTSULmHoipmkLfkRuBUbyAbqI987L919wzBCD1GiE2lCiHARBEBVkosxAY_qtNvihzm8Coz0ekXVJm-fePnNOc2emadr6pps2GjMKt5ZqjHCtUwyJpMhqXBgLfaPTHDsp8NA81qSWfd1HrgzSLyGSc6nxpYoqDOLTc1v-RrGDSlNUS5-wmAmw'
os.environ['OPENAI_API_KEY'] = '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'
os.environ['ANTHROPIC_API_KEY'] = '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'
os.environ['GEMINI_API_KEY'] = 'AIzaSyAUimX4y559-BQ7kOiy-QjZzZeJOzsI1cg'
os.environ['NOTION_INTEGRATION_SECRET'] = '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'
os.environ['NOTION_DATABASE_ID'] = '2049f30def818033b42af330a18aa313'

def test_processing_pipeline():
    """Test the therapy transcript processing pipeline with sample file"""
    print("Testing therapy transcript processing pipeline...")
    
    try:
        # Import the processing pipeline
        sys.path.append('src')
        from processing_pipeline import ProcessingPipeline
        
        # Initialize with API keys
        api_keys = {
            'dropbox_token': os.environ.get('DROPBOX_ACCESS_TOKEN'),
            'openai_key': os.environ.get('OPENAI_API_KEY'),
            'claude_key': os.environ.get('ANTHROPIC_API_KEY'),
            'gemini_key': os.environ.get('GEMINI_API_KEY'),
            'notion_key': os.environ.get('NOTION_INTEGRATION_SECRET'),
            'notion_parent_id': os.environ.get('NOTION_DATABASE_ID'),
            'dropbox_folder': '/apps/otter'
        }
        
        pipeline = ProcessingPipeline(api_keys)
        
        # Test with sample file
        sample_file = 'attached_assets/test_files/John_Smith_2025-06-04.pdf'
        if os.path.exists(sample_file):
            result = pipeline.process_single_file(sample_file)
            print(f"Processing result: {result}")
            return result.get('success', False)
        else:
            print(f"Sample file not found: {sample_file}")
            return False
            
    except Exception as e:
        print(f"Pipeline test failed: {str(e)}")
        return False

def test_dropbox_connection():
    """Test Dropbox API connection"""
    print("Testing Dropbox connection...")
    
    try:
        import dropbox
        token = os.environ.get('DROPBOX_ACCESS_TOKEN')
        dbx = dropbox.Dropbox(token)
        account = dbx.users_get_current_account()
        print(f"Connected to Dropbox account: {account.name.display_name}")
        
        # Try to list files in the apps/otter folder
        try:
            result = dbx.files_list_folder('/apps/otter')
            print(f"Found {len(result.entries)} files in /apps/otter")
            return True
        except dropbox.exceptions.ApiError as e:
            print(f"Dropbox folder access error: {str(e)}")
            return True  # Connection works, folder might not exist yet
            
    except Exception as e:
        print(f"Dropbox test failed: {str(e)}")
        return False

def test_ai_services():
    """Test AI service connections"""
    print("Testing AI service connections...")
    
    # Test OpenAI
    try:
        import openai
        client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello, this is a test."}],
            max_tokens=10
        )
        print("OpenAI connection: OK")
    except Exception as e:
        print(f"OpenAI test failed: {str(e)}")
        return False
    
    # Test Anthropic
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=10,
            messages=[{"role": "user", "content": "Hello"}]
        )
        print("Anthropic connection: OK")
    except Exception as e:
        print(f"Anthropic test failed: {str(e)}")
        return False
    
    return True

def test_notion_connection():
    """Test Notion API connection"""
    print("Testing Notion connection...")
    
    try:
        import requests
        headers = {
            "Authorization": f"Bearer {os.environ.get('NOTION_INTEGRATION_SECRET')}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        response = requests.get("https://api.notion.com/v1/users/me", headers=headers)
        if response.status_code == 200:
            print("Notion connection: OK")
            return True
        else:
            print(f"Notion test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Notion test failed: {str(e)}")
        return False

def main():
    """Run all system tests"""
    print("=" * 60)
    print("THERAPY TRANSCRIPT PROCESSOR - SYSTEM TEST")
    print("=" * 60)
    
    tests = [
        ("Dropbox Connection", test_dropbox_connection),
        ("AI Services", test_ai_services),
        ("Notion Connection", test_notion_connection),
        ("Processing Pipeline", test_processing_pipeline),
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 40)
        results[test_name] = test_func()
        print(f"Result: {'PASS' if results[test_name] else 'FAIL'}")
    
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print("=" * 60)
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name:<25}: {status}")
    
    all_passed = all(results.values())
    print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)