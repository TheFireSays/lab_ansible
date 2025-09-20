# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an Ansible-based network automation lab for managing Cisco NX-OS and IOS network devices in a data center fabric topology. The lab simulates a spine-leaf architecture with superspines, spines, leafs, and management switches, designed for EVPN-VXLAN configuration and testing.

## Network Topology

- **Superspines**: 4 devices (dub-ssp1-4) - Top tier switches
- **Spines**: 6 devices across 3 tiers (dub-st1/st2/st3-sp1/sp2) - Aggregation layer
- **Leafs**: 6 devices across 3 tiers (dub-st1/st2/st3-lf1/lf2) - Access layer  
- **Management**: 3 management switches for out-of-band access

All data switches run NX-OS, management switches run IOS.

## Key Commands

### Install Dependencies
```bash
ansible-galaxy collection install -r requirements.yml
```

### Run Playbooks
```bash
# Generate config files from templates
ansible-playbook playbooks/template_to_config.yml

# Push configurations to devices
ansible-playbook playbooks/multi-config-push.yml

# Generate host variable files from inventory
ansible-playbook playbooks/gen_hostvars_files_from_inv.yml

# Create empty config file placeholders
ansible-playbook playbooks/gen_configs_from_inventory.yml

# Change hostnames on devices
ansible-playbook playbooks/change_hostname.yml
```

### Test Connectivity
```bash
# Ping all devices
ansible all -m ping

# Check specific group
ansible data_switches -m ping
ansible mgmt_switches -m ping
```

## Architecture & Structure

### Configuration Management Flow
1. **Host Variables** (`host_vars/`) - Device-specific parameters like port-channels, IPs, VLANs
2. **Group Variables** (`group_vars/`) - Common features and settings per device type
3. **Templates** (`templates/`) - Jinja2 templates for generating device configurations
4. **Generated Configs** (`configs/`) - Final configuration files ready for deployment

### Key Files
- `inventory` - Defines all network devices with groups and connection parameters
- `ansible.cfg` - Ansible configuration with timeouts, logging, and SSH settings
- `requirements.yml` - Required Ansible collections (cisco.nxos, cisco.ios, etc.)

### Template System
The main template `templates/data_switches_template.j2` generates NX-OS configurations by:
- Enabling required features from group_vars
- Creating port-channel interfaces with LACP
- Configuring IP addresses and MTU settings
- Setting up console and VTY line configurations

### Variable Structure
Host variables in `host_vars/` define:
- `portchannels[]` - Array of port-channel definitions with members, IPs, descriptions
- Device-specific features can override group defaults

## EVPN-VXLAN Notes
The `evpn_vxlan_notes.txt` file contains detailed implementation notes for:
- Part 1: Underlay & VXLAN (LAGs, OSPF, multicast, VXLAN configuration)
- Part 2: Overlay/BGP-EVPN control plane
- Part 3: Anycast gateways, L3 VNI, route redistribution

## Development Workflow
1. Modify host variables for device-specific changes
2. Update templates for configuration logic changes
3. Test with `template_to_config.yml` to generate configs
4. Validate generated configs before pushing with `multi-config-push.yml`
5. Check logs in `logs/ansible.log` for troubleshooting