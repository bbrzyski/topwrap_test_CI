# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0

import pytest
import jsonschema
from yaml import load, Loader

from fpga_topwrap.yamls_to_kpm_spec_parser import ipcore_yamls_to_kpm_spec
from fpga_topwrap.kpm_topwrap_client import _ipcore_names_to_yamls_mapping


@pytest.fixture
def hdmi_ipcores_yamls() -> list:
    _hdmi_yamls_prefix = 'examples/hdmi/ipcores/'
    _axi_yamls_prefix = 'fpga_topwrap/ips/axi/'
    return [
        _hdmi_yamls_prefix + 'axi_dispctrl.yaml',
        _hdmi_yamls_prefix + 'clock_crossing.yaml',
        _hdmi_yamls_prefix + 'dma_axi_in_axis_out.yaml',
        _hdmi_yamls_prefix + 'hdmi_tx.yaml',
        _hdmi_yamls_prefix + 'litex_mmcm.yaml',
        _hdmi_yamls_prefix + 'proc_sys_reset.yaml',
        _hdmi_yamls_prefix + 'ps7.yaml',
        _axi_yamls_prefix + 'axi_axil_adapter.yaml',
        _axi_yamls_prefix + 'axi_interconnect.yaml',
        _axi_yamls_prefix + 'axi_protocol_converter.yaml',
        _axi_yamls_prefix + 'axis_dwidth_converter.yaml',
        _axi_yamls_prefix + 'axis_async_fifo.yaml',
    ]


@pytest.fixture
def hdmi_ipcores_names_to_yamls(hdmi_ipcores_yamls) -> dict:
    return _ipcore_names_to_yamls_mapping(hdmi_ipcores_yamls)


@pytest.fixture
def hdmi_design_yaml() -> dict:
    with open('examples/hdmi/project.yml', 'r') as yamlfile:
        design = load(yamlfile, Loader=Loader)
    return design


def test_hdmi_specification_generation(specification_schema, hdmi_ipcores_yamls):
    spec = ipcore_yamls_to_kpm_spec(hdmi_ipcores_yamls)
    assert len(spec['nodes']) == 14 # 12 IP cores + 2 External metanodes
    jsonschema.validate(spec, specification_schema)
