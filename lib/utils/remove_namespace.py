"""
This module contains a function that is used to remove the namespace tag
from all the document and the default namespace tag from the attrib of the element.
"""


def remove_namespace(doc, namespace):
    """
    remove the namespace in the passed document and namespace
    change the tag for element in place.
    remove the default namespace show up in the tag and id which
    shows up in the attrib of the element
    :param doc: lxml.etree.ElementTree
    :param namespace: str
    :return:
    """
    new_namespace = u'{%s}' % namespace
    new_namespace_length = len(new_namespace)
    default_namespace = '{http://www.w3.org/XML/1998/namespace}'
    default_namespace_length = len(default_namespace)
    for element in doc.getiterator():
        if element.tag.startswith(new_namespace):
            element.tag = element.tag[new_namespace_length:]
        for attribute in element.attrib:
            if attribute.startswith(default_namespace):
                element.attrib[attribute[default_namespace_length:]] = element.attrib.pop(attribute)
