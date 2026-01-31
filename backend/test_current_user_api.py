#!/usr/bin/env python3
"""
Test the /doctor/current-user API endpoint
"""
import requests
import json

# Test with a simple GET request (no session)
print("=" * 60)
print("Testing /doctor/current-user API endpoint")
print("=" * 60)

url = "http://localhost:5000/doctor/current-user"

print(f"\nGET {url}")
try:
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
