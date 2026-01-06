#!/usr/bin/env python3
"""
Test script for the template upload and management feature
"""

import json
import requests
from pathlib import Path

# Configuration
SERVER_URL = "http://localhost:5000"
API_BASE = f"{SERVER_URL}/api/pdf"

# Test template HTML
TEST_TEMPLATE = """
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
        .content { margin: 20px 0; }
        .footer { color: #666; font-size: 12px; margin-top: 40px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ title }}</h1>
        <p>Generated on: {{ REPORT_DATE }}</p>
    </div>
    <div class="content">
        <h2>Details</h2>
        <p><strong>Name:</strong> {{ name }}</p>
        <p><strong>Amount:</strong> {{ amount | currency }}</p>
        <p><strong>Description:</strong> {{ description }}</p>
    </div>
    <div class="footer">
        <p>This is a test template</p>
    </div>
</body>
</html>
"""


def test_upload_template():
    """Test uploading a template"""
    print("\n=== Testing Template Upload ===")
    
    # Create a temporary template file
    temp_file = Path("test_template.html")
    temp_file.write_text(TEST_TEMPLATE)
    
    try:
        with open(temp_file, 'rb') as f:
            files = {'file': f}
            data = {'code': 'test_invoice'}
            
            response = requests.post(f"{API_BASE}/upload", files=files, data=data)
            
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        return response.status_code == 201
    finally:
        temp_file.unlink()


def test_list_templates():
    """Test listing templates"""
    print("\n=== Testing List Templates ===")
    
    response = requests.get(f"{API_BASE}/templates")
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    return response.status_code == 200


def test_render_with_code():
    """Test rendering a template using code"""
    print("\n=== Testing Render with Code ===")
    
    payload = {
        "code": "test_invoice",
        "data": {
            "title": "Invoice #001",
            "name": "John Doe",
            "amount": 1500.50,
            "description": "Consulting Services"
        }
    }
    
    response = requests.post(f"{API_BASE}/render", json=payload)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Success: {result.get('success')}")
    
    if result.get('html'):
        print(f"HTML Length: {len(result['html'])} characters")
        print(f"HTML Preview: {result['html'][:200]}...")
    
    return response.status_code == 200


def test_generate_pdf_with_code():
    """Test generating PDF using code"""
    print("\n=== Testing Generate PDF with Code ===")
    
    payload = {
        "code": "test_invoice",
        "data": {
            "title": "Invoice #001",
            "name": "John Doe",
            "amount": 1500.50,
            "description": "Consulting Services"
        },
        "options": {
            "page_size": "A4",
            "orientation": "portrait"
        }
    }
    
    response = requests.post(f"{API_BASE}/generate", json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Success: {result.get('success')}")
        print(f"PDF Size: {result.get('size')} bytes")
        return True
    else:
        print(f"Error: {response.text}")
        return False


def test_delete_template():
    """Test deleting a template"""
    print("\n=== Testing Delete Template ===")
    
    response = requests.delete(f"{API_BASE}/templates/test_invoice")
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    return response.status_code == 200


def main():
    """Run all tests"""
    print("Starting Template Feature Tests...")
    print(f"Server URL: {SERVER_URL}")
    
    tests = [
        ("Upload Template", test_upload_template),
        ("List Templates", test_list_templates),
        ("Render with Code", test_render_with_code),
        ("Generate PDF with Code", test_generate_pdf_with_code),
        ("Delete Template", test_delete_template),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"ERROR: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n=== Test Summary ===")
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to server. Make sure the PDF server is running.")
        print(f"URL: {SERVER_URL}")
    except Exception as e:
        print(f"ERROR: {e}")
