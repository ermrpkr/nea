#!/usr/bin/env python
import requests
import json

def test_report_creation_page():
    try:
        # Try to access the report creation page directly
        response = requests.get('http://127.0.0.1:8000/reports/create/', timeout=10)
        
        if response.status_code == 200:
            print("✅ Successfully accessed report creation page")
            
            # Check if the page contains month options
            content = response.text
            if 'Chaitra' in content:
                print("✅ Found 'Chaitra' in page content")
            else:
                print("❌ 'Chaitra' not found in page content")
                
            # Look for debug output in console logs (won't be in HTML)
            print("Note: Debug output will appear in Django server logs, not in HTML response")
            
        else:
            print(f"❌ Failed to access page: {response.status_code}")
            print(f"Response: {response.text[:500]}...")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    test_report_creation_page()
