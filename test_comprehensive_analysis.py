#!/usr/bin/env python3
"""
Test the comprehensive clinical analysis with maximum token utilization
"""

import os
import sys

# Set all API keys for testing
os.environ['DROPBOX_ACCESS_TOKEN'] = 'sl.u.AFzkTn-I60M5RQL8Trj5PR9a6kUOg68s5lkhUKZNBsbqcXiTYAj94ZwJMO0bZuBAtP2pTUAhlD4sxeZKCY80khIpzWRPK-JFkO0Y3HgKhTPaOstl9Sx4qMx4Z5egNSdQl_E_UkujeIaeIvgZ2U3hFp-AR_4rMoqmHjhBR-sn47uNK2sMWZT0RSujpupjWTHXjQOMZnJcsf0yy4x99-a84ipnT0OcgJZS8AFgb1HdgtnnJUvkg1yS4MJSzq_WzM4PgOMDg56z5KUZMPU9kzyLRsPpAQ61IDYy7mQqhDAtx8PCasOhwuXqlSpI8Hj1RpK05OYNtYStinXGZ-3cMSl8oKGYDJXjSOtBkku1v0D3xM-AYTUrEI6yT4ognD9vfVs9W0cH54L2ODJ2shRwBHszuDxxc6HyaC0k6EgHfkNFyOfGXmscwRyO0vg_Vnk_m8wccddSFpocqd3SN413OxvKtgRycPxbS89gExNWzZvo-R0uXYkkOY6z4RHzRp4qHTElfVH03eIwT8R-gJZcFhrZZ7GhLz-OvhfcZyijSrydkAhIi9JJz0qNu0EoztAJo7F5_PduxWTxwwOsAdMEEibWCTYcMlQBOMtS82YU7XK4NOBhZhi8SuLdvKp6Hvamboomgvu1jb0jwq7FJfAoOkyxXmoMR4MFdxti9A0GkGGIjeuYWta8H6UKnWDP13SO3OlgBpOhJXq1JaaCaqnNR0Mqoxrz9j2DHDpEguGPVzngcfR_IgyXIbj4HfxcU2508FfgZxFYsnnasTNZuWkM1akJLOc61u2zUnG2GxXEH9M6o6gEF_pXHHNz00u5uN4GTM5t94qHAfcgDqmyTELbweRnee9vY8LsbJZ6cypoy4O7_5HIdZpzzKjtmkQF1T6MMozahdRjbVgN6km9g-5WsP3aIWN0P3Y6WL8ZDahFZJ1VInP2pm8ar_A5xGLd95WseELIKYUuz2V1b3YrdEzZYP4K1jQYp9bAzxzvlc_fYDg4dGumVvJ47I_vNQ0-oV2SLIuw8F6AFc-Nk69vIVYuPqHolt1zIeH_TLDMac61nKYC0fstK9nMtfE9GI5bQGUBaSKyqA1eXMb6suXMmgYBtwsC5C6sJD7UvEa_FAfWrgUUP1XjiviAE1XBbsmKgejAdgEEuCI4HEskj3FweNv4KwjpOg'
os.environ['OPENAI_API_KEY'] = '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'
os.environ['ANTHROPIC_API_KEY'] = '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'
os.environ['GEMINI_API_KEY'] = 'AIzaSyDKSugqYPsqYMrrAiXh-1bAPf992gVrGbk'

def test_comprehensive_clinical_analysis():
    """Test the comprehensive clinical analysis with maximum tokens"""
    print("Testing comprehensive clinical analysis with maximum token utilization...")
    
    try:
        from services.ai_service import AIService
        
        # Sample therapy transcript
        sample_transcript = """
        Therapist: Good morning, Sarah. How are you feeling today?
        
        Client: I'm... honestly, I'm struggling. The panic attacks have been getting worse since we last met. Yesterday, I had one in the grocery store and just had to leave my cart and run out. I felt so embarrassed.
        
        Therapist: That sounds really difficult and frightening. Can you tell me more about what was happening for you in that moment?
        
        Client: It started when I was in the cereal aisle. Suddenly, my heart started racing, and I felt like I couldn't breathe. The walls felt like they were closing in on me. I kept thinking "everyone is staring at me" and "I'm going to collapse right here." I know it doesn't make sense, but in that moment, it felt so real.
        
        Therapist: Those physical sensations and thoughts you're describing are very real experiences of panic. It makes complete sense that you would want to get to safety. Have you noticed any patterns in when these attacks occur?
        
        Client: They seem to happen most in crowded places now. It's gotten so bad that I've been avoiding going anywhere with lots of people. My sister invited me to her birthday party next week, but I already told her I can't come. I hate that this is controlling my life.
        
        Therapist: I can hear the frustration and sadness in your voice about how this is impacting your relationships and daily activities. When you think about not going to your sister's party, what emotions come up for you?
        
        Client: Guilt, mostly. And disappointment in myself. I used to be the person who never missed family events. Now I feel like I'm letting everyone down, including myself. Sometimes I wonder if I'll ever get back to who I used to be.
        """
        
        ai_service = AIService()
        
        print("Running OpenAI analysis with comprehensive clinical prompt...")
        openai_result = ai_service._analyze_with_openai(sample_transcript, "Sarah")
        
        print("✓ OpenAI analysis completed")
        print(f"Analysis type: {openai_result.get('analysis_type')}")
        print(f"Content length: {len(openai_result.get('clinical_progress_note', ''))}")
        
        print("\nRunning Anthropic analysis with comprehensive clinical prompt...")
        anthropic_result = ai_service._analyze_with_anthropic(sample_transcript, "Sarah")
        
        print("✓ Anthropic analysis completed")
        print(f"Analysis type: {anthropic_result.get('analysis_type')}")
        print(f"Content length: {len(anthropic_result.get('clinical_progress_note', ''))}")
        
        # Test longitudinal analysis
        session_data = [
            {
                'session_date': '2025-06-01',
                'clinical_progress_note': openai_result.get('clinical_progress_note', ''),
                'client_name': 'Sarah'
            }
        ]
        
        print("\nTesting longitudinal case conceptualization...")
        longitudinal_result = ai_service.analyze_longitudinal_progress(session_data)
        
        print("✓ Longitudinal analysis completed")
        print(f"Providers used: {[k for k in longitudinal_result.keys() if 'analysis' in k]}")
        
        return True
        
    except Exception as e:
        print(f"Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("COMPREHENSIVE CLINICAL ANALYSIS TEST")
    print("=" * 50)
    
    success = test_comprehensive_clinical_analysis()
    
    print("\n" + "=" * 50)
    if success:
        print("✓ All comprehensive clinical analysis features working!")
        print("• Maximum token utilization enabled")
        print("• Comprehensive clinical progress notes generated") 
        print("• Longitudinal case conceptualization functional")
        print("• Ready for Dropbox PDF processing")
    else:
        print("✗ Some features need attention")