# XML RESTful API

A comprehensive RESTful API for XML file manipulation with XSLT transformation capabilities. This project provides endpoints for uploading, retrieving, transforming, and performing CRUD operations on XML files and their elements.

## Features

- **XML File Management**: Upload, retrieve, list, and delete XML files
- **Element Manipulation**: Add, update, delete, and query XML elements using XPath
- **XSLT Transformation**: Transform XML files using XSLT stylesheets
- **XPath Support**: Query XML content using XPath expressions
- **Validation**: Automatic XML validation on upload
- **RESTful Design**: Clean and intuitive API endpoints
- **Error Handling**: Comprehensive error messages and appropriate HTTP status codes

## Technologies Used

- **Python 3.8+**
- **Flask**: Web framework for building the RESTful API
- **lxml**: XML processing library with XPath and XSLT support
- **pytest**: Testing framework
- **flask-cors**: CORS support for cross-origin requests
- **flask-restx**: RESTful API with Swagger/OpenAPI documentation

## Project Structure

```
Devoir/
├── src/
│   ├── app.py          # Main Flask application
│   ├── app_swagger.py  # Flask application with Swagger UI
│   └── xml_utils.py    # XML utility functions
├── tests/
│   ├── test_api.py     # API endpoint tests
│   └── test_xml_utils.py # XML utility tests
├── data/
│   ├── xml_files/      # Uploaded XML files storage
│   └── xslt_files/     # Temporary XSLT files storage
├── docs/
│   ├── API_DOCUMENTATION.md  # Detailed API documentation
│   └── Fiche projet no 5.pdf # Project requirements
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Devoir
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On Linux/Mac
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

### Option 1: Basic API (without Swagger)
```bash
python src/app.py
```

### Option 2: API with Swagger UI (Recommended)
```bash
python start_api_swagger.py
```

The Swagger UI will automatically open in your browser at `http://localhost:5000/api/docs`

### Option 3: Using the startup scripts
```bash
# Basic API
python start_api.py

# API with Swagger (opens browser automatically)
python start_api_swagger.py --host 127.0.0.1 --port 5000
```

The API will be available at `http://localhost:5000`

Check the health endpoint:
```bash
curl http://localhost:5000/api/health
```

## Quick Start Guide

### 1. Upload an XML file
```bash
curl -X POST http://localhost:5000/api/xml/upload \
  -F "file=@example.xml"
```

### 2. List all uploaded files
```bash
curl http://localhost:5000/api/xml
```

### 3. Query XML elements
```bash
curl "http://localhost:5000/api/xml/{file_id}/element?xpath=//book"
```

### 4. Transform XML with XSLT
```bash
curl -X POST http://localhost:5000/api/xml/{file_id}/transform \
  -F "xslt=@transform.xsl"
```

## API Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/xml/upload` | Upload XML file |
| GET | `/api/xml` | List all XML files |
| GET | `/api/xml/{file_id}` | Download XML file |
| GET | `/api/xml/{file_id}/element` | Get elements by XPath |
| POST | `/api/xml/{file_id}/element` | Add new element |
| PUT | `/api/xml/{file_id}/element` | Update element |
| DELETE | `/api/xml/{file_id}/element` | Delete element |
| POST | `/api/xml/{file_id}/transform` | Transform with XSLT |
| DELETE | `/api/xml/{file_id}` | Delete XML file |

For detailed API documentation, see [API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md).

## Swagger Documentation

When running the API with Swagger support (`python start_api_swagger.py`), you can access:

- **Interactive API Documentation**: `http://localhost:5000/api/docs`
- **OpenAPI Specification**: `http://localhost:5000/swagger.json`

The Swagger UI provides:
- Interactive API testing interface
- Automatic request/response documentation
- Model schemas and examples
- Try-it-out functionality for all endpoints

## Testing

Run the complete test suite:
```bash
pytest tests/ -v
```

Run specific test files:
```bash
# Test API endpoints
pytest tests/test_api.py -v

# Test XML utilities
pytest tests/test_xml_utils.py -v
```

Generate coverage report:
```bash
pytest tests/ --cov=src --cov-report=html
```

## Example XML File

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

```xml
<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="xml" indent="yes"/>
    
    <xsl:template match="/">
        <books>
            <xsl:for-each select="library/book">
                <book>
                    <xsl:attribute name="id">
                        <xsl:value-of select="@id"/>
                    </xsl:attribute>
                    <name><xsl:value-of select="title"/></name>
                    <writer><xsl:value-of select="author"/></writer>
                </book>
            </xsl:for-each>
        </books>
    </xsl:template>
</xsl:stylesheet>
```

## Configuration

The application uses the following default configurations:

- **Maximum file size**: 16MB
- **Server port**: 5000
- **Debug mode**: Enabled (disable in production)
- **CORS**: Enabled for all origins (restrict in production)

## Error Handling

The API returns appropriate HTTP status codes and error messages:

- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `413 Request Entity Too Large`: File size exceeds limit
- `500 Internal Server Error`: Server error

Error responses follow this format:
```json
{
    "error": "Descriptive error message"
}
```

## Security Considerations

1. **Input Validation**: All XML content is validated before processing
2. **File Type Restriction**: Only XML and XSL/XSLT files are accepted
3. **Size Limits**: Maximum file size is limited to 16MB
4. **XPath Injection**: Be cautious with user-provided XPath expressions
5. **XXE Protection**: XML parser is configured to prevent XXE attacks

## Production Deployment

For production deployment, consider:

1. **Disable debug mode** in `app.py`
2. **Use a production WSGI server** (e.g., Gunicorn, uWSGI)
3. **Implement authentication** and authorization
4. **Configure CORS** to allow only trusted origins
5. **Use a database** instead of in-memory storage
6. **Set up proper logging** and monitoring
7. **Implement rate limiting** to prevent abuse
8. **Use HTTPS** for secure communication

Example Gunicorn deployment:
```bash
# For basic API
gunicorn -w 4 -b 0.0.0.0:5000 src.app:app

# For API with Swagger
gunicorn -w 4 -b 0.0.0.0:5000 src.app_swagger:app
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is developed as part of an academic assignment. Please refer to your institution's guidelines for usage and distribution.

## Acknowledgments

- Flask documentation for excellent framework guidance
- lxml documentation for XML processing capabilities
- Project requirements from "Fiche projet no 5.pdf"