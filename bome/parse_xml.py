import xml.etree.cElementTree as cET
from xml.etree.cElementTree import Element


def read_xml(in_path):
    """
        Read and parse xml file
        in_path: xml file path
        return: ElementTree
    """
    tree = cET.parse(in_path)
    return tree


def write_xml(tree, out_path):
    """
        Write xml file
        tree: xml tree
        out_path: the out path
    """
    tree.write(out_path, encoding="utf-8", xml_declaration=True)


def get_xml_root(tree):
    """
    Get the root path of the xml file
    :param tree: xml tree
    :return: the root path
    """
    return tree.getroot()


def if_match(node, kv_map):
    """
        Determine whether a node contains all attributes
        node: node in the xml tree
        kv_map: attr&value map
    """
    for key in kv_map:
        if node.get(key) != kv_map.get(key):
            return False
    return True


def find_first_node(tree, path):
    """
    Find the first node matching a path
    :param tree: xml file
    :param path: the node path
    :return: the target node path
    """
    return tree.find(path)


def find_nodes(tree, path):
    """
        Find all nodes matching a path
        tree: xml tree
        path: the node path
    """
    return tree.findall(path)


def find_nodes_recursive(tree, path):
    """
    Find all nodes recursively
    :param tree: xml tree
    :param path: the node path
    :return: the target node path
    """
    return tree.iter(path)


def get_node_by_keyvalue(nodelist, kv_map):
    """
        Locate the corresponding node according to the
        attr&value, and return the node
        nodelist: the node to search
        kv_map: attr&value map
    """
    result_nodes = []
    for node in nodelist:
        if if_match(node, kv_map):
            result_nodes.append(node)
    return result_nodes


def change_node_properties(nodelist, kv_map, is_delete=False):
    """
        Modify/add/delete attr&value of nodes
        nodelist: the node to search
        kv_map: attr&value map
    """
    for node in nodelist:
        for key in kv_map:
            if is_delete:
                if key in node.attrib:
                    del node.attrib[key]
            else:
                node.set(key, kv_map.get(key))


def change_node_text(nodelist, text, is_add=False, is_delete=False):
    """
        Modify/add/delete a node's text
        nodelist: the node to search
        text: the updated text
    """
    for node in nodelist:
        if is_add:
            node.text += text
        elif is_delete:
            node.text = ""
        else:
            node.text = text


def create_node(tag, property_map, content):
    """
        Create a new node
        tag: the node tag
        property_map: attr&value map
        content: the tag's content
        return: new node
    """
    element = Element(tag, property_map)
    element.text = content
    return element


def add_child_node(nodelist, element):
    """
        Add child nodes to a node
        nodelist: the node to search
        element: the child nodes
    """
    for node in nodelist:
        node.append(element)


def del_node_by_tagkeyvalue(nodelist, tag, kv_map):
    """
        Locate a node by attr&value and delete it
        nodelist: parent node list
        tag: child node tag
        kv_map: attr&value map
    """
    for parent_node in nodelist:
        children = parent_node.getchildren()
        for child in children:
            if child.tag == tag and if_match(child, kv_map):
                parent_node.remove(child)
