from flask import Flask, request, send_file
from flask_restx import Api, Resource, fields, Namespace
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
import os
import uuid
from lxml import etree
import json

app = Flask(__name__)
CORS(app)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'xml_files')
app.config['XSLT_FOLDER'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'xslt_files')
app.config['RESTX_MASK_SWAGGER'] = False

# Ensure upload directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['XSLT_FOLDER'], exist_ok=True)

# In-memory storage for XML files (in production, use a database)
xml_storage = {}

# Initialize Flask-RESTX
api = Api(app,
    version='1.0.0',
    title='XML RESTful API',
    description='A comprehensive RESTful API for XML file manipulation with XSLT transformation capabilities',
    doc='/api/docs',
    prefix='/api'
)

# Create namespaces
health_ns = Namespace('health', description='Health check operations')
xml_ns = Namespace('xml', description='XML file operations')

# Add namespaces to API
api.add_namespace(health_ns)
api.add_namespace(xml_ns)

# Models for Swagger documentation
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


class XMLProcessor:
    """Class to handle XML processing operations"""

    @staticmethod
    def validate_xml(xml_content):
        """Validate if the content is valid XML"""
        try:
            etree.fromstring(xml_content)
            return True, None
        except etree.XMLSyntaxError as e:
            return False, str(e)

    @staticmethod
    def parse_xml_file(filepath):
        """Parse XML file and return the tree"""
        try:
            parser = etree.XMLParser(remove_blank_text=True)
            tree = etree.parse(filepath, parser)
            return tree, None
        except Exception as e:
            return None, str(e)

    @staticmethod
    def transform_xml(xml_tree, xslt_filepath):
        """Transform XML using XSLT"""
        try:
            xslt_tree = etree.parse(xslt_filepath)
            transform = etree.XSLT(xslt_tree)
            result = transform(xml_tree)
            return result, None
        except Exception as e:
            return None, str(e)

    @staticmethod
    def get_element_by_xpath(xml_tree, xpath):
        """Get elements using XPath"""
        try:
            elements = xml_tree.xpath(xpath)
            return elements, None
        except Exception as e:
            return None, str(e)


@health_ns.route('')
class HealthCheck(Resource):
    @api.doc('health_check')
    @api.marshal_with(health_model)
    def get(self):
        """Check API health status"""
        return {
            'status': 'healthy',
            'service': 'XML RESTful API',
            'version': '1.0.0'
        }, 200


@xml_ns.route('/upload')
class XMLUpload(Resource):
    @api.doc('upload_xml')
    @api.expect(upload_parser)
    @api.marshal_with(upload_response_model, code=201)
    @api.response(400, 'Bad Request', error_model)
    @api.response(413, 'File too large')
    def post(self):
        """Upload an XML file"""
        args = upload_parser.parse_args()
        file = args['file']

        if not file:
            api.abort(400, error='No file provided')

        if file.filename == '':
            api.abort(400, error='No file selected')

        if not file.filename.endswith('.xml'):
            api.abort(400, error='File must be XML format')

        try:
            # Read and validate XML content
            xml_content = file.read()
            is_valid, error = XMLProcessor.validate_xml(xml_content)

            if not is_valid:
                api.abort(400, error=f'Invalid XML: {error}')

            # Generate unique ID and save file
            file_id = str(uuid.uuid4())
            filename = secure_filename(f"{file_id}.xml")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            with open(filepath, 'wb') as f:
                f.write(xml_content)

            # Store metadata
            xml_storage[file_id] = {
                'id': file_id,
                'original_filename': file.filename,
                'filepath': filepath,
                'uploaded_at': str(uuid.uuid1().time)
            }

            return {
                'message': 'XML file uploaded successfully',
                'file_id': file_id,
                'filename': file.filename
            }, 201

        except Exception as e:
            api.abort(500, error=str(e))


@xml_ns.route('')
class XMLList(Resource):
    @api.doc('list_xml_files')
    @api.marshal_with(files_list_model)
    def get(self):
        """List all uploaded XML files"""
        files = []
        for file_id, metadata in xml_storage.items():
            files.append({
                'id': file_id,
                'filename': metadata['original_filename'],
                'uploaded_at': metadata['uploaded_at']
            })

        return {
            'count': len(files),
            'files': files
        }, 200


@xml_ns.route('/<string:file_id>')
@api.param('file_id', 'The file identifier')
class XMLFile(Resource):
    @api.doc('get_xml_file')
    @api.produces(['application/xml'])
    @api.response(404, 'File not found', error_model)
    def get(self, file_id):
        """Download an XML file"""
        if file_id not in xml_storage:
            api.abort(404, error='File not found')

        try:
            filepath = xml_storage[file_id]['filepath']
            return send_file(filepath, mimetype='application/xml', as_attachment=True,
                           download_name=xml_storage[file_id]['original_filename'])
        except Exception as e:
            api.abort(500, error=str(e))

    @api.doc('delete_xml_file')
    @api.marshal_with(delete_response_model)
    @api.response(404, 'File not found', error_model)
    def delete(self, file_id):
        """Delete an XML file"""
        if file_id not in xml_storage:
            api.abort(404, error='File not found')

        try:
            filepath = xml_storage[file_id]['filepath']
            if os.path.exists(filepath):
                os.remove(filepath)

            del xml_storage[file_id]

            return {
                'message': 'File deleted successfully',
                'file_id': file_id
            }, 200

        except Exception as e:
            api.abort(500, error=str(e))


@xml_ns.route('/<string:file_id>/element')
@api.param('file_id', 'The file identifier')
class XMLElement(Resource):
    @api.doc('get_xml_elements')
    @api.expect(xpath_parser)
    @api.marshal_with(elements_response_model)
    @api.response(400, 'Bad Request', error_model)
    @api.response(404, 'File not found', error_model)
    def get(self, file_id):
        """Get XML elements by XPath"""
        if file_id not in xml_storage:
            api.abort(404, error='File not found')

        args = xpath_parser.parse_args()
        xpath = args.get('xpath')

        if not xpath:
            api.abort(400, error='XPath parameter required')

        try:
            filepath = xml_storage[file_id]['filepath']
            tree, error = XMLProcessor.parse_xml_file(filepath)

            if error:
                api.abort(500, error=error)

            elements, error = XMLProcessor.get_element_by_xpath(tree, xpath)
            if error:
                api.abort(400, error=error)

            # Convert elements to string representation
            result = []
            for elem in elements:
                result.append({
                    'tag': elem.tag,
                    'text': elem.text,
                    'attributes': dict(elem.attrib),
                    'xml': etree.tostring(elem, encoding='unicode', pretty_print=True)
                })

            return {
                'file_id': file_id,
                'xpath': xpath,
                'count': len(result),
                'elements': result
            }, 200

        except Exception as e:
            api.abort(500, error=str(e))

    @api.doc('add_xml_element')
    @api.expect(add_element_request)
    @api.marshal_with(element_response_model, code=201)
    @api.response(400, 'Bad Request', error_model)
    @api.response(404, 'File not found', error_model)
    def post(self, file_id):
        """Add a new element to XML file"""
        if file_id not in xml_storage:
            api.abort(404, error='File not found')

        data = request.get_json()
        if not data:
            api.abort(400, error='JSON data required')

        required_fields = ['parent_xpath', 'tag']
        for field in required_fields:
            if field not in data:
                api.abort(400, error=f'Missing required field: {field}')

        try:
            filepath = xml_storage[file_id]['filepath']
            tree, error = XMLProcessor.parse_xml_file(filepath)

            if error:
                api.abort(500, error=error)

            # Find parent element
            parents, error = XMLProcessor.get_element_by_xpath(tree, data['parent_xpath'])
            if error or not parents:
                api.abort(404, error='Parent element not found')

            parent = parents[0]

            # Create new element
            new_elem = etree.SubElement(parent, data['tag'])

            if 'text' in data:
                new_elem.text = data['text']

            if 'attributes' in data and isinstance(data['attributes'], dict):
                for key, value in data['attributes'].items():
                    new_elem.set(key, str(value))

            # Save the modified tree
            tree.write(filepath, encoding='utf-8', xml_declaration=True, pretty_print=True)

            return {
                'message': 'Element added successfully',
                'file_id': file_id,
                'element': {
                    'tag': new_elem.tag,
                    'text': new_elem.text,
                    'attributes': dict(new_elem.attrib)
                }
            }, 201

        except Exception as e:
            api.abort(500, error=str(e))

    @api.doc('update_xml_element')
    @api.expect(update_element_request)
    @api.marshal_with(element_response_model)
    @api.response(400, 'Bad Request', error_model)
    @api.response(404, 'Element not found', error_model)
    def put(self, file_id):
        """Update an XML element"""
        if file_id not in xml_storage:
            api.abort(404, error='File not found')

        data = request.get_json()
        if not data or 'xpath' not in data:
            api.abort(400, error='XPath required')

        try:
            filepath = xml_storage[file_id]['filepath']
            tree, error = XMLProcessor.parse_xml_file(filepath)

            if error:
                api.abort(500, error=error)

            # Find element to update
            elements, error = XMLProcessor.get_element_by_xpath(tree, data['xpath'])
            if error or not elements:
                api.abort(404, error='Element not found')

            element = elements[0]

            # Update element
            if 'text' in data:
                element.text = data['text']

            if 'attributes' in data and isinstance(data['attributes'], dict):
                # Clear existing attributes if requested
                if data.get('clear_attributes', False):
                    element.attrib.clear()

                # Set new attributes
                for key, value in data['attributes'].items():
                    element.set(key, str(value))

            # Save the modified tree
            tree.write(filepath, encoding='utf-8', xml_declaration=True, pretty_print=True)

            return {
                'message': 'Element updated successfully',
                'file_id': file_id,
                'element': {
                    'tag': element.tag,
                    'text': element.text,
                    'attributes': dict(element.attrib)
                }
            }, 200

        except Exception as e:
            api.abort(500, error=str(e))

    @api.doc('delete_xml_element')
    @api.expect(xpath_parser)
    @api.marshal_with(delete_response_model)
    @api.response(400, 'Bad Request', error_model)
    @api.response(404, 'Element not found', error_model)
    def delete(self, file_id):
        """Delete XML elements by XPath"""
        if file_id not in xml_storage:
            api.abort(404, error='File not found')

        args = xpath_parser.parse_args()
        xpath = args.get('xpath')

        if not xpath:
            api.abort(400, error='XPath parameter required')

        try:
            filepath = xml_storage[file_id]['filepath']
            tree, error = XMLProcessor.parse_xml_file(filepath)

            if error:
                api.abort(500, error=error)

            # Find elements to delete
            elements, error = XMLProcessor.get_element_by_xpath(tree, xpath)
            if error or not elements:
                api.abort(404, error='Element not found')

            count = 0
            for element in elements:
                parent = element.getparent()
                if parent is not None:
                    parent.remove(element)
                    count += 1

            # Save the modified tree
            tree.write(filepath, encoding='utf-8', xml_declaration=True, pretty_print=True)

            return {
                'message': 'Elements deleted successfully',
                'file_id': file_id,
                'deleted_count': count
            }, 200

        except Exception as e:
            api.abort(500, error=str(e))


@xml_ns.route('/<string:file_id>/transform')
@api.param('file_id', 'The file identifier')
class XMLTransform(Resource):
    @api.doc('transform_xml')
    @api.expect(transform_parser)
    @api.marshal_with(transform_response_model)
    @api.response(400, 'Bad Request', error_model)
    @api.response(404, 'File not found', error_model)
    def post(self, file_id):
        """Transform XML file using XSLT"""
        if file_id not in xml_storage:
            api.abort(404, error='File not found')

        args = transform_parser.parse_args()
        xslt_file = args['xslt']

        if not xslt_file:
            api.abort(400, error='XSLT file required')

        if not xslt_file.filename.endswith('.xsl') and not xslt_file.filename.endswith('.xslt'):
            api.abort(400, error='File must be XSL/XSLT format')

        try:
            # Save XSLT file temporarily
            xslt_id = str(uuid.uuid4())
            xslt_filename = secure_filename(f"{xslt_id}.xsl")
            xslt_filepath = os.path.join(app.config['XSLT_FOLDER'], xslt_filename)
            xslt_file.save(xslt_filepath)

            # Parse XML file
            xml_filepath = xml_storage[file_id]['filepath']
            xml_tree, error = XMLProcessor.parse_xml_file(xml_filepath)

            if error:
                os.remove(xslt_filepath)
                api.abort(500, error=f'XML parsing error: {error}')

            # Transform XML
            result_tree, error = XMLProcessor.transform_xml(xml_tree, xslt_filepath)

            # Clean up XSLT file
            os.remove(xslt_filepath)

            if error:
                api.abort(500, error=f'Transformation error: {error}')

            # Save transformed result
            result_id = str(uuid.uuid4())
            result_filename = f"{result_id}_transformed.xml"
            result_filepath = os.path.join(app.config['UPLOAD_FOLDER'], result_filename)

            result_tree.write(result_filepath, encoding='utf-8', xml_declaration=True, pretty_print=True)

            # Store metadata
            xml_storage[result_id] = {
                'id': result_id,
                'original_filename': f"transformed_{xml_storage[file_id]['original_filename']}",
                'filepath': result_filepath,
                'uploaded_at': str(uuid.uuid1().time),
                'transformed_from': file_id
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
