"""
Test Script: Verify Doctor Chatbot Access Fix

This script tests the doctor chatbot authentication and authorization flow.

Run this after starting the Flask server to verify the fix works correctly.
"""

import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def print_result(test_name, passed, details=""):
    status = "✅ PASSED" if passed else "❌ FAILED"
    print(f"{test_name}: {status}")
    if details:
        print(f"  Details: {details}")

def test_unauthenticated_access():
    """Test 1: Unauthenticated user cannot access doctor chatbot"""
    print_header("TEST 1: Unauthenticated Access")
    
    try:
        response = requests.get(f"{BASE_URL}/doctor/chatbot", allow_redirects=False)
        
        # Should get 401 Unauthorized
        if response.status_code == 401:
            data = response.json()
            print_result("Unauthenticated Access Blocked", True, 
                        f"Got 401: {data.get('message')}")
        else:
            print_result("Unauthenticated Access Blocked", False,
                        f"Expected 401, got {response.status_code}")
    except Exception as e:
        print_result("Unauthenticated Access Test", False, str(e))

def test_doctor_login_and_access():
    """Test 2: Doctor can login and access chatbot"""
    print_header("TEST 2: Doctor Login & Access")
    
    session = requests.Session()
    
    # Step 1: Login as doctor
    print("\n→ Step 1: Attempting doctor login...")
    login_data = {
        "phone_number": "9876543210",  # Replace with actual test doctor
        "password": "doctor123"         # Replace with actual test password
    }
    
    try:
        login_response = session.post(
            f"{BASE_URL}/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            print_result("Doctor Login", True, 
                        f"Logged in as: {login_result.get('data', {}).get('user', {}).get('full_name')}")
            
            # Step 2: Access doctor chatbot page
            print("\n→ Step 2: Accessing /doctor/chatbot...")
            chatbot_response = session.get(f"{BASE_URL}/doctor/chatbot")
            
            if chatbot_response.status_code == 200:
                # Check if we got HTML
                if "<!DOCTYPE html>" in chatbot_response.text:
                    print_result("Doctor Chatbot Access", True,
                                "Successfully received doctor-chatbot.html")
                else:
                    print_result("Doctor Chatbot Access", False,
                                "Did not receive HTML page")
            elif chatbot_response.status_code == 401:
                print_result("Doctor Chatbot Access", False,
                            "Got 401: Session not maintained")
            elif chatbot_response.status_code == 403:
                print_result("Doctor Chatbot Access", False,
                            "Got 403: Role check failed")
            else:
                print_result("Doctor Chatbot Access", False,
                            f"Unexpected status: {chatbot_response.status_code}")
        
        elif login_response.status_code == 401:
            print_result("Doctor Login", False,
                        "Invalid credentials - update test data")
        else:
            print_result("Doctor Login", False,
                        f"Status: {login_response.status_code}")
    
    except Exception as e:
        print_result("Doctor Login & Access Test", False, str(e))

def test_patient_access_denied():
    """Test 3: Patient cannot access doctor chatbot"""
    print_header("TEST 3: Patient Access Denied")
    
    session = requests.Session()
    
    # Step 1: Login as patient
    print("\n→ Step 1: Attempting patient login...")
    login_data = {
        "phone_number": "9876543211",  # Replace with actual test patient
        "password": "patient123"        # Replace with actual test password
    }
    
    try:
        login_response = session.post(
            f"{BASE_URL}/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        if login_response.status_code == 200:
            print_result("Patient Login", True, "Logged in as patient")
            
            # Step 2: Try to access doctor chatbot
            print("\n→ Step 2: Attempting to access /doctor/chatbot...")
            chatbot_response = session.get(f"{BASE_URL}/doctor/chatbot")
            
            if chatbot_response.status_code == 403:
                data = chatbot_response.json()
                print_result("Patient Access Blocked", True,
                            f"Got 403: {data.get('message')}")
            else:
                print_result("Patient Access Blocked", False,
                            f"Expected 403, got {chatbot_response.status_code}")
        
        elif login_response.status_code == 401:
            print_result("Patient Login", False,
                        "Invalid credentials - update test data or skip this test")
        else:
            print_result("Patient Login", False,
                        f"Status: {login_response.status_code}")
    
    except Exception as e:
        print_result("Patient Access Test", False, str(e))

def test_session_check():
    """Test 4: Verify session check endpoint"""
    print_header("TEST 4: Session Check Endpoint")
    
    session = requests.Session()
    
    # Test unauthenticated
    try:
        response = session.get(f"{BASE_URL}/auth/check-session")
        data = response.json()
        
        if not data.get('authenticated'):
            print_result("Unauthenticated Session Check", True,
                        "Correctly reports not authenticated")
        else:
            print_result("Unauthenticated Session Check", False,
                        "Should report not authenticated")
    
    except Exception as e:
        print_result("Session Check Test", False, str(e))

def main():
    print("\n" + "="*60)
    print("  DOCTOR CHATBOT ACCESS FIX - TEST SUITE")
    print("="*60)
    print("\nThis script tests the session-based authentication fix.")
    print("Make sure the Flask server is running on port 5000.\n")
    
    input("Press Enter to start tests... ")
    
    # Run tests
    test_unauthenticated_access()
    test_session_check()
    test_doctor_login_and_access()
    test_patient_access_denied()
    
    print_header("TEST SUMMARY")
    print("\nTests completed!")
    print("\nNote: Update test credentials in script if login tests fail.")
    print("Default test data:")
    print("  - Doctor: 9876543210 / doctor123")
    print("  - Patient: 9876543211 / patient123")
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    main()
