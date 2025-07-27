from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
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

# Ensure upload directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['XSLT_FOLDER'], exist_ok=True)

# In-memory storage for XML files (in production, use a database)
xml_storage = {}


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


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'XML RESTful API',
        'version': '1.0.0'
    }), 200


@app.route('/api/xml/upload', methods=['POST'])
def upload_xml():
    """Upload XML file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not file.filename.endswith('.xml'):
        return jsonify({'error': 'File must be XML format'}), 400

    try:
        # Read and validate XML content
        xml_content = file.read()
        is_valid, error = XMLProcessor.validate_xml(xml_content)

        if not is_valid:
            return jsonify({'error': f'Invalid XML: {error}'}), 400

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

        return jsonify({
            'message': 'XML file uploaded successfully',
            'file_id': file_id,
            'filename': file.filename
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/xml/<file_id>', methods=['GET'])
def get_xml(file_id):
    """Retrieve XML file"""
    if file_id not in xml_storage:
        return jsonify({'error': 'File not found'}), 404

    try:
        filepath = xml_storage[file_id]['filepath']
        return send_file(filepath, mimetype='application/xml', as_attachment=True,
                        download_name=xml_storage[file_id]['original_filename'])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/xml/<file_id>/element', methods=['GET'])
def get_xml_element(file_id):
    """Get XML element by XPath"""
    if file_id not in xml_storage:
        return jsonify({'error': 'File not found'}), 404

    xpath = request.args.get('xpath')
    if not xpath:
        return jsonify({'error': 'XPath parameter required'}), 400

    try:
        filepath = xml_storage[file_id]['filepath']
        tree, error = XMLProcessor.parse_xml_file(filepath)

        if error:
            return jsonify({'error': error}), 500

        elements, error = XMLProcessor.get_element_by_xpath(tree, xpath)
        if error:
            return jsonify({'error': error}), 400

        # Convert elements to string representation
        result = []
        for elem in elements:
            result.append({
                'tag': elem.tag,
                'text': elem.text,
                'attributes': dict(elem.attrib),
                'xml': etree.tostring(elem, encoding='unicode', pretty_print=True)
            })

        return jsonify({
            'file_id': file_id,
            'xpath': xpath,
            'count': len(result),
            'elements': result
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/xml/<file_id>/element', methods=['POST'])
def add_xml_element(file_id):
    """Add new element to XML"""
    if file_id not in xml_storage:
        return jsonify({'error': 'File not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON data required'}), 400

    required_fields = ['parent_xpath', 'tag']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400

    try:
        filepath = xml_storage[file_id]['filepath']
        tree, error = XMLProcessor.parse_xml_file(filepath)

        if error:
            return jsonify({'error': error}), 500

        # Find parent element
        parents, error = XMLProcessor.get_element_by_xpath(tree, data['parent_xpath'])
        if error or not parents:
            return jsonify({'error': 'Parent element not found'}), 404

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

        return jsonify({
            'message': 'Element added successfully',
            'file_id': file_id,
            'element': {
                'tag': new_elem.tag,
                'text': new_elem.text,
                'attributes': dict(new_elem.attrib)
            }
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/xml/<file_id>/element', methods=['PUT'])
def update_xml_element(file_id):
    """Update XML element"""
    if file_id not in xml_storage:
        return jsonify({'error': 'File not found'}), 404

    data = request.get_json()
    if not data or 'xpath' not in data:
        return jsonify({'error': 'XPath required'}), 400

    try:
        filepath = xml_storage[file_id]['filepath']
        tree, error = XMLProcessor.parse_xml_file(filepath)

        if error:
            return jsonify({'error': error}), 500

        # Find element to update
        elements, error = XMLProcessor.get_element_by_xpath(tree, data['xpath'])
        if error or not elements:
            return jsonify({'error': 'Element not found'}), 404

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

        return jsonify({
            'message': 'Element updated successfully',
            'file_id': file_id,
            'element': {
                'tag': element.tag,
                'text': element.text,
                'attributes': dict(element.attrib)
            }
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/xml/<file_id>/element', methods=['DELETE'])
def delete_xml_element(file_id):
    """Delete XML element"""
    if file_id not in xml_storage:
        return jsonify({'error': 'File not found'}), 404

    xpath = request.args.get('xpath')
    if not xpath:
        return jsonify({'error': 'XPath parameter required'}), 400

    try:
        filepath = xml_storage[file_id]['filepath']
        tree, error = XMLProcessor.parse_xml_file(filepath)

        if error:
            return jsonify({'error': error}), 500

        # Find elements to delete
        elements, error = XMLProcessor.get_element_by_xpath(tree, xpath)
        if error or not elements:
            return jsonify({'error': 'Element not found'}), 404

        count = 0
        for element in elements:
            parent = element.getparent()
            if parent is not None:
                parent.remove(element)
                count += 1

        # Save the modified tree
        tree.write(filepath, encoding='utf-8', xml_declaration=True, pretty_print=True)

        return jsonify({
            'message': 'Elements deleted successfully',
            'file_id': file_id,
            'deleted_count': count
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/xml/<file_id>/transform', methods=['POST'])
def transform_xml(file_id):
    """Transform XML using XSLT"""
    if file_id not in xml_storage:
        return jsonify({'error': 'File not found'}), 404

    if 'xslt' not in request.files:
        return jsonify({'error': 'XSLT file required'}), 400

    xslt_file = request.files['xslt']
    if not xslt_file.filename.endswith('.xsl') and not xslt_file.filename.endswith('.xslt'):
        return jsonify({'error': 'File must be XSL/XSLT format'}), 400

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
            return jsonify({'error': f'XML parsing error: {error}'}), 500

        # Transform XML
        result_tree, error = XMLProcessor.transform_xml(xml_tree, xslt_filepath)

        # Clean up XSLT file
        os.remove(xslt_filepath)

        if error:
            return jsonify({'error': f'Transformation error: {error}'}), 500

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

        return jsonify({
            'message': 'XML transformed successfully',
            'original_file_id': file_id,
            'transformed_file_id': result_id,
            'download_url': f'/api/xml/{result_id}'
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/xml/<file_id>', methods=['DELETE'])
def delete_xml_file(file_id):
    """Delete XML file"""
    if file_id not in xml_storage:
        return jsonify({'error': 'File not found'}), 404

    try:
        filepath = xml_storage[file_id]['filepath']
        if os.path.exists(filepath):
            os.remove(filepath)

        del xml_storage[file_id]

        return jsonify({
            'message': 'File deleted successfully',
            'file_id': file_id
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/xml', methods=['GET'])
def list_xml_files():
    """List all uploaded XML files"""
    files = []
    for file_id, metadata in xml_storage.items():
        files.append({
            'id': file_id,
            'filename': metadata['original_filename'],
            'uploaded_at': metadata['uploaded_at']
        })

    return jsonify({
        'count': len(files),
        'files': files
    }), 200


@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': 'File too large. Maximum size is 16MB'}), 413


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
