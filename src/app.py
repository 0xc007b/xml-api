from flask import Flask, request, send_file, jsonify
from flask_restx import Api, Resource, fields, Namespace
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
import os
import uuid
from lxml import etree
import json
from datetime import timedelta

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": ["*"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Authorization", "Content-Type"]
    }
})

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'xml_files')
app.config['XSLT_FOLDER'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'xslt_files')
app.config['RESTX_MASK_SWAGGER'] = False

# JWT Configuration
app.config['JWT_SECRET_KEY'] = 'your-secret-key-change-in-production'  # Change this in production!
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

# Initialize JWT
jwt = JWTManager(app)

# Ensure upload directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['XSLT_FOLDER'], exist_ok=True)

# In-memory storage for XML files (in production, use a database)
xml_storage = {}

# Simple user storage (in production, use a proper database)
users = {
    'admin': {
        'password': generate_password_hash('Usage8-Unnamed5-Flatly9-Seducing0-Nuclear8'),  # Change this in production!
        'username': 'admin'
    }
}

# Initialize Flask-RESTX
api = Api(app,
    version='1.0.0',
    title='XML RESTful API',
    description='A comprehensive RESTful API for XML file manipulation with XSLT transformation capabilities',
    doc='/api/docs',
    prefix='/api',
    authorizations={
        'Bearer': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': 'Type in the value input box below: Bearer <JWT token>'
        }
    },
    security='Bearer'
)

# Create namespaces
auth_ns = Namespace('auth', description='Authentication operations')
health_ns = Namespace('health', description='Health check operations')
xml_ns = Namespace('xml', description='XML file operations')

# Add namespaces to API
api.add_namespace(auth_ns)
api.add_namespace(health_ns)
api.add_namespace(xml_ns)

# Models for Swagger documentation
login_model = api.model('Login', {
    'username': fields.String(required=True, description='Username'),
    'password': fields.String(required=True, description='Password')
})

token_response_model = api.model('TokenResponse', {
    'access_token': fields.String(required=True, description='JWT access token'),
    'expires_in': fields.Integer(required=True, description='Token expiration time in seconds')
})

health_model = api.model('Health', {
    'status': fields.String(required=True, description='Health status'),
    'service': fields.String(required=True, description='Service name'),
    'version': fields.String(required=True, description='API version')
})

error_model = api.model('Error', {
    'error': fields.String(required=True, description='Error message')
})

upload_response_model = api.model('UploadResponse', {
    'message': fields.String(required=True, description='Success message'),
    'file_id': fields.String(required=True, description='Unique file identifier'),
    'filename': fields.String(required=True, description='Original filename')
})

file_info_model = api.model('FileInfo', {
    'id': fields.String(required=True, description='File ID'),
    'filename': fields.String(required=True, description='Original filename'),
    'uploaded_at': fields.String(required=True, description='Upload timestamp')
})

files_list_model = api.model('FilesList', {
    'count': fields.Integer(required=True, description='Number of files'),
    'files': fields.List(fields.Nested(file_info_model))
})

element_model = api.model('Element', {
    'tag': fields.String(required=True, description='Element tag name'),
    'text': fields.String(description='Element text content'),
    'attributes': fields.Raw(description='Element attributes'),
    'xml': fields.String(description='Element XML representation')
})

elements_response_model = api.model('ElementsResponse', {
    'file_id': fields.String(required=True, description='File ID'),
    'xpath': fields.String(required=True, description='XPath query'),
    'count': fields.Integer(required=True, description='Number of elements found'),
    'elements': fields.List(fields.Nested(element_model))
})

add_element_request = api.model('AddElementRequest', {
    'parent_xpath': fields.String(required=True, description='XPath to parent element'),
    'tag': fields.String(required=True, description='Tag name for new element'),
    'text': fields.String(description='Text content of the element'),
    'attributes': fields.Raw(description='Attributes for the element')
})

update_element_request = api.model('UpdateElementRequest', {
    'xpath': fields.String(required=True, description='XPath to element to update'),
    'text': fields.String(description='New text content'),
    'attributes': fields.Raw(description='New or updated attributes'),
    'clear_attributes': fields.Boolean(description='Clear existing attributes before setting new ones')
})

element_response_model = api.model('ElementResponse', {
    'message': fields.String(required=True, description='Success message'),
    'file_id': fields.String(required=True, description='File ID'),
    'element': fields.Nested(element_model)
})

delete_response_model = api.model('DeleteResponse', {
    'message': fields.String(required=True, description='Success message'),
    'file_id': fields.String(required=True, description='File ID'),
    'deleted_count': fields.Integer(description='Number of elements deleted')
})

transform_response_model = api.model('TransformResponse', {
    'message': fields.String(required=True, description='Success message'),
    'original_file_id': fields.String(required=True, description='Original file ID'),
    'transformed_file_id': fields.String(required=True, description='Transformed file ID'),
    'download_url': fields.String(required=True, description='URL to download transformed file')
})

# File upload parsers
upload_parser = api.parser()
upload_parser.add_argument('file', location='files', type=FileStorage, required=True, help='XML file to upload')

transform_parser = api.parser()
transform_parser.add_argument('xslt', location='files', type=FileStorage, required=True, help='XSLT file for transformation')

# Query parsers
xpath_parser = api.parser()
xpath_parser.add_argument('xpath', type=str, required=True, help='XPath expression', location='args')


# Authentication endpoints
@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.expect(login_model)
    @auth_ns.marshal_with(token_response_model, code=200)
    @auth_ns.response(401, 'Invalid credentials', error_model)
    @auth_ns.response(400, 'Bad request', error_model)
    def post(self):
        """Authenticate user and return JWT token"""
        data = request.get_json()
        if not data:
            api.abort(400, error='Request body must be JSON')

        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            api.abort(400, error='Username and password are required')

        user = users.get(username)
        if user and check_password_hash(user['password'], password):
            access_token = create_access_token(identity=username)
            return {
                'access_token': access_token,
                'expires_in': 3600  # 1 hour in seconds
            }, 200
        else:
            api.abort(401, error='Invalid credentials')


class XMLProcessor:
    """Class to handle XML processing operations"""

    @staticmethod
    def validate_xml(file_path):
        """Validate XML file"""
        try:
            etree.parse(file_path)
            return True, "Valid XML"
        except etree.XMLSyntaxError as e:
            return False, str(e)

    @staticmethod
    def parse_xml_file(file_path):
        """Parse XML file and return root element"""
        try:
            tree = etree.parse(file_path)
            return tree, None
        except Exception as e:
            return None, str(e)

    @staticmethod
    def transform_xml(xml_file_path, xslt_file_path):
        """Transform XML using XSLT"""
        try:
            xml_doc = etree.parse(xml_file_path)
            xslt_doc = etree.parse(xslt_file_path)
            transform = etree.XSLT(xslt_doc)
            result = transform(xml_doc)
            return result, None
        except Exception as e:
            return None, str(e)

    @staticmethod
    def get_element_by_xpath(tree, xpath):
        """Get elements by XPath expression"""
        try:
            elements = tree.xpath(xpath)
            return elements, None
        except Exception as e:
            return None, str(e)


@health_ns.route('/')
class HealthCheck(Resource):
    @health_ns.marshal_with(health_model)
    @health_ns.response(200, 'Success')
    @jwt_required()
    def get(self):
        """Get API health status"""
        return {
            'status': 'healthy',
            'service': 'XML RESTful API',
            'version': '1.0.0'
        }, 200


@xml_ns.route('/upload')
class XMLUpload(Resource):
    @xml_ns.expect(upload_parser)
    @xml_ns.marshal_with(upload_response_model, code=201)
    @xml_ns.response(400, 'Bad Request', error_model)
    @xml_ns.response(413, 'File too large', error_model)
    @jwt_required()
    def post(self):
        """Upload XML file"""
        if 'file' not in request.files:
            api.abort(400, error='No file provided')

        file = request.files['file']
        if file.filename == '':
            api.abort(400, error='No file selected')

        if not file.filename.lower().endswith('.xml'):
            api.abort(400, error='Only XML files are allowed')

        try:
            # Generate unique file ID
            file_id = str(uuid.uuid4())
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}_{filename}")

            # Save file
            file.save(file_path)

            # Validate XML
            is_valid, message = XMLProcessor.validate_xml(file_path)
            if not is_valid:
                os.remove(file_path)
                api.abort(400, error=f'Invalid XML: {message}')

            # Store file info
            xml_storage[file_id] = {
                'filename': filename,
                'path': file_path,
                'uploaded_at': str(uuid.uuid4())
            }

            return {
                'message': 'File uploaded successfully',
                'file_id': file_id,
                'filename': filename
            }, 201

        except Exception as e:
            api.abort(500, error=str(e))


@xml_ns.route('/')
class XMLList(Resource):
    @xml_ns.marshal_with(files_list_model)
    @jwt_required()
    def get(self):
        """Get list of all uploaded XML files"""
        files = []
        for file_id, info in xml_storage.items():
            files.append({
                'id': file_id,
                'filename': info['filename'],
                'uploaded_at': info['uploaded_at']
            })

        return {
            'count': len(files),
            'files': files
        }, 200


@xml_ns.route('/<string:file_id>')
class XMLFile(Resource):
    @xml_ns.response(200, 'File content')
    @xml_ns.response(404, 'File not found', error_model)
    @jwt_required()
    def get(self, file_id):
        """Download XML file"""
        if file_id not in xml_storage:
            api.abort(404, error='File not found')

        file_info = xml_storage[file_id]
        return send_file(file_info['path'], as_attachment=True, download_name=file_info['filename'])

    @xml_ns.marshal_with(delete_response_model)
    @xml_ns.response(404, 'File not found', error_model)
    @jwt_required()
    def delete(self, file_id):
        """Delete XML file"""
        if file_id not in xml_storage:
            api.abort(404, error='File not found')

        try:
            file_info = xml_storage[file_id]
            if os.path.exists(file_info['path']):
                os.remove(file_info['path'])
            del xml_storage[file_id]

            return {
                'message': 'File deleted successfully',
                'file_id': file_id
            }, 200

        except Exception as e:
            api.abort(500, error=str(e))


@xml_ns.route('/<string:file_id>/element')
class XMLElement(Resource):
    @xml_ns.expect(xpath_parser)
    @xml_ns.marshal_with(elements_response_model)
    @xml_ns.response(404, 'File not found', error_model)
    @xml_ns.response(400, 'Invalid XPath', error_model)
    @jwt_required()
    def get(self, file_id):
        """Get XML elements by XPath"""
        if file_id not in xml_storage:
            api.abort(404, error='File not found')

        xpath = request.args.get('xpath')
        if not xpath:
            api.abort(400, error='XPath parameter is required')

        try:
            file_info = xml_storage[file_id]
            tree, error = XMLProcessor.parse_xml_file(file_info['path'])
            if error:
                api.abort(500, error=f'Error parsing XML: {error}')

            elements, error = XMLProcessor.get_element_by_xpath(tree, xpath)
            if error:
                api.abort(400, error=f'Invalid XPath: {error}')

            # Format elements for response
            formatted_elements = []
            for elem in elements:
                if hasattr(elem, 'tag'):  # It's an element
                    formatted_elements.append({
                        'tag': elem.tag,
                        'text': elem.text,
                        'attributes': dict(elem.attrib),
                        'xml': etree.tostring(elem, encoding='unicode', pretty_print=True)
                    })
                else:  # It's a text node or attribute
                    formatted_elements.append({
                        'tag': 'text',
                        'text': str(elem),
                        'attributes': {},
                        'xml': str(elem)
                    })

            return {
                'file_id': file_id,
                'xpath': xpath,
                'count': len(formatted_elements),
                'elements': formatted_elements
            }, 200

        except Exception as e:
            api.abort(500, error=str(e))

    @xml_ns.expect(add_element_request)
    @xml_ns.marshal_with(element_response_model, code=201)
    @xml_ns.response(404, 'File not found', error_model)
    @xml_ns.response(400, 'Bad Request', error_model)
    @jwt_required()
    def post(self, file_id):
        """Add new element to XML file"""
        if file_id not in xml_storage:
            api.abort(404, error='File not found')

        data = request.get_json()
        parent_xpath = data.get('parent_xpath')
        tag = data.get('tag')
        text = data.get('text', '')
        attributes = data.get('attributes', {})

        if not parent_xpath or not tag:
            api.abort(400, error='parent_xpath and tag are required')

        try:
            file_info = xml_storage[file_id]
            tree, error = XMLProcessor.parse_xml_file(file_info['path'])
            if error:
                api.abort(500, error=f'Error parsing XML: {error}')

            # Find parent element
            parents, error = XMLProcessor.get_element_by_xpath(tree, parent_xpath)
            if error:
                api.abort(400, error=f'Invalid parent XPath: {error}')
            if not parents:
                api.abort(400, error='Parent element not found')

            # Add new element to first parent found
            parent = parents[0]
            new_element = etree.SubElement(parent, tag)

            if text:
                new_element.text = text

            for attr_name, attr_value in attributes.items():
                new_element.set(attr_name, str(attr_value))

            # Save the modified XML
            tree.write(file_info['path'], encoding='utf-8', xml_declaration=True, pretty_print=True)

            return {
                'message': 'Element added successfully',
                'file_id': file_id,
                'element': {
                    'tag': new_element.tag,
                    'text': new_element.text,
                    'attributes': dict(new_element.attrib),
                    'xml': etree.tostring(new_element, encoding='unicode', pretty_print=True)
                }
            }, 201

        except Exception as e:
            api.abort(500, error=str(e))

    @xml_ns.expect(update_element_request)
    @xml_ns.marshal_with(element_response_model)
    @xml_ns.response(404, 'File not found', error_model)
    @xml_ns.response(400, 'Bad Request', error_model)
    @jwt_required()
    def put(self, file_id):
        """Update existing XML element"""
        if file_id not in xml_storage:
            api.abort(404, error='File not found')

        data = request.get_json()
        xpath = data.get('xpath')
        text = data.get('text')
        attributes = data.get('attributes', {})
        clear_attributes = data.get('clear_attributes', False)

        if not xpath:
            api.abort(400, error='xpath is required')

        try:
            file_info = xml_storage[file_id]
            tree, error = XMLProcessor.parse_xml_file(file_info['path'])
            if error:
                api.abort(500, error=f'Error parsing XML: {error}')

            # Find elements to update
            elements, error = XMLProcessor.get_element_by_xpath(tree, xpath)
            if error:
                api.abort(400, error=f'Invalid XPath: {error}')
            if not elements:
                api.abort(404, error='Element not found')

            # Update first element found
            element = elements[0]

            if text is not None:
                element.text = text

            if clear_attributes:
                element.clear()
                if text is not None:
                    element.text = text

            for attr_name, attr_value in attributes.items():
                element.set(attr_name, str(attr_value))

            # Save the modified XML
            tree.write(file_info['path'], encoding='utf-8', xml_declaration=True, pretty_print=True)

            return {
                'message': 'Element updated successfully',
                'file_id': file_id,
                'element': {
                    'tag': element.tag,
                    'text': element.text,
                    'attributes': dict(element.attrib),
                    'xml': etree.tostring(element, encoding='unicode', pretty_print=True)
                }
            }, 200

        except Exception as e:
            api.abort(500, error=str(e))

    @xml_ns.expect(xpath_parser)
    @xml_ns.marshal_with(delete_response_model)
    @xml_ns.response(404, 'File not found', error_model)
    @xml_ns.response(400, 'Invalid XPath', error_model)
    @jwt_required()
    def delete(self, file_id):
        """Delete XML elements by XPath"""
        if file_id not in xml_storage:
            api.abort(404, error='File not found')

        xpath = request.args.get('xpath')
        if not xpath:
            api.abort(400, error='XPath parameter is required')

        try:
            file_info = xml_storage[file_id]
            tree, error = XMLProcessor.parse_xml_file(file_info['path'])
            if error:
                api.abort(500, error=f'Error parsing XML: {error}')

            # Find elements to delete
            elements, error = XMLProcessor.get_element_by_xpath(tree, xpath)
            if error:
                api.abort(400, error=f'Invalid XPath: {error}')

            deleted_count = 0
            for element in elements:
                if hasattr(element, 'getparent'):
                    parent = element.getparent()
                    if parent is not None:
                        parent.remove(element)
                        deleted_count += 1

            # Save the modified XML
            tree.write(file_info['path'], encoding='utf-8', xml_declaration=True, pretty_print=True)

            return {
                'message': f'Deleted {deleted_count} elements',
                'file_id': file_id,
                'deleted_count': deleted_count
            }, 200

        except Exception as e:
            api.abort(500, error=str(e))


@xml_ns.route('/<string:file_id>/transform')
class XMLTransform(Resource):
    @xml_ns.expect(transform_parser)
    @xml_ns.marshal_with(transform_response_model)
    @xml_ns.response(404, 'File not found', error_model)
    @xml_ns.response(400, 'Bad Request', error_model)
    @jwt_required()
    def post(self, file_id):
        """Transform XML file using XSLT"""
        if file_id not in xml_storage:
            api.abort(404, error='File not found')

        if 'xslt' not in request.files:
            api.abort(400, error='No XSLT file provided')

        xslt_file = request.files['xslt']
        if xslt_file.filename == '':
            api.abort(400, error='No XSLT file selected')

        try:
            # Save XSLT file temporarily
            xslt_filename = secure_filename(xslt_file.filename)
            xslt_path = os.path.join(app.config['XSLT_FOLDER'], f"temp_{uuid.uuid4()}_{xslt_filename}")
            xslt_file.save(xslt_path)

            # Transform XML
            file_info = xml_storage[file_id]
            result, error = XMLProcessor.transform_xml(file_info['path'], xslt_path)

            # Clean up temporary XSLT file
            os.remove(xslt_path)

            if error:
                api.abort(400, error=f'Transformation error: {error}')

            # Save transformed result
            result_id = str(uuid.uuid4())
            result_filename = f"transformed_{file_info['filename']}"
            result_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{result_id}_{result_filename}")

            with open(result_path, 'w', encoding='utf-8') as f:
                f.write(str(result))

            # Store transformed file info
            xml_storage[result_id] = {
                'filename': result_filename,
                'path': result_path,
                'uploaded_at': str(uuid.uuid4())
            }

            return {
                'message': 'XML transformed successfully',
                'original_file_id': file_id,
                'transformed_file_id': result_id,
                'download_url': f'/api/xml/{result_id}'
            }, 200

        except Exception as e:
            api.abort(500, error=str(e))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
