# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0


EXT_INPUT_NAME = "External Input"
EXT_OUTPUT_NAME = "External Output"


def _is_external_metanode(node: dict) -> bool:
    """ Return True if a node is an external metanode, False elsewhere.
    """
    return (node['type'] in [EXT_INPUT_NAME, EXT_OUTPUT_NAME])


def get_dataflow_ip_nodes(dataflow_json) -> list:
    """ Return a list of nodes which represent ip cores
    (i.e. filter out External Outputs and Inputs)
    """
    return [
        node for node in dataflow_json['graph']['nodes']
        if not _is_external_metanode(node)
    ]


def get_dataflow_metanodes(dataflow_json) -> list:
    """ Return a list of external metanodes (i.e. External Outputs and Inputs)
    """
    return [
        node for node in dataflow_json['graph']['nodes']
        if _is_external_metanode(node)
    ]


def _get_interfaces(nodes: list) -> dict:
    """ Return a dict of all the interfaces belonging to given nodes.
    The resulting dict consists of items
    { "iface_id": {"node_name": ..., "iface_name": ..., "iface_dir": ...} }
    """
    result = {}
    for node in nodes:
        for interface in node['interfaces']:
            result[interface['id']] = {
                "node_name": node['name'],
                "iface_name": interface['name'],
                "iface_dir": interface['direction']
            }
    return result


def get_dataflow_ips_interfaces(dataflow_json) -> dict:
    """ Return a dict of all the interfaces of all the nodes representing
    ip cores. The resulting dict consists of items
    { "iface_id": {"node_name": ..., "iface_name": ..., "iface_dir": ...} }
    """
    return _get_interfaces(get_dataflow_ip_nodes(dataflow_json))


def get_dataflow_ip_connections(dataflow_json) -> list:
    """ Return connections between two IP cores
    (e.g. filter out connections to external metanodes)
    """
    ifaces_ids = get_dataflow_ips_interfaces(dataflow_json).keys()
    return [
        conn for conn in dataflow_json['graph']['connections']
        if conn["from"] in ifaces_ids and conn["to"] in ifaces_ids
    ]


def get_dataflow_externals_interfaces(dataflow_json) -> dict:
    """ Return a dict of all the interfaces of all the external metanodes.
    The resulting dict consists of items
    { "iface_id": {"node_name": ..., "iface_name": ..., "iface_dir": ...} }
    """
    return _get_interfaces(get_dataflow_metanodes(dataflow_json))


def get_dataflow_external_connections(dataflow_json) -> list:
    """ Return connections from/to metanodes representing
    external inputs/outputs
    """
    ifaces_ids = get_dataflow_externals_interfaces(dataflow_json).keys()
    return [
        conn for conn in dataflow_json['graph']['connections']
        if conn["from"] in ifaces_ids or conn["to"] in ifaces_ids
    ]


def find_dataflow_interface_by_id(dataflow_json, iface_id: str) -> dict:
    """ Return a dict {"node_name": ..., "iface_name": ..., "iface_dir": ...}
    that corresponds to a given 'iface_id'
    """
    interfaces = _get_interfaces(dataflow_json['graph']['nodes'])
    if iface_id in interfaces.keys():
        return interfaces[iface_id]


def find_spec_interface_by_name(
        specification,
        node_type: str,
        iface_name: str) -> dict:
    """ Find `name` interface of `ip_type` IP core in `specification`
    """
    for node in specification['nodes']:
        if node['type'] != node_type:
            continue
        for interface in node['interfaces']:
            if interface['name'] == iface_name:
                return interface


def find_dataflow_node_type_by_name(dataflow_data, node_name: str) -> str:
    for node in dataflow_data['graph']['nodes']:
        if node['name'] == node_name:
            return node["type"]