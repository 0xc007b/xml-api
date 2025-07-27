# XML RESTful API Documentation

## Overview

This RESTful API provides comprehensive functionality for XML file manipulation, including upload, retrieval, transformation using XSLT, and CRUD operations on XML elements.

## Base URL

```
http://localhost:5000/api
```

## Swagger UI / OpenAPI Documentation

When running the API with Swagger support (`python start_api_swagger.py`), you can access:

- **Interactive API Documentation**: `http://localhost:5000/api/docs`
- **OpenAPI JSON Specification**: `http://localhost:5000/swagger.json`

The Swagger UI provides:
- Interactive testing interface for all endpoints
- Automatic request/response documentation
- Model schemas with examples
- Try-it-out functionality
- Export capabilities for API client generation

## Authentication

Currently, the API does not require authentication. In production, implement appropriate authentication mechanisms.

## Content Types

- **Request**: `application/json` (for JSON payloads), `multipart/form-data` (for file uploads)
- **Response**: `application/json`, `application/xml` (for file downloads)

## Error Handling

All error responses follow this format:

```json
{
    "error": "Error message description"
}
```

Common HTTP status codes:
- `200 OK` - Successful request
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request parameters
- `404 Not Found` - Resource not found
- `413 Request Entity Too Large` - File size exceeds limit (16MB)
- `500 Internal Server Error` - Server error

## Endpoints

### 1. Health Check

Check if the API is running and healthy.

**Endpoint:** `GET /health`

**Response:**
```json
{
    "status": "healthy",
    "service": "XML RESTful API",
    "version": "1.0.0"
}
```

### 2. Upload XML File

Upload an XML file to the server.

**Endpoint:** `POST /xml/upload`

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: Form data with file field

**Example using cURL:**
```bash
curl -X POST http://localhost:5000/api/xml/upload \
  -F "file=@example.xml"
```

**Success Response (201):**
```json
{
    "message": "XML file uploaded successfully",
    "file_id": "550e8400-e29b-41d4-a716-446655440000",
    "filename": "example.xml"
}
```

**Error Responses:**
- `400 Bad Request` - No file provided, invalid XML, or wrong file format
- `413 Request Entity Too Large` - File exceeds 16MB limit

### 3. Retrieve XML File

Download a previously uploaded XML file.

**Endpoint:** `GET /xml/{file_id}`

**Parameters:**
- `file_id` (path parameter) - UUID of the uploaded file

**Example:**
```bash
curl -X GET http://localhost:5000/api/xml/550e8400-e29b-41d4-a716-446655440000 \
  -o downloaded.xml
```

**Success Response (200):**
- Content-Type: `application/xml`
- Body: XML file content

**Error Response:**
- `404 Not Found` - File not found

### 4. List All XML Files

Get a list of all uploaded XML files.

**Endpoint:** `GET /xml`

**Example:**
```bash
curl -X GET http://localhost:5000/api/xml
```

**Success Response (200):**
```json
{
    "count": 2,
    "files": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "filename": "books.xml",
            "uploaded_at": "1672531200"
        },
        {
            "id": "660e8400-e29b-41d4-a716-446655440001",
            "filename": "catalog.xml",
            "uploaded_at": "1672531300"
        }
    ]
}
```

### 5. Get XML Elements by XPath

Retrieve specific elements from an XML file using XPath.

**Endpoint:** `GET /xml/{file_id}/element`

**Parameters:**
- `file_id` (path parameter) - UUID of the XML file
- `xpath` (query parameter) - XPath expression

**Example:**
```bash
curl -X GET "http://localhost:5000/api/xml/550e8400-e29b-41d4-a716-446655440000/element?xpath=//book[@genre='fiction']"
```

**Success Response (200):**
```json
{
    "file_id": "550e8400-e29b-41d4-a716-446655440000",
    "xpath": "//book[@genre='fiction']",
    "count": 2,
    "elements": [
        {
            "tag": "book",
            "text": null,
            "attributes": {
                "id": "1",
                "genre": "fiction"
            },
            "xml": "<book id=\"1\" genre=\"fiction\">\n  <title>The Great Gatsby</title>\n  <author>F. Scott Fitzgerald</author>\n</book>"
        }
    ]
}
```

**Error Responses:**
- `400 Bad Request` - Missing XPath parameter or invalid XPath syntax
- `404 Not Found` - File not found

### 6. Add XML Element

Add a new element to an XML file.

**Endpoint:** `POST /xml/{file_id}/element`

**Parameters:**
- `file_id` (path parameter) - UUID of the XML file

**Request Body:**
```json
{
    "parent_xpath": "/library",
    "tag": "book",
    "text": "",
    "attributes": {
        "id": "3",
        "genre": "mystery"
    }
}
```

**Required Fields:**
- `parent_xpath` - XPath to the parent element
- `tag` - Tag name for the new element

**Optional Fields:**
- `text` - Text content of the element
- `attributes` - Object containing attribute key-value pairs

**Example:**
```bash
curl -X POST http://localhost:5000/api/xml/550e8400-e29b-41d4-a716-446655440000/element \
  -H "Content-Type: application/json" \
  -d '{
    "parent_xpath": "/library",
    "tag": "book",
    "attributes": {"id": "3", "genre": "mystery"}
  }'
```

**Success Response (201):**
```json
{
    "message": "Element added successfully",
    "file_id": "550e8400-e29b-41d4-a716-446655440000",
    "element": {
        "tag": "book",
        "text": null,
        "attributes": {
            "id": "3",
            "genre": "mystery"
        }
    }
}
```

### 7. Update XML Element

Update an existing element in an XML file.

**Endpoint:** `PUT /xml/{file_id}/element`

**Parameters:**
- `file_id` (path parameter) - UUID of the XML file

**Request Body:**
```json
{
    "xpath": "//book[@id='1']/title",
    "text": "Updated Title",
    "attributes": {
        "lang": "en"
    },
    "clear_attributes": false
}
```

**Required Fields:**
- `xpath` - XPath to the element to update

**Optional Fields:**
- `text` - New text content
- `attributes` - New or updated attributes
- `clear_attributes` - Boolean to clear existing attributes before setting new ones

**Example:**
```bash
curl -X PUT http://localhost:5000/api/xml/550e8400-e29b-41d4-a716-446655440000/element \
  -H "Content-Type: application/json" \
  -d '{
    "xpath": "//book[@id=\"1\"]/title",
    "text": "The Great Gatsby (Revised Edition)"
  }'
```

**Success Response (200):**
```json
{
    "message": "Element updated successfully",
    "file_id": "550e8400-e29b-41d4-a716-446655440000",
    "element": {
        "tag": "title",
        "text": "The Great Gatsby (Revised Edition)",
        "attributes": {}
    }
}
```

### 8. Delete XML Element

Delete elements from an XML file.

**Endpoint:** `DELETE /xml/{file_id}/element`

**Parameters:**
- `file_id` (path parameter) - UUID of the XML file
- `xpath` (query parameter) - XPath expression to select elements for deletion

**Example:**
```bash
curl -X DELETE "http://localhost:5000/api/xml/550e8400-e29b-41d4-a716-446655440000/element?xpath=//book[@id='2']"
```

**Success Response (200):**
```json
{
    "message": "Elements deleted successfully",
    "file_id": "550e8400-e29b-41d4-a716-446655440000",
    "deleted_count": 1
}
```

### 9. Transform XML with XSLT

Transform an XML file using an XSLT stylesheet.

**Endpoint:** `POST /xml/{file_id}/transform`

**Parameters:**
- `file_id` (path parameter) - UUID of the XML file to transform

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: Form data with XSLT file

**Example:**
```bash
curl -X POST http://localhost:5000/api/xml/550e8400-e29b-41d4-a716-446655440000/transform \
  -F "xslt=@transform.xsl"
```

**Success Response (200):**
```json
{
    "message": "XML transformed successfully",
    "original_file_id": "550e8400-e29b-41d4-a716-446655440000",
    "transformed_file_id": "770e8400-e29b-41d4-a716-446655440002",
    "download_url": "/api/xml/770e8400-e29b-41d4-a716-446655440002"
}
```

**Error Responses:**
- `400 Bad Request` - No XSLT file provided or wrong file format
- `404 Not Found` - Original XML file not found
- `500 Internal Server Error` - XSLT transformation error

### 10. Delete XML File

Delete an XML file from the server.

**Endpoint:** `DELETE /xml/{file_id}`

**Parameters:**
- `file_id` (path parameter) - UUID of the file to delete

**Example:**
```bash
curl -X DELETE http://localhost:5000/api/xml/550e8400-e29b-41d4-a716-446655440000
```

**Success Response (200):**
```json
{
    "message": "File deleted successfully",
    "file_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## XPath Examples

Here are some useful XPath expressions for querying XML:

1. **Select all elements of a specific type:**
   ```
   //book
   ```

2. **Select elements with specific attribute:**
   ```
   //book[@genre='fiction']
   ```

3. **Select elements with specific text content:**
   ```
   //title[text()='The Great Gatsby']
   ```

4. **Select first element:**
   ```
   //book[1]
   ```

5. **Select elements containing text:**
   ```
   //title[contains(text(), 'Gatsby')]
   ```

6. **Select child elements:**
   ```
   /library/book/title
   ```

7. **Select elements with multiple conditions:**
   ```
   //book[@genre='fiction' and @id='1']
   ```

## Example XML File

Here's an example XML file that works well with this API:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<library>
    <book id="1" genre="fiction">
        <title>The Great Gatsby</title>
        <author>F. Scott Fitzgerald</author>
        <year>1925</year>
        <price currency="USD">10.99</price>
    </book>
    <book id="2" genre="science">
        <title>A Brief History of Time</title>
        <author>Stephen Hawking</author>
        <year>1988</year>
        <price currency="USD">15.99</price>
    </book>
</library>
```

## Example XSLT File

Here's an example XSLT file for transformation:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="xml" indent="yes"/>
    
    <xsl:template match="/">
        <catalog>
            <xsl:for-each select="library/book">
                <item>
                    <xsl:attribute name="id">
                        <xsl:value-of select="@id"/>
                    </xsl:attribute>
                    <name><xsl:value-of select="title"/></name>
                    <creator><xsl:value-of select="author"/></creator>
                    <cost><xsl:value-of select="price"/></cost>
                </item>
            </xsl:for-each>
        </catalog>
    </xsl:template>
</xsl:stylesheet>
```

## Rate Limiting

Currently, no rate limiting is implemented. In production, consider implementing rate limiting to prevent abuse.

## CORS

CORS is enabled for all origins. In production, configure CORS to allow only trusted origins.

## Security Considerations

1. **File Upload Security**: Only XML and XSL/XSLT files are accepted
2. **File Size Limit**: Maximum file size is 16MB
3. **XPath Injection**: Be cautious with user-provided XPath expressions
4. **XML External Entity (XXE) Attacks**: The parser is configured to be secure by default

## Running the API

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   
   **Option 1: Basic API**
   ```bash
   python src/app.py
   ```

   **Option 2: API with Swagger UI (Recommended)**
   ```bash
   python start_api_swagger.py
   ```
   This will automatically open the Swagger UI in your browser.

3. The API will be available at `http://localhost:5000`
4. If using Swagger, the documentation will be at `http://localhost:5000/api/docs`

## Testing the API

### Using Swagger UI

1. Start the API with Swagger:
   ```bash
   python start_api_swagger.py
   ```

2. Navigate to `http://localhost:5000/api/docs`

3. Click on any endpoint to expand it

4. Click "Try it out" to test the endpoint interactively

5. Fill in the required parameters and click "Execute"

### Using the Test Suite

Run the automated test suite:
```bash
pytest tests/ -v
```

### Using the Example Script

Run the comprehensive example script:
```bash
# First, start the API server
python start_api_swagger.py

# In another terminal, run the examples
python examples/test_api.py
```

## Future Enhancements

1. Add authentication and authorization
2. Implement database storage instead of in-memory storage
3. Add support for XML schema validation
4. Implement batch operations
5. Add WebSocket support for real-time updates
6. Implement caching for frequently accessed files
7. Add support for compressed XML files