import os
from lxml import etree
import json
from typing import Dict, List, Tuple, Optional, Any


class XMLUtils:
    """Utility class for XML operations"""

    @staticmethod
    def validate_xml_string(xml_string: str) -> Tuple[bool, Optional[str]]:
        """
        Validate if a string is valid XML

        Args:
            xml_string: XML content as string

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            etree.fromstring(xml_string.encode('utf-8'))
            return True, None
        except etree.XMLSyntaxError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    @staticmethod
    def validate_xml_file(file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate if a file contains valid XML

        Args:
            file_path: Path to XML file

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            parser = etree.XMLParser()
            etree.parse(file_path, parser)
            return True, None
        except etree.XMLSyntaxError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    @staticmethod
    def xml_to_dict(element: etree.Element) -> Dict[str, Any]:
        """
        Convert XML element to dictionary

        Args:
            element: lxml Element object

        Returns:
            Dictionary representation of XML
        """
        result = {}

        # Add attributes
        if element.attrib:
            result['@attributes'] = dict(element.attrib)

        # Add text content
        if element.text and element.text.strip():
            if len(element) == 0:  # No children
                if element.attrib:
                    result['#text'] = element.text.strip()
                else:
                    return element.text.strip()
            else:
                result['#text'] = element.text.strip()

        # Add children
        children = {}
        for child in element:
            child_data = XMLUtils.xml_to_dict(child)
            if child.tag in children:
                # Multiple children with same tag
                if not isinstance(children[child.tag], list):
                    children[child.tag] = [children[child.tag]]
                children[child.tag].append(child_data)
            else:
                children[child.tag] = child_data

        if children:
            result.update(children)

        # If only attributes, return the result
        if not children and not (element.text and element.text.strip()):
            if element.attrib:
                return result
            else:
                return None

        return result

    @staticmethod
    def dict_to_xml(data: Dict[str, Any], root_tag: str = 'root') -> etree.Element:
        """
        Convert dictionary to XML element

        Args:
            data: Dictionary to convert
            root_tag: Tag name for root element

        Returns:
            lxml Element object
        """
        def build_element(tag: str, value: Any) -> etree.Element:
            elem = etree.Element(tag)

            if isinstance(value, dict):
                # Handle attributes
                if '@attributes' in value:
                    for attr_key, attr_val in value['@attributes'].items():
                        elem.set(attr_key, str(attr_val))

                # Handle text content
                if '#text' in value:
                    elem.text = str(value['#text'])

                # Handle children
                for key, val in value.items():
                    if key not in ['@attributes', '#text']:
                        if isinstance(val, list):
                            for item in val:
                                child = build_element(key, item)
                                elem.append(child)
                        else:
                            child = build_element(key, val)
                            elem.append(child)

            elif isinstance(value, list):
                # This shouldn't happen at top level
                pass

            else:
                # Simple text content
                elem.text = str(value)

            return elem

        return build_element(root_tag, data)

    @staticmethod
    def pretty_print_xml(element: etree.Element) -> str:
        """
        Pretty print XML element

        Args:
            element: lxml Element object

        Returns:
            Pretty printed XML string
        """
        result = etree.tostring(
            element,
            encoding='unicode',
            pretty_print=True
        )
        # Add XML declaration manually
        return '<?xml version="1.0" encoding="UTF-8"?>\n' + result

    @staticmethod
    def merge_xml_elements(base: etree.Element, update: etree.Element) -> etree.Element:
        """
        Merge two XML elements

        Args:
            base: Base XML element
            update: XML element with updates

        Returns:
            Merged XML element
        """
        # Update attributes
        base.attrib.update(update.attrib)

        # Update text if present
        if update.text and update.text.strip():
            base.text = update.text

        # Merge children
        base_children = {child.tag: child for child in base}

        for update_child in update:
            if update_child.tag in base_children:
                # Recursively merge
                XMLUtils.merge_xml_elements(
                    base_children[update_child.tag],
                    update_child
                )
            else:
                # Add new child
                base.append(update_child)

        return base

    @staticmethod
    def find_elements_by_content(
        root: etree.Element,
        tag: Optional[str] = None,
        text: Optional[str] = None,
        attributes: Optional[Dict[str, str]] = None
    ) -> List[etree.Element]:
        """
        Find elements by tag, text content, and/or attributes

        Args:
            root: Root element to search in
            tag: Tag name to match (optional)
            text: Text content to match (optional)
            attributes: Attributes to match (optional)

        Returns:
            List of matching elements
        """
        results = []

        # Build XPath query
        if tag:
            xpath = f".//{tag}"
        else:
            xpath = ".//*"

        # Add text condition
        if text:
            xpath += f"[contains(text(), '{text}')]"

        # Add attribute conditions
        if attributes:
            for key, value in attributes.items():
                xpath += f"[@{key}='{value}']"

        try:
            results = root.xpath(xpath)
        except Exception:
            # Fallback to manual search if XPath fails
            for elem in root.iter():
                match = True

                if tag and elem.tag != tag:
                    match = False

                if match and text and (not elem.text or text not in elem.text):
                    match = False

                if match and attributes:
                    for key, value in attributes.items():
                        if elem.get(key) != value:
                            match = False
                            break

                if match:
                    results.append(elem)

        return results

    @staticmethod
    def get_element_path(element: etree.Element) -> str:
        """
        Get the full path of an element

        Args:
            element: lxml Element object

        Returns:
            Path string like /root/parent/child
        """
        path_parts = []
        current = element

        while current is not None:
            if current.tag is not None:
                # Count siblings with same tag
                parent = current.getparent()
                if parent is not None:
                    siblings = [e for e in parent if e.tag == current.tag]
                    if len(siblings) > 1:
                        index = siblings.index(current) + 1
                        path_parts.append(f"{current.tag}[{index}]")
                    else:
                        path_parts.append(current.tag)
                else:
                    path_parts.append(current.tag)

            current = current.getparent()

        path_parts.reverse()
        return "/" + "/".join(path_parts)

    @staticmethod
    def validate_xpath(xpath: str) -> Tuple[bool, Optional[str]]:
        """
        Validate if an XPath expression is valid

        Args:
            xpath: XPath expression to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            etree.XPath(xpath)
            return True, None
        except etree.XPathSyntaxError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    @staticmethod
    def compare_xml_elements(elem1: etree.Element, elem2: etree.Element) -> bool:
        """
        Compare two XML elements for equality

        Args:
            elem1: First element
            elem2: Second element

        Returns:
            True if elements are equal, False otherwise
        """
        # Compare tags
        if elem1.tag != elem2.tag:
            return False

        # Compare text
        text1 = (elem1.text or "").strip()
        text2 = (elem2.text or "").strip()
        if text1 != text2:
            return False

        # Compare attributes
        if elem1.attrib != elem2.attrib:
            return False

        # Compare children
        children1 = list(elem1)
        children2 = list(elem2)

        if len(children1) != len(children2):
            return False

        for child1, child2 in zip(children1, children2):
            if not XMLUtils.compare_xml_elements(child1, child2):
                return False

        return True
