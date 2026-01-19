#!/usr/bin/env python
"""Quick test script for TRAMOS ticket API"""

import requests
import json
import sys

API_URL = "http://localhost:8000/tickets"

payload = {
    "name": "Test Driver",
    "email": "test@tramos.com",
    "subject": "Test Ticket",
    "message": "Testing TRAMOS API",
    "ip": "127.0.0.1"
}

print("=" * 60)
print("TRAMOS API Test - Create Ticket")
print("=" * 60)
print(f"\nURL: {API_URL}")
print(f"Payload: {json.dumps(payload, indent=2)}")
print("\nSending request...")

try:
    response = requests.post(API_URL, json=payload, timeout=10)
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response Body: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ SUCCESS!")
        print(f"Ticket ID: {data.get('ticket_id')}")
        print(f"Message: {data.get('message')}")
        sys.exit(0)
    else:
        print(f"\n❌ FAILED - Status {response.status_code}")
        print(f"Response: {response.json()}")
        sys.exit(1)
        
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    sys.exit(1)
