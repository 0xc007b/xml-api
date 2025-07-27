#!/usr/bin/env python3
"""
API Usage Examples Script

This script demonstrates how to use the XML RESTful API with various operations.
Make sure the API server is running before executing this script.
"""

import requests
import json
import os
import sys
from pathlib import Path

# API Base URL
BASE_URL = "http://localhost:5000/api"

# Get the examples directory path
EXAMPLES_DIR = Path(__file__).parent
LIBRARY_XML = EXAMPLES_DIR / "library.xml"
BOOK_CATALOG_XSL = EXAMPLES_DIR / "book_catalog.xsl"
LIBRARY_HTML_XSL = EXAMPLES_DIR / "library_to_html.xsl"


def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}\n")


def check_health():
    """Check API health status"""
    print_section("1. Health Check")

    response = requests.get(f"{BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    return response.status_code == 200


def upload_xml_file():
    """Upload XML file and return file ID"""
    print_section("2. Upload XML File")

    if not LIBRARY_XML.exists():
        print(f"Error: {LIBRARY_XML} not found!")
        return None

    with open(LIBRARY_XML, 'rb') as f:
        files = {'file': ('library.xml', f, 'application/xml')}
        response = requests.post(f"{BASE_URL}/xml/upload", files=files)

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 201:
        return response.json()['file_id']
    return None


def list_xml_files():
    """List all uploaded XML files"""
    print_section("3. List All XML Files")

    response = requests.get(f"{BASE_URL}/xml")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def get_elements_by_xpath(file_id):
    """Get XML elements using XPath"""
    print_section("4. Query XML Elements with XPath")

    # Example 1: Get all books
    print("\nExample 1: Get all books")
    response = requests.get(f"{BASE_URL}/xml/{file_id}/element",
                          params={'xpath': '//book'})
    print(f"Status Code: {response.status_code}")
    data = response.json()
    print(f"Found {data['count']} books")

    # Example 2: Get fiction books
    print("\nExample 2: Get fiction books")
    response = requests.get(f"{BASE_URL}/xml/{file_id}/element",
                          params={'xpath': '//book[@genre="fiction"]'})
    data = response.json()
    print(f"Found {data['count']} fiction books:")
    for elem in data['elements']:
        # Parse the nested book data
        book_title = elem['xml'].split('<title>')[1].split('</title>')[0] if '<title>' in elem['xml'] else 'Unknown'
        print(f"  - {book_title}")

    # Example 3: Get books under $12
    print("\nExample 3: Get book prices")
    response = requests.get(f"{BASE_URL}/xml/{file_id}/element",
                          params={'xpath': '//book/price'})
    data = response.json()
    print("Book prices:")
    for elem in data['elements']:
        print(f"  - {elem['attributes'].get('currency', 'USD')} {elem['text']}")


def add_new_element(file_id):
    """Add a new book to the library"""
    print_section("5. Add New XML Element")

    new_book = {
        "parent_xpath": "/library/books",
        "tag": "book",
        "attributes": {
            "id": "6",
            "isbn": "978-0-141-43951-8",
            "genre": "philosophy"
        }
    }

    response = requests.post(f"{BASE_URL}/xml/{file_id}/element",
                           json=new_book,
                           headers={'Content-Type': 'application/json'})

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    # Now add child elements to the new book
    book_xpath = '//book[@id="6"]'

    # Add title
    title_data = {
        "parent_xpath": book_xpath,
        "tag": "title",
        "text": "The Republic"
    }
    requests.post(f"{BASE_URL}/xml/{file_id}/element", json=title_data)

    # Add author
    author_data = {
        "parent_xpath": book_xpath,
        "tag": "author",
        "text": "Plato"
    }
    requests.post(f"{BASE_URL}/xml/{file_id}/element", json=author_data)

    # Add price
    price_data = {
        "parent_xpath": book_xpath,
        "tag": "price",
        "text": "11.99",
        "attributes": {"currency": "USD"}
    }
    requests.post(f"{BASE_URL}/xml/{file_id}/element", json=price_data)

    print("\nAdded new book with details")


def update_element(file_id):
    """Update an existing element"""
    print_section("6. Update XML Element")

    # Update the price of book with id="1"
    update_data = {
        "xpath": '//book[@id="1"]/price',
        "text": "12.99",
        "attributes": {
            "currency": "USD",
            "discount": "10%"
        }
    }

    response = requests.put(f"{BASE_URL}/xml/{file_id}/element",
                          json=update_data,
                          headers={'Content-Type': 'application/json'})

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def delete_element(file_id):
    """Delete an element from XML"""
    print_section("7. Delete XML Element")

    # Delete out-of-stock books
    response = requests.delete(f"{BASE_URL}/xml/{file_id}/element",
                             params={'xpath': '//book[availability="out-of-stock"]'})

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def transform_xml(file_id):
    """Transform XML using XSLT"""
    print_section("8. Transform XML with XSLT")

    # Transform to catalog format
    if not BOOK_CATALOG_XSL.exists():
        print(f"Error: {BOOK_CATALOG_XSL} not found!")
        return None

    with open(BOOK_CATALOG_XSL, 'rb') as f:
        files = {'xslt': ('book_catalog.xsl', f, 'application/xml')}
        response = requests.post(f"{BASE_URL}/xml/{file_id}/transform", files=files)

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 200:
        transformed_id = response.json()['transformed_file_id']

        # Download the transformed file
        download_response = requests.get(f"{BASE_URL}/xml/{transformed_id}")
        if download_response.status_code == 200:
            output_file = EXAMPLES_DIR / "transformed_catalog.xml"
            with open(output_file, 'wb') as f:
                f.write(download_response.content)
            print(f"\nTransformed XML saved to: {output_file}")

        return transformed_id

    return None


def download_xml(file_id):
    """Download XML file"""
    print_section("9. Download XML File")

    response = requests.get(f"{BASE_URL}/xml/{file_id}")

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        output_file = EXAMPLES_DIR / f"downloaded_{file_id}.xml"
        with open(output_file, 'wb') as f:
            f.write(response.content)
        print(f"XML file saved to: {output_file}")

        # Print first few lines
        print("\nFirst few lines of the file:")
        print("-" * 40)
        lines = response.text.split('\n')[:10]
        for line in lines:
            print(line)
        if len(response.text.split('\n')) > 10:
            print("...")


def delete_xml_file(file_id):
    """Delete XML file"""
    print_section("10. Delete XML File")

    response = requests.delete(f"{BASE_URL}/xml/{file_id}")

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def main():
    """Main function to run all examples"""
    print("\n" + "="*60)
    print(" XML RESTful API - Usage Examples")
    print("="*60)
    print(f"\nAPI Base URL: {BASE_URL}")
    print(f"Examples Directory: {EXAMPLES_DIR}")

    # Check if API is running
    if not check_health():
        print("\nError: API is not running! Please start the server first.")
        print("Run: python src/app.py")
        sys.exit(1)

    # Upload XML file
    file_id = upload_xml_file()
    if not file_id:
        print("\nError: Failed to upload XML file!")
        sys.exit(1)

    # List all files
    list_xml_files()

    # Query elements
    get_elements_by_xpath(file_id)

    # Add new element
    add_new_element(file_id)

    # Update element
    update_element(file_id)

    # Delete element
    delete_element(file_id)

    # Transform XML
    transformed_id = transform_xml(file_id)

    # Download the modified XML
    download_xml(file_id)

    # Clean up - delete files
    print("\n" + "="*60)
    print(" Cleanup")
    print("="*60)

    response = input("\nDo you want to delete the uploaded files? (y/n): ")
    if response.lower() == 'y':
        delete_xml_file(file_id)
        if transformed_id:
            delete_xml_file(transformed_id)
        print("\nCleanup completed!")
    else:
        print("\nFiles kept on server.")

    print("\n" + "="*60)
    print(" All examples completed successfully!")
    print("="*60)


if __name__ == "__main__":
    main()
