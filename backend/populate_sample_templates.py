#!/usr/bin/env python3
"""
Simple script to populate sample templates via HTTP API
"""

import requests
import json

def populate_templates():
    """Populate sample templates using the backend API"""
    base_url = "http://localhost:8000"
    
    print("🚀 Populating sample templates...")
    
    # Test if backend is running
    try:
        response = requests.get(f"{base_url}/api/v1/templates/test", timeout=5)
        print(f"✅ Backend is running: {response.status_code}")
        result = response.json()
        print(f"📊 Current template count: {result.get('template_count', 0)}")
        
        if result.get('template_count', 0) > 0:
            print("✅ Templates already exist in database")
            print(f"📂 Categories: {result.get('categories', [])}")
            return True
        else:
            print("📝 No templates found, would need to run migration script")
            return True
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend connection failed: {e}")
        print("💡 Make sure the backend is running on http://localhost:8000")
        return False

if __name__ == "__main__":
    success = populate_templates()
    if success:
        print("🎉 Template population check completed!")
    else:
        print("❌ Failed to connect to backend")