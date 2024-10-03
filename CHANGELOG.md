# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Add support for IP cores from fusesoc in topwrap
    - Nox session for downloading and packaging fusesoc library

### Fixed

- Fix issue with YAML files produced with topwarp parse having unnecessary 2 hyphens for signals

## [0.1.0] - 2024-09-27

### Topwrap features

- Convert HDL sources into YAML IP core description files
    - Verilog and VHDL support
    - Ability to infer interfaces: AXI, AXI-Lite, AXI Stream, Wishbone
    - Simple YAML-based description for command-line use
- Assemble top-level design from IP cores
    - Support compliance checks for predefined interfaces
    - Generate a FuseSoC `.core` file
    - Use [Amaranth](https://github.com/amaranth-lang/amaranth) for final generation of top level
- Create and visualize designs in GUI
    - User-friendly GUI powered by [Kenning Pipeline Manager](https://github.com/antmicro/kenning-pipeline-manager)
    - Create designs by dragging cores and connecting them
    - Visualize hierarchical designs
    - Validate and build designs to get information about problems in design
    - Converter from yaml IP core/design to KPM specification/dataflow
- Added User Repository
    - Create custom libraries to reuse across projects
    - Directory for each core with it's HDL and parsed IP core
    - Support for multiple HDL sources per single repository entry
    - Directory for all the interface definitions
    - Simplify the CLI flow by automatically loading of IP core yamls from repository
- User friendly documentation
    - Documentation focuses on the gradual introduction to using topwrap
    - Examples have live preview to show how they look in GUI
    - Developers's guide part of documentation for more advanced concepts and future contributors
