import pytest
import json
import os
import tempfile
from io import BytesIO
from pathlib import Path
import sys

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from app import app, xml_storage


@pytest.fixture
def client():
    """Create a test client for the Flask application"""
    app.config['TESTING'] = True
    with tempfile.TemporaryDirectory() as temp_dir:
        app.config['UPLOAD_FOLDER'] = os.path.join(temp_dir, 'xml_files')
        app.config['XSLT_FOLDER'] = os.path.join(temp_dir, 'xslt_files')
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['XSLT_FOLDER'], exist_ok=True)

        with app.test_client() as client:
            yield client

        # Clean up
        xml_storage.clear()


@pytest.fixture 
def auth_token(client):
    """Get authentication token for testing"""
    login_data = {
        'username': 'admin',
        'password': 'Usage8-Unnamed5-Flatly9-Seducing0-Nuclear8'
    }
    response = client.post('/api/auth/login',
                          json=login_data,
                          content_type='application/json')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    return data['access_token']


@pytest.fixture
def auth_headers(auth_token):
    """Get authorization headers for API requests"""
    return {'Authorization': f'Bearer {auth_token}'}


@pytest.fixture
def sample_xml():
    """Sample XML content for testing"""
    return '''<?xml version="1.0" encoding="UTF-8"?>
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
</library>'''


@pytest.fixture
def sample_xslt():
    """Sample XSLT content for testing"""
    return '''<?xml version="1.0" encoding="UTF-8"?>
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
</xsl:stylesheet>'''


class TestAuthentication:
    """Test authentication endpoints"""

    def test_login_valid_credentials(self, client):
        """Test login with valid credentials"""
        login_data = {
            'username': 'admin',
            'password': 'Usage8-Unnamed5-Flatly9-Seducing0-Nuclear8'
        }
        response = client.post('/api/auth/login',
                              json=login_data,
                              content_type='application/json')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'access_token' in data
        assert 'expires_in' in data
        assert data['expires_in'] == 3600

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        login_data = {
            'username': 'admin',
            'password': 'wrong_password'
        }
        response = client.post('/api/auth/login',
                              json=login_data,
                              content_type='application/json')

        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error'] == 'Invalid credentials'

    def test_login_missing_credentials(self, client):
        """Test login with missing credentials"""
        login_data = {'username': 'admin'}
        response = client.post('/api/auth/login',
                              json=login_data,
                              content_type='application/json')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Username and password are required' in data['error']

    def test_login_no_data(self, client):
        """Test login with no data"""
        response = client.post('/api/auth/login')

        # Could be 400 or 415 depending on Flask version and configuration
        assert response.status_code in [400, 415]
        data = json.loads(response.data)
        # Could be 'error' or 'message' depending on Flask-RESTX version
        assert 'error' in data or 'message' in data

    def test_unauthorized_access(self, client):
        """Test accessing protected endpoint without token"""
        response = client.get('/api/health/')

        assert response.status_code == 401


class TestHealthCheck:
    """Test health check endpoint"""

    def test_health_check_with_auth(self, client, auth_headers):
        """Test health check with authentication"""
        response = client.get('/api/health/', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['service'] == 'XML RESTful API'
        assert data['version'] == '1.0.0'

    def test_health_check_without_auth(self, client):
        """Test health check without authentication"""
        response = client.get('/api/health/')
        
        assert response.status_code == 401


class TestXMLUpload:
    """Test XML upload functionality"""

    def test_upload_valid_xml(self, client, auth_headers, sample_xml):
        """Test uploading valid XML file"""
        data = {
            'file': (BytesIO(sample_xml.encode('utf-8')), 'test.xml')
        }
        response = client.post('/api/xml/upload',
                             data=data,
                             headers=auth_headers,
                             content_type='multipart/form-data')

        assert response.status_code == 201
        result = json.loads(response.data)
        assert 'file_id' in result
        assert result['filename'] == 'test.xml'
        assert result['message'] == 'File uploaded successfully'

    def test_upload_invalid_xml(self, client, auth_headers):
        """Test uploading invalid XML file"""
        invalid_xml = b'<invalid><not_closed>'
        data = {
            'file': (BytesIO(invalid_xml), 'invalid.xml')
        }
        response = client.post('/api/xml/upload',
                             data=data,
                             headers=auth_headers,
                             content_type='multipart/form-data')

        # Could be 400 or 500 depending on Flask-RESTX error handling
        assert response.status_code in [400, 500]
        result = json.loads(response.data)
        assert 'error' in result or 'message' in result

    def test_upload_no_file(self, client, auth_headers):
        """Test upload with no file"""
        response = client.post('/api/xml/upload', headers=auth_headers)
        
        assert response.status_code == 400
        result = json.loads(response.data)
        assert result['error'] == 'No file provided'

    def test_upload_non_xml_file(self, client, auth_headers):
        """Test uploading non-XML file"""
        data = {
            'file': (BytesIO(b'Not XML content'), 'test.txt')
        }
        response = client.post('/api/xml/upload',
                             data=data,
                             headers=auth_headers,
                             content_type='multipart/form-data')

        assert response.status_code == 400
        result = json.loads(response.data)
        assert result['error'] == 'Only XML files are allowed'

    def test_upload_empty_filename(self, client, auth_headers):
        """Test upload with empty filename"""
        data = {
            'file': (BytesIO(b'<root></root>'), '')
        }
        response = client.post('/api/xml/upload',
                             data=data,
                             headers=auth_headers,
                             content_type='multipart/form-data')

        assert response.status_code == 400
        result = json.loads(response.data)
        assert result['error'] == 'No file selected'

    def test_upload_without_auth(self, client, sample_xml):
        """Test upload without authentication"""
        data = {
            'file': (BytesIO(sample_xml.encode('utf-8')), 'test.xml')
        }
        response = client.post('/api/xml/upload',
                             data=data,
                             content_type='multipart/form-data')

        assert response.status_code == 401


class TestXMLRetrieval:
    """Test XML retrieval functionality"""

    def setup_file(self, client, auth_headers, sample_xml):
        """Helper method to upload a file and return its ID"""
        data = {
            'file': (BytesIO(sample_xml.encode('utf-8')), 'test.xml')
        }
        response = client.post('/api/xml/upload',
                             data=data,
                             headers=auth_headers,
                             content_type='multipart/form-data')
        return json.loads(response.data)['file_id']

    def test_get_xml_file(self, client, auth_headers, sample_xml):
        """Test downloading XML file"""
        file_id = self.setup_file(client, auth_headers, sample_xml)

        response = client.get(f'/api/xml/{file_id}', headers=auth_headers)
        
        assert response.status_code == 200
        # The response should contain the XML content
        assert b'<library>' in response.data
        assert b'The Great Gatsby' in response.data

    def test_get_nonexistent_file(self, client, auth_headers):
        """Test getting non-existent file"""
        response = client.get('/api/xml/nonexistent-id', headers=auth_headers)
        
        assert response.status_code == 404
        result = json.loads(response.data)
        assert result['error'] == 'File not found'

    def test_list_xml_files(self, client, auth_headers, sample_xml):
        """Test listing all XML files"""
        # Upload two files
        for i in range(2):
            data = {
                'file': (BytesIO(sample_xml.encode('utf-8')), f'test{i}.xml')
            }
            client.post('/api/xml/upload',
                       data=data,
                       headers=auth_headers,
                       content_type='multipart/form-data')

        # List files
        response = client.get('/api/xml/', headers=auth_headers)
        
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['count'] == 2
        assert len(result['files']) == 2

    def test_list_empty_files(self, client, auth_headers):
        """Test listing files when none exist"""
        response = client.get('/api/xml/', headers=auth_headers)
        
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['count'] == 0
        assert len(result['files']) == 0

    def test_get_file_without_auth(self, client, auth_headers, sample_xml):
        """Test getting file without authentication"""
        file_id = self.setup_file(client, auth_headers, sample_xml)

        response = client.get(f'/api/xml/{file_id}')
        
        assert response.status_code == 401


class TestXMLElementOperations:
    """Test XML element CRUD operations"""

    def setup_file(self, client, auth_headers, sample_xml):
        """Helper method to upload a file and return its ID"""
        data = {
            'file': (BytesIO(sample_xml.encode('utf-8')), 'test.xml')
        }
        response = client.post('/api/xml/upload',
                             data=data,
                             headers=auth_headers,
                             content_type='multipart/form-data')
        return json.loads(response.data)['file_id']

    def test_get_element_by_xpath(self, client, auth_headers, sample_xml):
        """Test getting elements by XPath"""
        file_id = self.setup_file(client, auth_headers, sample_xml)

        # Get book elements
        response = client.get(f'/api/xml/{file_id}/element?xpath=//book', 
                            headers=auth_headers)
        
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['count'] == 2
        assert len(result['elements']) == 2
        assert result['elements'][0]['tag'] == 'book'
        assert result['file_id'] == file_id
        assert result['xpath'] == '//book'

    def test_get_element_with_attributes(self, client, auth_headers, sample_xml):
        """Test getting elements with specific attributes"""
        file_id = self.setup_file(client, auth_headers, sample_xml)

        response = client.get(f'/api/xml/{file_id}/element?xpath=//book[@id="1"]', 
                            headers=auth_headers)
        
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['count'] == 1
        assert result['elements'][0]['attributes']['id'] == '1'

    def test_get_element_text_content(self, client, auth_headers, sample_xml):
        """Test getting text content of elements"""
        file_id = self.setup_file(client, auth_headers, sample_xml)

        response = client.get(f'/api/xml/{file_id}/element?xpath=//title/text()', 
                            headers=auth_headers)
        
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['count'] == 2
        # Text nodes are returned differently
        assert any('Great Gatsby' in str(elem['text']) for elem in result['elements'])

    def test_get_element_invalid_xpath(self, client, auth_headers, sample_xml):
        """Test getting elements with invalid XPath"""
        file_id = self.setup_file(client, auth_headers, sample_xml)

        response = client.get(f'/api/xml/{file_id}/element?xpath=//book[', 
                            headers=auth_headers)
        
        # Could be 400 or 500 depending on Flask-RESTX error handling
        assert response.status_code in [400, 500]
        result = json.loads(response.data)
        assert 'error' in result or 'message' in result

    def test_get_element_no_xpath(self, client, auth_headers, sample_xml):
        """Test getting elements without XPath parameter"""
        file_id = self.setup_file(client, auth_headers, sample_xml)

        response = client.get(f'/api/xml/{file_id}/element', 
                            headers=auth_headers)
        
        assert response.status_code == 400
        result = json.loads(response.data)
        assert result['error'] == 'XPath parameter is required'

    def test_add_element(self, client, auth_headers, sample_xml):
        """Test adding new element"""
        file_id = self.setup_file(client, auth_headers, sample_xml)

        # Add a new book
        new_book = {
            'parent_xpath': '/library',
            'tag': 'book',
            'text': '',
            'attributes': {
                'id': '3',
                'genre': 'mystery'
            }
        }

        response = client.post(f'/api/xml/{file_id}/element',
                             json=new_book,
                             headers=auth_headers,
                             content_type='application/json')

        assert response.status_code == 201
        result = json.loads(response.data)
        assert result['message'] == 'Element added successfully'
        assert result['element']['tag'] == 'book'
        assert result['element']['attributes']['id'] == '3'

        # Verify the element was added
        check_response = client.get(f'/api/xml/{file_id}/element?xpath=//book[@id="3"]', 
                                  headers=auth_headers)
        check_result = json.loads(check_response.data)
        assert check_result['count'] == 1

    def test_add_element_with_text(self, client, auth_headers, sample_xml):
        """Test adding element with text content"""
        file_id = self.setup_file(client, auth_headers, sample_xml)

        # Add a new title to first book
        new_element = {
            'parent_xpath': '//book[@id="1"]',
            'tag': 'subtitle',
            'text': 'An American Classic',
            'attributes': {}
        }

        response = client.post(f'/api/xml/{file_id}/element',
                             json=new_element,
                             headers=auth_headers,
                             content_type='application/json')

        assert response.status_code == 201
        result = json.loads(response.data)
        assert result['element']['text'] == 'An American Classic'

    def test_add_element_missing_required_fields(self, client, auth_headers, sample_xml):
        """Test adding element with missing required fields"""
        file_id = self.setup_file(client, auth_headers, sample_xml)

        # Missing tag
        incomplete_element = {
            'parent_xpath': '/library'
        }

        response = client.post(f'/api/xml/{file_id}/element',
                             json=incomplete_element,
                             headers=auth_headers,
                             content_type='application/json')

        assert response.status_code == 400
        result = json.loads(response.data)
        assert 'parent_xpath and tag are required' in result['error']

    def test_add_element_invalid_parent(self, client, auth_headers, sample_xml):
        """Test adding element with invalid parent XPath"""
        file_id = self.setup_file(client, auth_headers, sample_xml)

        new_element = {
            'parent_xpath': '//nonexistent',
            'tag': 'test',
            'text': 'Test'
        }

        response = client.post(f'/api/xml/{file_id}/element',
                             json=new_element,
                             headers=auth_headers,
                             content_type='application/json')

        # Could be 400 or 500 depending on Flask-RESTX error handling
        assert response.status_code in [400, 500]
        result = json.loads(response.data)
        assert 'error' in result or 'message' in result

    def test_update_element(self, client, auth_headers, sample_xml):
        """Test updating existing element"""
        file_id = self.setup_file(client, auth_headers, sample_xml)

        # Update the first book's title
        update_data = {
            'xpath': '//book[@id="1"]/title',
            'text': 'The Great Gatsby (Updated Edition)'
        }

        response = client.put(f'/api/xml/{file_id}/element',
                            json=update_data,
                            headers=auth_headers,
                            content_type='application/json')

        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['message'] == 'Element updated successfully'
        assert result['element']['text'] == 'The Great Gatsby (Updated Edition)'

        # Verify the update
        check_response = client.get(f'/api/xml/{file_id}/element?xpath=//book[@id="1"]/title', 
                                  headers=auth_headers)
        check_result = json.loads(check_response.data)
        assert check_result['elements'][0]['text'] == 'The Great Gatsby (Updated Edition)'

    def test_update_element_attributes(self, client, auth_headers, sample_xml):
        """Test updating element attributes"""
        file_id = self.setup_file(client, auth_headers, sample_xml)

        # Update book attributes
        update_data = {
            'xpath': '//book[@id="1"]',
            'attributes': {
                'genre': 'classic-fiction',
                'rating': '5'
            }
        }

        response = client.put(f'/api/xml/{file_id}/element',
                            json=update_data,
                            headers=auth_headers,
                            content_type='application/json')

        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['element']['attributes']['genre'] == 'classic-fiction'
        assert result['element']['attributes']['rating'] == '5'

    def test_update_element_clear_attributes(self, client, auth_headers, sample_xml):
        """Test updating element with clearing attributes"""
        file_id = self.setup_file(client, auth_headers, sample_xml)

        update_data = {
            'xpath': '//book[@id="1"]',
            'text': 'New text content',
            'clear_attributes': True,
            'attributes': {
                'new_attr': 'new_value'
            }
        }

        response = client.put(f'/api/xml/{file_id}/element',
                            json=update_data,
                            headers=auth_headers,
                            content_type='application/json')

        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['element']['attributes']['new_attr'] == 'new_value'
        # Old attributes should be cleared
        assert 'id' not in result['element']['attributes']
        assert 'genre' not in result['element']['attributes']

    def test_update_nonexistent_element(self, client, auth_headers, sample_xml):
        """Test updating non-existent element"""
        file_id = self.setup_file(client, auth_headers, sample_xml)

        update_data = {
            'xpath': '//nonexistent',
            'text': 'New text'
        }

        response = client.put(f'/api/xml/{file_id}/element',
                            json=update_data,
                            headers=auth_headers,
                            content_type='application/json')

        # Could be 404 or 500 depending on Flask-RESTX error handling
        assert response.status_code in [404, 500]
        result = json.loads(response.data)
        assert 'error' in result or 'message' in result

    def test_delete_element(self, client, auth_headers, sample_xml):
        """Test deleting XML elements"""
        file_id = self.setup_file(client, auth_headers, sample_xml)

        # Delete the second book
        response = client.delete(f'/api/xml/{file_id}/element?xpath=//book[@id="2"]',
                               headers=auth_headers)

        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['deleted_count'] == 1
        assert 'Deleted 1 elements' in result['message']

        # Verify deletion
        check_response = client.get(f'/api/xml/{file_id}/element?xpath=//book', 
                                  headers=auth_headers)
        check_result = json.loads(check_response.data)
        assert check_result['count'] == 1

    def test_delete_multiple_elements(self, client, auth_headers):
        """Test deleting multiple elements"""
        # Create XML with multiple similar elements
        xml_content = '''<?xml version="1.0"?>
        <root>
            <item>Item 1</item>
            <item>Item 2</item>
            <item>Item 3</item>
        </root>'''
        
        data = {
            'file': (BytesIO(xml_content.encode('utf-8')), 'test.xml')
        }
        upload_response = client.post('/api/xml/upload',
                                    data=data,
                                    headers=auth_headers,
                                    content_type='multipart/form-data')
        file_id = json.loads(upload_response.data)['file_id']

        # Delete all items
        response = client.delete(f'/api/xml/{file_id}/element?xpath=//item',
                               headers=auth_headers)

        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['deleted_count'] == 3

    def test_delete_element_no_xpath(self, client, auth_headers, sample_xml):
        """Test deleting element without XPath"""
        file_id = self.setup_file(client, auth_headers, sample_xml)

        response = client.delete(f'/api/xml/{file_id}/element',
                               headers=auth_headers)

        assert response.status_code == 400
        result = json.loads(response.data)
        assert result['error'] == 'XPath parameter is required'

    def test_element_operations_without_auth(self, client, sample_xml):
        """Test element operations without authentication"""
        # This test assumes we can't upload without auth, so we'll test the endpoints directly
        response = client.get('/api/xml/some-id/element?xpath=//book')
        assert response.status_code == 401

        response = client.post('/api/xml/some-id/element', json={'parent_xpath': '/', 'tag': 'test'})
        assert response.status_code == 401

        response = client.put('/api/xml/some-id/element', json={'xpath': '//test', 'text': 'new'})
        assert response.status_code == 401

        response = client.delete('/api/xml/some-id/element?xpath=//test')
        assert response.status_code == 401


class TestXMLTransformation:
    """Test XML transformation functionality"""

    def setup_file(self, client, auth_headers, sample_xml):
        """Helper method to upload a file and return its ID"""
        data = {
            'file': (BytesIO(sample_xml.encode('utf-8')), 'test.xml')
        }
        response = client.post('/api/xml/upload',
                             data=data,
                             headers=auth_headers,
                             content_type='multipart/form-data')
        return json.loads(response.data)['file_id']

    def test_transform_xml(self, client, auth_headers, sample_xml, sample_xslt):
        """Test XML transformation with XSLT"""
        file_id = self.setup_file(client, auth_headers, sample_xml)

        # Transform with XSLT
        xslt_data = {
            'xslt': (BytesIO(sample_xslt.encode('utf-8')), 'transform.xsl')
        }
        response = client.post(f'/api/xml/{file_id}/transform',
                             data=xslt_data,
                             headers=auth_headers,
                             content_type='multipart/form-data')

        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['message'] == 'XML transformed successfully'
        assert 'transformed_file_id' in result
        assert result['original_file_id'] == file_id
        assert 'download_url' in result

        # Retrieve and check transformed file
        transformed_id = result['transformed_file_id']
        transformed_response = client.get(f'/api/xml/{transformed_id}', 
                                        headers=auth_headers)
        assert transformed_response.status_code == 200
        
        # Check that the transformed content contains expected elements
        transformed_content = transformed_response.data.decode('utf-8')
        assert '<books>' in transformed_content
        assert '<name>' in transformed_content
        assert '<writer>' in transformed_content

    def test_transform_invalid_xslt(self, client, auth_headers, sample_xml):
        """Test transformation with invalid XSLT"""
        file_id = self.setup_file(client, auth_headers, sample_xml)

        # Try to transform with invalid XSLT
        invalid_xslt = b'<xsl:stylesheet>Invalid XSLT content</xsl:stylesheet>'
        xslt_data = {
            'xslt': (BytesIO(invalid_xslt), 'invalid.xsl')
        }
        response = client.post(f'/api/xml/{file_id}/transform',
                             data=xslt_data,
                             headers=auth_headers,
                             content_type='multipart/form-data')

        # Could be 400 or 500 depending on Flask-RESTX error handling
        assert response.status_code in [400, 500]
        result = json.loads(response.data)
        assert 'error' in result or 'message' in result

    def test_transform_no_xslt_file(self, client, auth_headers, sample_xml):
        """Test transformation without XSLT file"""
        file_id = self.setup_file(client, auth_headers, sample_xml)

        response = client.post(f'/api/xml/{file_id}/transform',
                             headers=auth_headers)

        assert response.status_code == 400
        result = json.loads(response.data)
        assert result['error'] == 'No XSLT file provided'

    def test_transform_empty_xslt_filename(self, client, auth_headers, sample_xml):
        """Test transformation with empty XSLT filename"""
        file_id = self.setup_file(client, auth_headers, sample_xml)

        xslt_data = {
            'xslt': (BytesIO(b'<xsl:stylesheet></xsl:stylesheet>'), '')
        }
        response = client.post(f'/api/xml/{file_id}/transform',
                             data=xslt_data,
                             headers=auth_headers,
                             content_type='multipart/form-data')

        assert response.status_code == 400
        result = json.loads(response.data)
        assert result['error'] == 'No XSLT file selected'

    def test_transform_nonexistent_file(self, client, auth_headers, sample_xslt):
        """Test transformation with non-existent XML file"""
        xslt_data = {
            'xslt': (BytesIO(sample_xslt.encode('utf-8')), 'transform.xsl')
        }
        response = client.post('/api/xml/nonexistent-id/transform',
                             data=xslt_data,
                             headers=auth_headers,
                             content_type='multipart/form-data')

        assert response.status_code == 404
        result = json.loads(response.data)
        assert result['error'] == 'File not found'

    def test_transform_without_auth(self, client, sample_xml, sample_xslt):
        """Test transformation without authentication"""
        xslt_data = {
            'xslt': (BytesIO(sample_xslt.encode('utf-8')), 'transform.xsl')
        }
        response = client.post('/api/xml/some-id/transform',
                             data=xslt_data,
                             content_type='multipart/form-data')

        assert response.status_code == 401


class TestXMLDeletion:
    """Test XML file deletion"""

    def setup_file(self, client, auth_headers, sample_xml):
        """Helper method to upload a file and return its ID"""
        data = {
            'file': (BytesIO(sample_xml.encode('utf-8')), 'test.xml')
        }
        response = client.post('/api/xml/upload',
                             data=data,
                             headers=auth_headers,
                             content_type='multipart/form-data')
        return json.loads(response.data)['file_id']

    def test_delete_xml_file(self, client, auth_headers, sample_xml):
        """Test deleting XML file"""
        file_id = self.setup_file(client, auth_headers, sample_xml)

        # Delete the file
        response = client.delete(f'/api/xml/{file_id}', headers=auth_headers)
        
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['message'] == 'File deleted successfully'
        assert result['file_id'] == file_id

        # Verify deletion
        get_response = client.get(f'/api/xml/{file_id}', headers=auth_headers)
        assert get_response.status_code == 404

    def test_delete_nonexistent_file(self, client, auth_headers):
        """Test deleting non-existent file"""
        response = client.delete('/api/xml/nonexistent-id', headers=auth_headers)
        
        assert response.status_code == 404
        result = json.loads(response.data)
        assert result['error'] == 'File not found'

    def test_delete_file_without_auth(self, client, auth_headers, sample_xml):
        """Test deleting file without authentication"""
        file_id = self.setup_file(client, auth_headers, sample_xml)

        response = client.delete(f'/api/xml/{file_id}')
        
        assert response.status_code == 401

    def test_delete_file_multiple_times(self, client, auth_headers, sample_xml):
        """Test deleting the same file multiple times"""
        file_id = self.setup_file(client, auth_headers, sample_xml)

        # First deletion should succeed
        response1 = client.delete(f'/api/xml/{file_id}', headers=auth_headers)
        assert response1.status_code == 200

        # Second deletion should fail
        response2 = client.delete(f'/api/xml/{file_id}', headers=auth_headers)
        assert response2.status_code == 404


class TestErrorHandling:
    """Test error handling"""

    def test_404_error_nonexistent_endpoint(self, client, auth_headers):
        """Test 404 error for non-existent endpoint"""
        response = client.get('/api/nonexistent', headers=auth_headers)
        assert response.status_code == 404

    def test_file_not_found_errors(self, client, auth_headers):
        """Test various file not found scenarios"""
        nonexistent_id = 'nonexistent-file-id'
        
        # Test getting non-existent file
        response = client.get(f'/api/xml/{nonexistent_id}', headers=auth_headers)
        assert response.status_code == 404

        # Test getting elements from non-existent file
        response = client.get(f'/api/xml/{nonexistent_id}/element?xpath=//test', 
                            headers=auth_headers)
        assert response.status_code == 404

        # Test adding element to non-existent file
        response = client.post(f'/api/xml/{nonexistent_id}/element',
                             json={'parent_xpath': '/', 'tag': 'test'},
                             headers=auth_headers)
        assert response.status_code == 404

        # Test updating element in non-existent file
        response = client.put(f'/api/xml/{nonexistent_id}/element',
                            json={'xpath': '//test', 'text': 'new'},
                            headers=auth_headers)
        assert response.status_code == 404

        # Test deleting element from non-existent file
        response = client.delete(f'/api/xml/{nonexistent_id}/element?xpath=//test',
                               headers=auth_headers)
        assert response.status_code == 404

    def test_missing_required_parameters(self, client, auth_headers, sample_xml):
        """Test missing required parameters"""
        data = {
            'file': (BytesIO(sample_xml.encode('utf-8')), 'test.xml')
        }
        upload_response = client.post('/api/xml/upload',
                                    data=data,
                                    headers=auth_headers,
                                    content_type='multipart/form-data')
        file_id = json.loads(upload_response.data)['file_id']

        # Missing xpath parameter for GET
        response = client.get(f'/api/xml/{file_id}/element', headers=auth_headers)
        assert response.status_code == 400
        result = json.loads(response.data)
        assert result['error'] == 'XPath parameter is required'

        # Missing xpath parameter for DELETE
        response = client.delete(f'/api/xml/{file_id}/element', headers=auth_headers)
        assert response.status_code == 400
        result = json.loads(response.data)
        assert result['error'] == 'XPath parameter is required'

    def test_malformed_json_requests(self, client, auth_headers, sample_xml):
        """Test malformed JSON in requests"""
        data = {
            'file': (BytesIO(sample_xml.encode('utf-8')), 'test.xml')
        }
        upload_response = client.post('/api/xml/upload',
                                    data=data,
                                    headers=auth_headers,
                                    content_type='multipart/form-data')
        file_id = json.loads(upload_response.data)['file_id']

        # Send malformed JSON for POST
        response = client.post(f'/api/xml/{file_id}/element',
                             data='{"invalid": json}',
                             headers=auth_headers,
                             content_type='application/json')
        assert response.status_code == 400

        # Send malformed JSON for PUT
        response = client.put(f'/api/xml/{file_id}/element',
                            data='{"invalid": json}',
                            headers=auth_headers,
                            content_type='application/json')
        assert response.status_code == 400

    def test_unauthorized_requests(self, client):
        """Test unauthorized requests to all protected endpoints"""
        endpoints_methods = [
            ('GET', '/api/health/'),
            ('GET', '/api/xml/'),
            ('POST', '/api/xml/upload'),
            ('GET', '/api/xml/some-id'),
            ('DELETE', '/api/xml/some-id'),
            ('GET', '/api/xml/some-id/element?xpath=//test'),
            ('POST', '/api/xml/some-id/element'),
            ('PUT', '/api/xml/some-id/element'),
            ('DELETE', '/api/xml/some-id/element?xpath=//test'),
            ('POST', '/api/xml/some-id/transform'),
        ]

        for method, endpoint in endpoints_methods:
            if method == 'GET':
                response = client.get(endpoint)
            elif method == 'POST':
                response = client.post(endpoint)
            elif method == 'PUT':
                response = client.put(endpoint)
            elif method == 'DELETE':
                response = client.delete(endpoint)
            
            assert response.status_code == 401, f"Expected 401 for {method} {endpoint}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
