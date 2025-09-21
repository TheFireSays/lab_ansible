#!/usr/bin/env python3
"""
Ansible host_vars generator for Multi-Building Campus Nexus EVPN Lab
Generates host_vars, group_vars, and inventory files for your topology:
- 4 Superspines (Route Reflectors only)
- 3 Buildings with 2 Spines + 2 Leafs each
- Selective VLAN stretching between buildings
"""

import os
import yaml
from pathlib import Path

# Device data from your CSV (update with actual management IPs if needed)
devices_data = [
    # Superspines (Route Reflectors only)
    {"hostname": "dub-ssp1", "loopback0": "10.10.10.1", "loopback1": "20.20.20.1", "mgmt": "1.1.1.1"},
    {"hostname": "dub-ssp2", "loopback0": "10.10.10.2", "loopback1": "20.20.20.2", "mgmt": "1.1.1.2"},
    {"hostname": "dub-ssp3", "loopback0": "10.10.10.3", "loopback1": "20.20.20.3", "mgmt": "1.1.1.3"},
    {"hostname": "dub-ssp4", "loopback0": "10.10.10.4", "loopback1": "20.20.20.4", "mgmt": "1.1.1.4"},
    
    # Building 1 (st1) - VLANs: 100, 200, 300
    {"hostname": "dub-st1-sp1", "loopback0": "10.10.10.5", "loopback1": "20.20.20.5", "mgmt": "1.1.1.5"},
    {"hostname": "dub-st1-sp2", "loopback0": "10.10.10.6", "loopback1": "20.20.20.6", "mgmt": "1.1.1.6"},
    {"hostname": "dub-st1-lf1", "loopback0": "10.10.10.11", "loopback1": "20.20.20.11", "mgmt": "1.1.1.11"},
    {"hostname": "dub-st1-lf2", "loopback0": "10.10.10.12", "loopback1": "20.20.20.12", "mgmt": "1.1.1.12"},
    
    # Building 2 (st2) - VLANs: 200, 300, 400
    {"hostname": "dub-st2-sp1", "loopback0": "10.10.10.7", "loopback1": "20.20.20.7", "mgmt": "1.1.1.7"},
    {"hostname": "dub-st2-sp2", "loopback0": "10.10.10.8", "loopback1": "20.20.20.8", "mgmt": "1.1.1.8"},
    {"hostname": "dub-st2-lf1", "loopback0": "10.10.10.13", "loopback1": "20.20.20.13", "mgmt": "1.1.1.13"},
    {"hostname": "dub-st2-lf2", "loopback0": "10.10.10.14", "loopback1": "20.20.20.14", "mgmt": "1.1.1.14"},
    
    # Building 3 (st3) - VLANs: 100, 300, 400
    {"hostname": "dub-st3-sp1", "loopback0": "10.10.10.9", "loopback1": "20.20.20.9", "mgmt": "1.1.1.9"},
    {"hostname": "dub-st3-sp2", "loopback0": "10.10.10.10", "loopback1": "20.20.20.10", "mgmt": "1.1.1.10"},
    {"hostname": "dub-st3-lf1", "loopback0": "10.10.10.15", "loopback1": "20.20.20.15", "mgmt": "1.1.1.15"},
    {"hostname": "dub-st3-lf2", "loopback0": "10.10.10.16", "loopback1": "20.20.20.16", "mgmt": "1.1.1.16"},
]

def determine_device_type(hostname):
    """Determine device type from hostname"""
    if "-ssp" in hostname:
        return "superspine"
    elif "-sp" in hostname and "-ssp" not in hostname:
        return "spine"
    elif "-lf" in hostname:
        return "leaf"
    else:
        return "unknown"

def extract_building(hostname):
    """Extract building/area from hostname (st1, st2, st3)"""
    if "-st1-" in hostname:
        return "st1"
    elif "-st2-" in hostname:
        return "st2"
    elif "-st3-" in hostname:
        return "st3"
    else:
        return None

def get_building_vlans(building):
    """Get VLAN list for each building based on your selective stretching design"""
    vlan_mapping = {
        "st1": [100, 200, 300],  # Building 1: VLANs 100↔st3, 200↔st2, 300↔all
        "st2": [200, 300, 400],  # Building 2: VLANs 200↔st1, 300↔all, 400↔st3  
        "st3": [100, 300, 400]   # Building 3: VLANs 100↔st1, 300↔all, 400↔st2
    }
    return vlan_mapping.get(building, [])

def generate_host_vars(device):
    """Generate host_vars dictionary for a device"""
    hostname = device["hostname"]
    device_type = determine_device_type(hostname)
    building = extract_building(hostname)
    
    # Base configuration for all devices
    host_vars = {
        "# Device identification": None,
        "hostname": hostname,
        "device_type": device_type,
        "router_id": device["loopback0"],
        
        "# Routing parameters": None,
        "ospf_process_id": 1,
        "ospf_area": "0.0.0.0",
        "bgp_asn": 65001
    }
    
    # Superspines: Route Reflectors only (no VTEP functionality)
    if device_type == "superspine":
        host_vars.update({
            "# BGP Route Reflector role": None,
            "bgp_role": "route_reflector",
            "route_reflector_cluster_id": "1.1.1.1",
            
            "# Loopback interfaces (RR only)": None,
            "loopback_interfaces": {
                "loopback0": {
                    "description": "Router-ID for OSPF and BGP Route Reflector",
                    "ip_address": f"{device['loopback0']}/32"
                }
            }
        })
    
    # Spines and Leafs: VTEP functionality + BGP clients
    else:
        host_vars.update({
            "# VTEP configuration": None,
            "vtep_ip": device["loopback1"],
            "bgp_role": "route_reflector_client",
            
            "# Loopback interfaces (VTEP enabled)": None,
            "loopback_interfaces": {
                "loopback0": {
                    "description": "Router-ID for OSPF and BGP",
                    "ip_address": f"{device['loopback0']}/32"
                },
                "loopback1": {
                    "description": "VTEP Loopback for VXLAN", 
                    "ip_address": f"{device['loopback1']}/32"
                }
            }
        })
    
    # Add building-specific configuration
    if building:
        building_vlans = get_building_vlans(building)
        host_vars.update({
            "# Building-specific configuration": None,
            "building": building,
            "vlans": building_vlans
        })
        
        # Add VNI mappings for VTEP devices only
        if device_type in ["spine", "leaf"] and building_vlans:
            host_vars.update({
                "# VLAN to VNI mappings": None,
                "vni_mappings": {
                    vlan: vlan + 10000 for vlan in building_vlans
                }
            })
    
    return host_vars

def create_host_vars_files(devices, output_dir="host_vars"):
    """Create individual host_vars files for each device"""
    
    # Create output directory
    Path(output_dir).mkdir(exist_ok=True)
    
    print(f"Creating host_vars files in {output_dir}/")
    
    # Generate files for each device
    for device in devices:
        hostname = device["hostname"]
        host_vars = generate_host_vars(device)
        
        # Write YAML file with proper formatting
        file_path = Path(output_dir) / f"{hostname}.yml"
        with open(file_path, 'w') as f:
            f.write("---\n")
            for key, value in host_vars.items():
                if value is None:
                    f.write(f"\n{key}\n")
                else:
                    yaml.dump({key: value}, f, default_flow_style=False, indent=2)
        
        print(f"  ✓ {hostname}.yml")

def create_group_vars():
    """Create group_vars/all.yml with global parameters"""
    
    Path("group_vars").mkdir(exist_ok=True)
    
    group_vars = {
        "# Global network parameters": None,
        "ospf_process_id": 1,
        "ospf_area": "0.0.0.0", 
        "bgp_asn": 65001,
        
        "# VXLAN global settings": None,
        "vxlan_udp_port": 4789,
        "multicast_group": "239.1.1.1",
        
        "# Global VLAN to VNI mappings": None,
        "global_vni_mappings": {
            100: 10100,  # VLAN 100 → VNI 10100 (st1↔st3)
            200: 10200,  # VLAN 200 → VNI 10200 (st1↔st2)
            300: 10300,  # VLAN 300 → VNI 10300 (st1↔st2↔st3)
            400: 10400   # VLAN 400 → VNI 10400 (st2↔st3)
        },
        
        "# Building VLAN assignments": None,
        "building_vlans": {
            "st1": [100, 200, 300],
            "st2": [200, 300, 400], 
            "st3": [100, 300, 400]
        },
        
        "# VLAN stretching design": None,
        "vlan_stretching": {
            100: ["st1", "st3"],
            200: ["st1", "st2"],
            300: ["st1", "st2", "st3"],
            400: ["st2", "st3"]
        },
        
        "# Route reflector settings": None,
        "route_reflector_cluster_id": "1.1.1.1",
        
        "# Ansible connection parameters": None,
        "ansible_user": "admin",
        "ansible_password": "Firelab33",
        "ansible_network_os": "cisco.nxos.nxos",
        "ansible_connection": "ansible.netcommon.network_cli",
        "ansible_ssh_common_args": "-o StrictHostKeyChecking=no"
    }
    
    file_path = Path("group_vars") / "all.yml"
    with open(file_path, 'w') as f:
        f.write("---\n")
        for key, value in group_vars.items():
            if value is None:
                f.write(f"\n{key}\n")
            else:
                yaml.dump({key: value}, f, default_flow_style=False, indent=2)
    
    print("✓ group_vars/all.yml")

def create_inventory_file(devices):
    """Create inventory.ini file with proper grouping"""
    
    # Categorize devices
    superspines = [d for d in devices if determine_device_type(d["hostname"]) == "superspine"]
    spines = [d for d in devices if determine_device_type(d["hostname"]) == "spine"]
    leafs = [d for d in devices if determine_device_type(d["hostname"]) == "leaf"]
    
    # Group by building
    buildings = {"st1": [], "st2": [], "st3": []}
    for device in devices:
        building = extract_building(device["hostname"])
        if building:
            buildings[building].append(device)
    
    inventory_content = """# Multi-Building Campus EVPN Lab Inventory
# 4 Superspines + 3 Buildings with selective VLAN stretching

[superspines]
"""
    
    for device in superspines:
        mgmt_ip = device.get('mgmt', 'ansible_host_not_set')
        inventory_content += f"{device['hostname']} ansible_host={mgmt_ip}\n"
    
    inventory_content += "\n[spines]\n"
    for device in spines:
        mgmt_ip = device.get('mgmt', 'ansible_host_not_set')
        inventory_content += f"{device['hostname']} ansible_host={mgmt_ip}\n"
    
    inventory_content += "\n[leafs]\n"
    for device in leafs:
        mgmt_ip = device.get('mgmt', 'ansible_host_not_set')
        inventory_content += f"{device['hostname']} ansible_host={mgmt_ip}\n"
    
    # Add building-specific groups
    for building, devices_in_building in buildings.items():
        if devices_in_building:
            inventory_content += f"\n[{building}]\n"
            for device in devices_in_building:
                mgmt_ip = device.get('mgmt', 'ansible_host_not_set')
                inventory_content += f"{device['hostname']} ansible_host={mgmt_ip}\n"
    
    inventory_content += """
# Hierarchical groups
[all:children]
superspines
spines
leafs

# Device type groups for targeted playbook runs
[route_reflectors:children]
superspines

[vtep_devices:children]
spines
leafs

# Building groups for VLAN-specific deployments
[building_st1:children]
st1

[building_st2:children]
st2

[building_st3:children]
st3
"""
    
    with open("inventory.ini", 'w') as f:
        f.write(inventory_content)
    
    print("✓ inventory.ini")

def create_readme():
    """Create README with usage instructions"""
    
    readme_content = """# Multi-Building Campus EVPN Lab
Generated Ansible files for your GNS3 lab topology.

## Topology Overview
- **4 Superspines**: Route Reflectors only (dub-ssp1-4)
- **3 Buildings**: Connected via dark fiber
  - Building st1: VLANs 100, 200, 300
  - Building st2: VLANs 200, 300, 400  
  - Building st3: VLANs 100, 300, 400

## VLAN Stretching Design
- VLAN 100: st1 ↔ st3
- VLAN 200: st1 ↔ st2
- VLAN 300: st1 ↔ st2 ↔ st3 (global)
- VLAN 400: st2 ↔ st3

## Usage Examples

### Test connectivity
```bash
ansible all -i inventory.ini -m ping
```

### Configure loopbacks (underlay foundation)
```bash
ansible-playbook -i inventory.ini loopback_config.yml -v
```

### Deploy BGP EVPN (overlay)
```bash
ansible-playbook -i inventory.ini bgp_evpn_config.yml -v
```

### Target specific device types
```bash
ansible-playbook -i inventory.ini playbook.yml --limit superspines
ansible-playbook -i inventory.ini playbook.yml --limit building_st1
ansible-playbook -i inventory.ini playbook.yml --limit vtep_devices
```

### Dry run (check mode)
```bash
ansible-playbook -i inventory.ini playbook.yml --check
```

## File Structure
```
├── host_vars/          # Individual device variables
│   ├── dub-ssp1.yml
│   ├── dub-st1-sp1.yml
│   └── ...
├── group_vars/         # Global variables
│   └── all.yml
├── inventory.ini       # Device inventory
└── README.md          # This file
```

## Next Steps
1. Update management IP addresses in inventory.ini if needed
2. Test basic connectivity with ping module
3. Deploy underlay configuration (OSPF + loopbacks)
4. Deploy overlay configuration (BGP EVPN)
5. Add access layer configuration per building
"""
    
    with open("README.md", 'w') as f:
        f.write(readme_content)
    
    print("✓ README.md")

def main():
    """Main function to generate all Ansible files"""
    
    print("╔═══════════════════════════════════════════════════════╗")
    print("║        Multi-Building Campus EVPN Lab Generator       ║")
    print("║            Ansible Files for GNS3 Topology           ║")
    print("╚═══════════════════════════════════════════════════════╝")
    print()
    
    print(f"Processing {len(devices_data)} devices...")
    
    # Device breakdown
    device_counts = {
        "superspine": len([d for d in devices_data if determine_device_type(d["hostname"]) == "superspine"]),
        "spine": len([d for d in devices_data if determine_device_type(d["hostname"]) == "spine"]),
        "leaf": len([d for d in devices_data if determine_device_type(d["hostname"]) == "leaf"])
    }
    
    print(f"  → {device_counts['superspine']} Superspines (Route Reflectors)")
    print(f"  → {device_counts['spine']} Spines (per building)")
    print(f"  → {device_counts['leaf']} Leafs (per building)")
    print()
    
    # Generate all files
    print("Generating files:")
    create_host_vars_files(devices_data)
    create_group_vars()
    create_inventory_file(devices_data)
    create_readme()
    
    print()
    print("╔═══════════════════════════════════════════════════════╗")
    print("║                  GENERATION COMPLETE                  ║")
    print("╚═══════════════════════════════════════════════════════╝")
    print()
    print("Files created:")
    print("  ✓ host_vars/*.yml (16 device files)")
    print("  ✓ group_vars/all.yml")
    print("  ✓ inventory.ini")
    print("  ✓ README.md")
    print()
    print("Next steps:")
    print("  1. Update management IPs in inventory.ini if needed")
    print("  2. Test: ansible all -i inventory.ini -m ping")
    print("  3. Deploy: ansible-playbook -i inventory.ini loopback_config.yml")

if __name__ == "__main__":
    main()
