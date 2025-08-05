import pytest
import os
import sys
import tempfile
from lxml import etree

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from xml_utils import XMLUtils


class TestXMLValidation:
    """Test XML validation functions"""

    def test_validate_valid_xml_string(self):
        valid_xml = '<?xml version="1.0"?><root><child>text</child></root>'
        is_valid, error = XMLUtils.validate_xml_string(valid_xml)
        assert is_valid is True
        assert error is None

    def test_validate_invalid_xml_string(self):
        invalid_xml = '<root><child>text</root>'  # Missing closing tag
        is_valid, error = XMLUtils.validate_xml_string(invalid_xml)
        assert is_valid is False
        assert error is not None
        assert 'child' in error

    def test_validate_empty_xml_string(self):
        is_valid, error = XMLUtils.validate_xml_string('')
        assert is_valid is False
        assert error is not None

    def test_validate_xml_with_special_characters(self):
        xml_with_special = '<?xml version="1.0"?><root><text>Special chars: &lt;&gt;&amp;</text></root>'
        is_valid, error = XMLUtils.validate_xml_string(xml_with_special)
        assert is_valid is True
        assert error is None

    def test_validate_xml_file(self):
        """Test XML file validation"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write('<?xml version="1.0"?><root><child>text</child></root>')
            temp_path = f.name

        try:
            is_valid, error = XMLUtils.validate_xml_file(temp_path)
            assert is_valid is True
            assert error is None
        finally:
            os.unlink(temp_path)

    def test_validate_invalid_xml_file(self):
        """Test invalid XML file validation"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write('<root><child>text</root>')  # Missing closing tag
            temp_path = f.name

        try:
            is_valid, error = XMLUtils.validate_xml_file(temp_path)
            assert is_valid is False
            assert error is not None
        finally:
            os.unlink(temp_path)


class TestXMLToDictConversion:
    """Test XML to dictionary conversion"""

    def test_simple_xml_to_dict(self):
        xml_str = '<root><name>Test</name><value>123</value></root>'
        root = etree.fromstring(xml_str)
        result = XMLUtils.xml_to_dict(root)

        assert 'name' in result
        assert result['name'] == 'Test'
        assert 'value' in result
        assert result['value'] == '123'

    def test_xml_with_attributes_to_dict(self):
        xml_str = '<book id="1" genre="fiction"><title>Test Book</title></book>'
        root = etree.fromstring(xml_str)
        result = XMLUtils.xml_to_dict(root)

        assert '@attributes' in result
        assert result['@attributes']['id'] == '1'
        assert result['@attributes']['genre'] == 'fiction'
        assert result['title'] == 'Test Book'

    def test_xml_with_multiple_children_to_dict(self):
        xml_str = '''
        <library>
            <book>Book 1</book>
            <book>Book 2</book>
            <book>Book 3</book>
        </library>
        '''
        root = etree.fromstring(xml_str)
        result = XMLUtils.xml_to_dict(root)

        assert 'book' in result
        assert isinstance(result['book'], list)
        assert len(result['book']) == 3
        assert result['book'][0] == 'Book 1'

    def test_xml_with_mixed_content_to_dict(self):
        xml_str = '<root>Text before<child>Child text</child>Text after</root>'
        root = etree.fromstring(xml_str)
        result = XMLUtils.xml_to_dict(root)

        assert '#text' in result or 'child' in result
        assert result['child'] == 'Child text'

    def test_empty_element_to_dict(self):
        xml_str = '<root><empty/></root>'
        root = etree.fromstring(xml_str)
        result = XMLUtils.xml_to_dict(root)

        assert 'empty' in result
        assert result['empty'] is None

    def test_text_only_element_to_dict(self):
        xml_str = '<root>Simple text</root>'
        root = etree.fromstring(xml_str)
        result = XMLUtils.xml_to_dict(root)

        # Should return just the text when it's a simple text element
        assert result == 'Simple text'

    def test_element_with_attributes_and_text_to_dict(self):
        xml_str = '<item id="1">Text content</item>'
        root = etree.fromstring(xml_str)
        result = XMLUtils.xml_to_dict(root)

        assert '@attributes' in result
        assert result['@attributes']['id'] == '1'
        assert '#text' in result
        assert result['#text'] == 'Text content'


class TestDictToXMLConversion:
    """Test dictionary to XML conversion"""

    def test_simple_dict_to_xml(self):
        data = {
            'name': 'Test',
            'value': 123
        }
        root = XMLUtils.dict_to_xml(data, 'root')

        assert root.tag == 'root'
        assert root.find('name').text == 'Test'
        assert root.find('value').text == '123'

    def test_dict_with_attributes_to_xml(self):
        data = {
            '@attributes': {'id': '1', 'type': 'test'},
            'content': 'Test content'
        }
        root = XMLUtils.dict_to_xml(data, 'element')

        assert root.tag == 'element'
        assert root.get('id') == '1'
        assert root.get('type') == 'test'
        assert root.find('content').text == 'Test content'

    def test_nested_dict_to_xml(self):
        data = {
            'library': {
                'book': {
                    '@attributes': {'id': '1'},
                    'title': 'Test Book',
                    'author': 'Test Author'
                }
            }
        }
        root = XMLUtils.dict_to_xml(data, 'root')

        library = root.find('library')
        assert library is not None
        book = library.find('book')
        assert book is not None
        assert book.get('id') == '1'
        assert book.find('title').text == 'Test Book'

    def test_list_in_dict_to_xml(self):
        data = {
            'items': [
                {'name': 'Item 1'},
                {'name': 'Item 2'},
                {'name': 'Item 3'}
            ]
        }
        root = XMLUtils.dict_to_xml(data, 'root')

        items = root.findall('items')
        assert len(items) == 3
        assert items[0].find('name').text == 'Item 1'

    def test_dict_with_text_content_to_xml(self):
        data = {
            '@attributes': {'id': '1'},
            '#text': 'Text content',
            'child': 'Child content'
        }
        root = XMLUtils.dict_to_xml(data, 'element')

        assert root.tag == 'element'
        assert root.get('id') == '1'
        assert root.text == 'Text content'
        assert root.find('child').text == 'Child content'


class TestXMLPrettyPrint:
    """Test XML pretty printing"""

    def test_pretty_print_simple_xml(self):
        xml_str = '<root><child>text</child></root>'
        root = etree.fromstring(xml_str)
        pretty = XMLUtils.pretty_print_xml(root)

        assert '<?xml' in pretty
        assert 'root' in pretty
        assert 'child' in pretty
        assert '\n' in pretty  # Should have newlines for formatting

    def test_pretty_print_with_attributes(self):
        xml_str = '<root id="1"><child attr="value">text</child></root>'
        root = etree.fromstring(xml_str)
        pretty = XMLUtils.pretty_print_xml(root)

        assert '<?xml' in pretty
        assert 'id="1"' in pretty
        assert 'attr="value"' in pretty

    def test_pretty_print_empty_element(self):
        xml_str = '<root><empty/></root>'
        root = etree.fromstring(xml_str)
        pretty = XMLUtils.pretty_print_xml(root)

        assert '<?xml' in pretty
        assert '<empty' in pretty  # Could be <empty/> or <empty></empty>
        assert 'root' in pretty


class TestXMLMerge:
    """Test XML element merging"""

    def test_merge_simple_elements(self):
        base_xml = '<root><name>Original</name><value>100</value></root>'
        update_xml = '<root><name>Updated</name><new>Added</new></root>'

        base = etree.fromstring(base_xml)
        update = etree.fromstring(update_xml)

        result = XMLUtils.merge_xml_elements(base, update)

        assert result.find('name').text == 'Updated'
        assert result.find('value').text == '100'  # Should remain
        assert result.find('new').text == 'Added'  # Should be added

    def test_merge_with_attributes(self):
        base_xml = '<root id="1" type="original"><content>Test</content></root>'
        update_xml = '<root type="updated" new_attr="value"/>'

        base = etree.fromstring(base_xml)
        update = etree.fromstring(update_xml)

        result = XMLUtils.merge_xml_elements(base, update)

        assert result.get('id') == '1'  # Should remain
        assert result.get('type') == 'updated'  # Should be updated
        assert result.get('new_attr') == 'value'  # Should be added

    def test_merge_with_text_content(self):
        base_xml = '<root>Original text<child>Child content</child></root>'
        update_xml = '<root>Updated text</root>'

        base = etree.fromstring(base_xml)
        update = etree.fromstring(update_xml)

        result = XMLUtils.merge_xml_elements(base, update)

        assert result.text.strip() == 'Updated text'
        assert result.find('child').text == 'Child content'  # Should remain


class TestElementSearch:
    """Test element search functionality"""

    def test_find_elements_by_tag(self):
        xml_str = '''
        <root>
            <book>Book 1</book>
            <magazine>Magazine 1</magazine>
            <book>Book 2</book>
        </root>
        '''
        root = etree.fromstring(xml_str)

        books = XMLUtils.find_elements_by_content(root, tag='book')
        assert len(books) == 2
        assert books[0].text == 'Book 1'
        assert books[1].text == 'Book 2'

    def test_find_elements_by_text(self):
        xml_str = '''
        <root>
            <item>Contains search term</item>
            <item>Different text</item>
            <item>Also contains search word</item>
        </root>
        '''
        root = etree.fromstring(xml_str)

        elements = XMLUtils.find_elements_by_content(root, text='search')
        assert len(elements) == 2

    def test_find_elements_by_attributes(self):
        xml_str = '''
        <root>
            <item type="A" priority="high">Item 1</item>
            <item type="B" priority="low">Item 2</item>
            <item type="A" priority="low">Item 3</item>
        </root>
        '''
        root = etree.fromstring(xml_str)

        elements = XMLUtils.find_elements_by_content(
            root,
            attributes={'type': 'A'}
        )
        assert len(elements) == 2

        elements = XMLUtils.find_elements_by_content(
            root,
            attributes={'type': 'A', 'priority': 'low'}
        )
        assert len(elements) == 1
        assert elements[0].text == 'Item 3'

    def test_find_elements_combined_criteria(self):
        xml_str = '''
        <root>
            <book type="fiction">Fiction Book</book>
            <book type="science">Science Book</book>
            <magazine type="fiction">Fiction Magazine</magazine>
        </root>
        '''
        root = etree.fromstring(xml_str)

        elements = XMLUtils.find_elements_by_content(
            root,
            tag='book',
            attributes={'type': 'fiction'}
        )
        assert len(elements) == 1
        assert elements[0].text == 'Fiction Book'

    def test_find_elements_no_results(self):
        xml_str = '<root><item>Test</item></root>'
        root = etree.fromstring(xml_str)

        elements = XMLUtils.find_elements_by_content(root, tag='nonexistent')
        assert len(elements) == 0


class TestElementPath:
    """Test element path functionality"""

    def test_get_element_path_simple(self):
        xml_str = '<root><parent><child>text</child></parent></root>'
        root = etree.fromstring(xml_str)
        child = root.find('.//child')

        path = XMLUtils.get_element_path(child)
        assert path == '/root/parent/child'

    def test_get_element_path_with_siblings(self):
        xml_str = '''
        <root>
            <item>First</item>
            <item>Second</item>
            <item>Third</item>
        </root>
        '''
        root = etree.fromstring(xml_str)
        items = root.findall('item')

        path1 = XMLUtils.get_element_path(items[0])
        path2 = XMLUtils.get_element_path(items[1])
        path3 = XMLUtils.get_element_path(items[2])

        assert path1 == '/root/item[1]'
        assert path2 == '/root/item[2]'
        assert path3 == '/root/item[3]'

    def test_get_element_path_root(self):
        xml_str = '<root><child>text</child></root>'
        root = etree.fromstring(xml_str)

        path = XMLUtils.get_element_path(root)
        assert path == '/root'

    def test_get_element_path_nested_with_attributes(self):
        xml_str = '''
        <root>
            <section id="1">
                <item>Item 1</item>
                <item>Item 2</item>
            </section>
            <section id="2">
                <item>Item 3</item>
            </section>
        </root>
        '''
        root = etree.fromstring(xml_str)
        item = root.find('.//section[@id="2"]/item')

        path = XMLUtils.get_element_path(item)
        assert path == '/root/section[2]/item'


class TestXPathValidation:
    """Test XPath validation"""

    def test_validate_valid_xpath(self):
        valid_xpaths = [
            '//book',
            '/root/child',
            '//book[@id="1"]',
            '//book[position()=1]',
            '//book[contains(text(), "search")]',
            '//*[@attr]',
            '//parent/child[1]',
            '//text()',
            '//@id'
        ]

        for xpath in valid_xpaths:
            is_valid, error = XMLUtils.validate_xpath(xpath)
            assert is_valid is True, f"XPath '{xpath}' should be valid but got error: {error}"
            assert error is None

    def test_validate_invalid_xpath(self):
        invalid_xpaths = [
            '//book[',  # Unclosed bracket
            '//book[@]',  # Invalid attribute syntax
            '//book[position(]',  # Unclosed function
            '//book[@id=]',  # Incomplete attribute comparison
            '//book[text() contains "search"]',  # Wrong function syntax
        ]

        for xpath in invalid_xpaths:
            is_valid, error = XMLUtils.validate_xpath(xpath)
            assert is_valid is False, f"XPath '{xpath}' should be invalid"
            assert error is not None

    def test_validate_empty_xpath(self):
        is_valid, error = XMLUtils.validate_xpath('')
        assert is_valid is False
        assert error is not None


class TestElementComparison:
    """Test XML element comparison"""

    def test_compare_identical_elements(self):
        xml_str = '<book id="1"><title>Test</title><author>Author</author></book>'
        elem1 = etree.fromstring(xml_str)
        elem2 = etree.fromstring(xml_str)

        assert XMLUtils.compare_xml_elements(elem1, elem2) is True

    def test_compare_different_tags(self):
        elem1 = etree.fromstring('<book>Test</book>')
        elem2 = etree.fromstring('<magazine>Test</magazine>')

        assert XMLUtils.compare_xml_elements(elem1, elem2) is False

    def test_compare_different_text(self):
        elem1 = etree.fromstring('<book>Text 1</book>')
        elem2 = etree.fromstring('<book>Text 2</book>')

        assert XMLUtils.compare_xml_elements(elem1, elem2) is False

    def test_compare_different_attributes(self):
        elem1 = etree.fromstring('<book id="1">Test</book>')
        elem2 = etree.fromstring('<book id="2">Test</book>')

        assert XMLUtils.compare_xml_elements(elem1, elem2) is False

    def test_compare_different_children(self):
        elem1 = etree.fromstring('<book><title>Test</title></book>')
        elem2 = etree.fromstring('<book><title>Test</title><author>Author</author></book>')

        assert XMLUtils.compare_xml_elements(elem1, elem2) is False

    def test_compare_with_whitespace(self):
        elem1 = etree.fromstring('<book>  Test  </book>')
        elem2 = etree.fromstring('<book>Test</book>')

        # Should be equal after stripping whitespace
        assert XMLUtils.compare_xml_elements(elem1, elem2) is True

    def test_compare_empty_elements(self):
        elem1 = etree.fromstring('<empty/>')
        elem2 = etree.fromstring('<empty></empty>')

        assert XMLUtils.compare_xml_elements(elem1, elem2) is True

    def test_compare_elements_different_attribute_order(self):
        elem1 = etree.fromstring('<book id="1" type="fiction">Test</book>')
        elem2 = etree.fromstring('<book type="fiction" id="1">Test</book>')

        assert XMLUtils.compare_xml_elements(elem1, elem2) is True

    def test_compare_nested_elements(self):
        xml1 = '<root><book><title>Test</title><author>Author</author></book></root>'
        xml2 = '<root><book><title>Test</title><author>Author</author></book></root>'
        
        elem1 = etree.fromstring(xml1)
        elem2 = etree.fromstring(xml2)

        assert XMLUtils.compare_xml_elements(elem1, elem2) is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
