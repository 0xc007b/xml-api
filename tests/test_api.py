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
from xml_utils import XMLUtils


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


class TestHealthCheck:
    """Test health check endpoint"""

    def test_health_check(self, client):
        response = client.get('/api/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['service'] == 'XML RESTful API'
        assert 'version' in data


class TestXMLUpload:
    """Test XML upload functionality"""

    def test_upload_valid_xml(self, client, sample_xml):
        data = {
            'file': (BytesIO(sample_xml.encode('utf-8')), 'test.xml')
        }
        response = client.post('/api/xml/upload',
                             data=data,
                             content_type='multipart/form-data')

        assert response.status_code == 201
        result = json.loads(response.data)
        assert 'file_id' in result
        assert result['filename'] == 'test.xml'
        assert result['message'] == 'XML file uploaded successfully'

    def test_upload_invalid_xml(self, client):
        invalid_xml = b'<invalid><not_closed>'
        data = {
            'file': (BytesIO(invalid_xml), 'invalid.xml')
        }
        response = client.post('/api/xml/upload',
                             data=data,
                             content_type='multipart/form-data')

        assert response.status_code == 400
        result = json.loads(response.data)
        assert 'error' in result
        assert 'Invalid XML' in result['error']

    def test_upload_no_file(self, client):
        response = client.post('/api/xml/upload')
        assert response.status_code == 400
        result = json.loads(response.data)
        assert result['error'] == 'No file provided'

    def test_upload_non_xml_file(self, client):
        data = {
            'file': (BytesIO(b'Not XML content'), 'test.txt')
        }
        response = client.post('/api/xml/upload',
                             data=data,
                             content_type='multipart/form-data')

        assert response.status_code == 400
        result = json.loads(response.data)
        assert result['error'] == 'File must be XML format'


class TestXMLRetrieval:
    """Test XML retrieval functionality"""

    def test_get_xml_file(self, client, sample_xml):
        # First upload a file
        data = {
            'file': (BytesIO(sample_xml.encode('utf-8')), 'test.xml')
        }
        upload_response = client.post('/api/xml/upload',
                                    data=data,
                                    content_type='multipart/form-data')
        file_id = json.loads(upload_response.data)['file_id']

        # Now retrieve it
        response = client.get(f'/api/xml/{file_id}')
        assert response.status_code == 200
        assert response.content_type == 'application/xml'
        assert response.data.decode('utf-8').strip() == sample_xml.strip()

    def test_get_nonexistent_file(self, client):
        response = client.get('/api/xml/nonexistent-id')
        assert response.status_code == 404
        result = json.loads(response.data)
        assert result['error'] == 'File not found'

    def test_list_xml_files(self, client, sample_xml):
        # Upload two files
        for i in range(2):
            data = {
                'file': (BytesIO(sample_xml.encode('utf-8')), f'test{i}.xml')
            }
            client.post('/api/xml/upload',
                       data=data,
                       content_type='multipart/form-data')

        # List files
        response = client.get('/api/xml')
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['count'] == 2
        assert len(result['files']) == 2


class TestXMLElementOperations:
    """Test XML element CRUD operations"""

    def setup_file(self, client, sample_xml):
        """Helper method to upload a file and return its ID"""
        data = {
            'file': (BytesIO(sample_xml.encode('utf-8')), 'test.xml')
        }
        response = client.post('/api/xml/upload',
                             data=data,
                             content_type='multipart/form-data')
        return json.loads(response.data)['file_id']

    def test_get_element_by_xpath(self, client, sample_xml):
        file_id = self.setup_file(client, sample_xml)

        # Get book elements
        response = client.get(f'/api/xml/{file_id}/element?xpath=//book')
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['count'] == 2
        assert len(result['elements']) == 2
        assert result['elements'][0]['tag'] == 'book'

    def test_get_element_invalid_xpath(self, client, sample_xml):
        file_id = self.setup_file(client, sample_xml)

        response = client.get(f'/api/xml/{file_id}/element?xpath=//nonexistent')
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['count'] == 0

    def test_add_element(self, client, sample_xml):
        file_id = self.setup_file(client, sample_xml)

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
                             content_type='application/json')

        assert response.status_code == 201
        result = json.loads(response.data)
        assert result['element']['tag'] == 'book'
        assert result['element']['attributes']['id'] == '3'

        # Verify the element was added
        check_response = client.get(f'/api/xml/{file_id}/element?xpath=//book[@id="3"]')
        check_result = json.loads(check_response.data)
        assert check_result['count'] == 1

    def test_update_element(self, client, sample_xml):
        file_id = self.setup_file(client, sample_xml)

        # Update the first book's title
        update_data = {
            'xpath': '//book[@id="1"]/title',
            'text': 'The Great Gatsby (Updated)'
        }

        response = client.put(f'/api/xml/{file_id}/element',
                            json=update_data,
                            content_type='application/json')

        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['element']['text'] == 'The Great Gatsby (Updated)'

        # Verify the update
        check_response = client.get(f'/api/xml/{file_id}/element?xpath=//book[@id="1"]/title')
        check_result = json.loads(check_response.data)
        assert check_result['elements'][0]['text'] == 'The Great Gatsby (Updated)'

    def test_delete_element(self, client, sample_xml):
        file_id = self.setup_file(client, sample_xml)

        # Delete the second book
        response = client.delete(f'/api/xml/{file_id}/element?xpath=//book[@id="2"]')

        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['deleted_count'] == 1

        # Verify deletion
        check_response = client.get(f'/api/xml/{file_id}/element?xpath=//book')
        check_result = json.loads(check_response.data)
        assert check_result['count'] == 1


class TestXMLTransformation:
    """Test XML transformation functionality"""

    def test_transform_xml(self, client, sample_xml, sample_xslt):
        # First upload XML file
        xml_data = {
            'file': (BytesIO(sample_xml.encode('utf-8')), 'test.xml')
        }
        upload_response = client.post('/api/xml/upload',
                                    data=xml_data,
                                    content_type='multipart/form-data')
        file_id = json.loads(upload_response.data)['file_id']

        # Transform with XSLT
        xslt_data = {
            'xslt': (BytesIO(sample_xslt.encode('utf-8')), 'transform.xsl')
        }
        response = client.post(f'/api/xml/{file_id}/transform',
                             data=xslt_data,
                             content_type='multipart/form-data')

        assert response.status_code == 200
        result = json.loads(response.data)
        assert 'transformed_file_id' in result
        assert result['original_file_id'] == file_id

        # Retrieve and check transformed file
        transformed_id = result['transformed_file_id']
        transformed_response = client.get(f'/api/xml/{transformed_id}')
        assert transformed_response.status_code == 200

    def test_transform_invalid_xslt(self, client, sample_xml):
        # Upload XML file
        xml_data = {
            'file': (BytesIO(sample_xml.encode('utf-8')), 'test.xml')
        }
        upload_response = client.post('/api/xml/upload',
                                    data=xml_data,
                                    content_type='multipart/form-data')
        file_id = json.loads(upload_response.data)['file_id']

        # Try to transform with invalid XSLT
        invalid_xslt = b'<xsl:stylesheet>Invalid</xsl:stylesheet>'
        xslt_data = {
            'xslt': (BytesIO(invalid_xslt), 'invalid.xsl')
        }
        response = client.post(f'/api/xml/{file_id}/transform',
                             data=xslt_data,
                             content_type='multipart/form-data')

        assert response.status_code == 500
        result = json.loads(response.data)
        assert 'error' in result


class TestXMLDeletion:
    """Test XML file deletion"""

    def test_delete_xml_file(self, client, sample_xml):
        # Upload a file
        data = {
            'file': (BytesIO(sample_xml.encode('utf-8')), 'test.xml')
        }
        upload_response = client.post('/api/xml/upload',
                                    data=data,
                                    content_type='multipart/form-data')
        file_id = json.loads(upload_response.data)['file_id']

        # Delete the file
        response = client.delete(f'/api/xml/{file_id}')
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['message'] == 'File deleted successfully'

        # Verify deletion
        get_response = client.get(f'/api/xml/{file_id}')
        assert get_response.status_code == 404


class TestErrorHandling:
    """Test error handling"""

    def test_404_error(self, client):
        response = client.get('/api/nonexistent')
        assert response.status_code == 404
        result = json.loads(response.data)
        assert 'error' in result

    def test_missing_xpath_parameter(self, client, sample_xml):
        # Upload a file
        data = {
            'file': (BytesIO(sample_xml.encode('utf-8')), 'test.xml')
        }
        upload_response = client.post('/api/xml/upload',
                                    data=data,
                                    content_type='multipart/form-data')
        file_id = json.loads(upload_response.data)['file_id']

        # Try to get element without xpath
        response = client.get(f'/api/xml/{file_id}/element')
        assert response.status_code == 400
        result = json.loads(response.data)
        assert result['error'] == 'XPath parameter required'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
