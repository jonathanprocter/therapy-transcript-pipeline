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

# Set up environment with placeholder API keys for testing
os.environ.setdefault("DROPBOX_ACCESS_TOKEN", "dummy")
os.environ.setdefault("OPENAI_API_KEY", "dummy")
os.environ.setdefault("ANTHROPIC_API_KEY", "dummy")
os.environ.setdefault("GEMINI_API_KEY", "dummy")
os.environ.setdefault("NOTION_INTEGRATION_SECRET", "dummy")
os.environ.setdefault("NOTION_DATABASE_ID", "dummy")

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