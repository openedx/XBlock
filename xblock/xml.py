"""
XML utilities for XBlock, including parsing and loading XML definitions.
"""
from lxml import etree


XML_PARSER = etree.XMLParser(dtd_validation=False, load_dtd=False, remove_blank_text=True, encoding='utf-8')


def name_to_pathname(name):
    """
    Convert a location name for use in a path: replace ':' with '/'.
    This allows users of the xml format to organize content into directories
    """
    return name.replace(':', '/')


def is_pointer_tag(xml_obj):
    """
    Check if xml_obj is a pointer tag: <blah url_name="something" />.
    No children, one attribute named url_name, no text.

    Special case for course roots: the pointer is
      <course url_name="something" org="myorg" course="course">

    xml_obj: an etree Element

    Returns a bool.
    """
    if xml_obj.tag != "course":
        expected_attr = {'url_name'}
    else:
        expected_attr = {'url_name', 'course', 'org'}

    actual_attr = set(xml_obj.attrib.keys())

    has_text = xml_obj.text is not None and len(xml_obj.text.strip()) > 0

    return len(xml_obj) == 0 and actual_attr == expected_attr and not has_text


def load_definition_xml(node, runtime, def_id):
    """
    Parses and loads an XML definition file based on a given node, runtime
    environment, and definition ID.

    Arguments:
    node: XML element containing attributes for definition loading.
    runtime: The runtime environment that provides resource access.
    def_id: Unique identifier for the definition being loaded.

    Returns:
    tuple: A tuple containing the loaded XML definition and the
    corresponding file path.
    """
    url_name = node.get('url_name')
    filepath = format_filepath(node.tag, name_to_pathname(url_name))
    definition_xml = load_file(filepath, runtime.resources_fs, def_id)
    return definition_xml, filepath


def format_filepath(category, name):
    """
    Construct a formatted filepath string based on the given category and name.
    """
    return f'{category}/{name}.xml'


def load_file(filepath, fs, def_id):  # pylint: disable=invalid-name
    """
    Open the specified file in fs, and call cls.file_to_xml on it,
    returning the lxml object.

    Add details and reraise on error.
    """
    try:
        with fs.open(filepath) as xml_file:
            return file_to_xml(xml_file)
    except Exception as err:
        # Add info about where we are, but keep the traceback
        raise Exception(f'Unable to load file contents at path {filepath} for item {def_id}: {err}') from err


def file_to_xml(file_object):
    """
    Used when this module wants to parse a file object to xml
    that will be converted to the definition.

    Returns an lxml Element
    """
    return etree.parse(file_object, parser=XML_PARSER).getroot()
