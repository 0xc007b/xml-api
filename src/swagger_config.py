"""
Swagger/OpenAPI Configuration for XML RESTful API

This module contains configuration and customization for the Swagger UI
and OpenAPI documentation.
"""

from flask import Flask
from flask_restx import Api, fields

# Swagger UI configuration
SWAGGER_CONFIG = {
    'doc': '/docs',
    'title': 'XML RESTful API',
    'version': '1.0.0',
    'description': '''
A comprehensive RESTful API for XML file manipulation with XSLT transformation capabilities.

## Features

- **XML File Management**: Upload, retrieve, list, and delete XML files
- **Element Manipulation**: Add, update, delete, and query XML elements using XPath
- **XSLT Transformation**: Transform XML files using XSLT stylesheets
- **XPath Support**: Query XML content using powerful XPath expressions
- **Validation**: Automatic XML validation on upload
- **RESTful Design**: Clean and intuitive API endpoints

## Getting Started

1. Upload an XML file using the `/xml/upload` endpoint
2. Use the returned `file_id` to perform operations on the file
3. Query elements using XPath expressions
4. Transform XML files with custom XSLT stylesheets

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
</library>
```

## XPath Examples

- Select all books: `//book`
- Select by attribute: `//book[@genre='fiction']`
- Select by ID: `//book[@id='1']`
- Select with conditions: `//book[price < 15]`

## Support

For detailed documentation, visit the [GitHub repository](https://github.com/your-repo/xml-api)
    ''',
    'contact': {
        'name': 'API Support',
        'email': 'support@example.com'
    },
    'license': {
        'name': 'MIT',
        'url': 'https://opensource.org/licenses/MIT'
    },
    'servers': [
        {
            'url': 'http://localhost:5000',
            'description': 'Development server'
        },
        {
            'url': 'https://api.example.com',
            'description': 'Production server'
        }
    ],
    'tags': [
        {
            'name': 'health',
            'description': 'Health check operations'
        },
        {
            'name': 'xml',
            'description': 'XML file and element operations'
        }
    ],
    'authorizations': {
        'apikey': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'X-API-Key',
            'description': 'API key for authentication (not implemented in development)'
        }
    }
}

# Custom Swagger UI settings
SWAGGER_UI_CONFIG = {
    'docExpansion': 'list',  # 'none', 'list', or 'full'
    'defaultModelsExpandDepth': 2,
    'defaultModelExpandDepth': 2,
    'displayRequestDuration': True,
    'filter': True,
    'showExtensions': True,
    'showCommonExtensions': True,
    'tryItOutEnabled': True,
    'displayOperationId': False,
    'persistAuthorization': True,
    'syntaxHighlight.theme': 'monokai'
}

# API metadata
API_METADATA = {
    'x-logo': {
        'url': 'https://example.com/logo.png',
        'altText': 'XML API Logo'
    },
    'x-api-id': 'xml-restful-api-v1',
    'x-audience': 'public',
    'x-api-category': 'data-processing'
}


def configure_swagger(app: Flask, api: Api):
    """
    Configure Swagger UI and OpenAPI documentation

    Args:
        app: Flask application instance
        api: Flask-RESTX API instance
    """
    # Apply Swagger UI configuration
    app.config.update({
        'SWAGGER_UI_DOC_EXPANSION': SWAGGER_UI_CONFIG['docExpansion'],
        'SWAGGER_UI_OPERATION_ID': SWAGGER_UI_CONFIG['displayOperationId'],
        'SWAGGER_UI_REQUEST_DURATION': SWAGGER_UI_CONFIG['displayRequestDuration'],
        'SWAGGER_UI_TRY_IT_OUT_ENABLED': SWAGGER_UI_CONFIG['tryItOutEnabled']
    })

    # Add custom headers for API responses
    @app.after_request
    def add_api_headers(response):
        response.headers['X-API-Version'] = '1.0.0'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response


# Response examples for documentation
RESPONSE_EXAMPLES = {
    'upload_success': {
        'message': 'XML file uploaded successfully',
        'file_id': '550e8400-e29b-41d4-a716-446655440000',
        'filename': 'example.xml'
    },
    'element_found': {
        'file_id': '550e8400-e29b-41d4-a716-446655440000',
        'xpath': '//book[@genre="fiction"]',
        'count': 2,
        'elements': [
            {
                'tag': 'book',
                'text': None,
                'attributes': {
                    'id': '1',
                    'genre': 'fiction'
                },
                'xml': '<book id="1" genre="fiction">...</book>'
            }
        ]
    },
    'transform_success': {
        'message': 'XML transformed successfully',
        'original_file_id': '550e8400-e29b-41d4-a716-446655440000',
        'transformed_file_id': '660e8400-e29b-41d4-a716-446655440001',
        'download_url': '/api/xml/660e8400-e29b-41d4-a716-446655440001'
    },
    'error_response': {
        'error': 'File not found'
    }
}


# Request examples for documentation
REQUEST_EXAMPLES = {
    'add_element': {
        'parent_xpath': '/library/books',
        'tag': 'book',
        'text': '',
        'attributes': {
            'id': '3',
            'genre': 'mystery'
        }
    },
    'update_element': {
        'xpath': '//book[@id="1"]/title',
        'text': 'The Great Gatsby (Revised Edition)',
        'attributes': {
            'lang': 'en'
        },
        'clear_attributes': False
    }
}


def create_error_model(api: Api):
    """Create reusable error response model"""
    return api.model('Error', {
        'error': fields.String(
            required=True,
            description='Error message',
            example='File not found'
        ),
        'code': fields.Integer(
            description='Error code',
            example=404
        ),
        'details': fields.Raw(
            description='Additional error details'
        )
    })


def create_pagination_model(api: Api):
    """Create reusable pagination model"""
    return api.model('Pagination', {
        'page': fields.Integer(
            description='Current page number',
            example=1
        ),
        'per_page': fields.Integer(
            description='Items per page',
            example=20
        ),
        'total': fields.Integer(
            description='Total number of items',
            example=100
        ),
        'pages': fields.Integer(
            description='Total number of pages',
            example=5
        )
    })
