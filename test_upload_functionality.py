#!/usr/bin/env python3
"""
Test the upload functionality with the new OpenAI API key
"""

import os
import sys

# Use placeholder API keys
os.environ.setdefault('OPENAI_API_KEY', 'dummy')
os.environ.setdefault('NOTION_INTEGRATION_SECRET', 'dummy')
os.environ.setdefault('NOTION_DATABASE_ID', 'dummy')

def test_openai_connection():
    """Test OpenAI connection with new API key"""
    try:
        import openai
        client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        
        # Test with a simple therapy-related prompt
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user", 
                "content": "Analyze this brief therapy session: Client discussed anxiety about work deadlines. Provide a JSON response with mood and key themes."
            }],
            max_tokens=100
        )
        
        print("OpenAI connection successful!")
        print(f"Response: {response.choices[0].message.content[:200]}...")
        return True
        
    except Exception as e:
        print(f"OpenAI test failed: {str(e)}")
        return False

def test_processing_pipeline():
    """Test the processing pipeline with sample content"""
    try:
        sys.path.append('src')
        from processing_pipeline import ProcessingPipeline
        
        api_keys = {
            'openai_key': os.environ.get('OPENAI_API_KEY'),
            'notion_key': os.environ.get('NOTION_INTEGRATION_SECRET'),
            'notion_parent_id': os.environ.get('NOTION_DATABASE_ID'),
        }
        
        pipeline = ProcessingPipeline(api_keys)
        
        # Test with sample text file
        sample_file = 'attached_assets/test_files/John_Smith_2025-06-04.txt'
        if os.path.exists(sample_file):
            print(f"Testing with sample file: {sample_file}")
            result = pipeline.process_single_file(sample_file)
            print(f"Processing result: {result}")
            return result.get('success', False)
        else:
            print("Sample file not found")
            return False
            
    except Exception as e:
        print(f"Pipeline test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing upload functionality with new OpenAI API key...")
    print("=" * 60)
    
    print("\n1. Testing OpenAI connection:")
    openai_ok = test_openai_connection()
    
    print("\n2. Testing processing pipeline:")
    pipeline_ok = test_processing_pipeline()
    
    print("\n" + "=" * 60)
    print("RESULTS:")
    print(f"OpenAI connection: {'PASS' if openai_ok else 'FAIL'}")
    print(f"Processing pipeline: {'PASS' if pipeline_ok else 'FAIL'}")
    
    if openai_ok and pipeline_ok:
        print("\nUpload functionality is ready!")
    else:
        print("\nSome issues need to be resolved.")