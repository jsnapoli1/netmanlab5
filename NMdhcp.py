import paramiko
import ipaddress
import json
import os
from typing import Tuple, Dict
import datetime
import time

def load_used_ips(used_ips_file: str = "used_ips.json") -> Dict[str, str]:
    """Load the used IP addresses from file"""
    if os.path.exists(used_ips_file):
        with open(used_ips_file, 'r') as f:
            return json.load(f)
    return {}

def save_used_ips(used_ips: Dict[str, str], used_ips_file: str = "used_ips.json"):
    """Save the used IP addresses to file"""
    with open(used_ips_file, 'w') as f:
        json.dump(used_ips, f)

def find_available_ip(network: ipaddress.IPv4Network, used_ips: Dict[str, str]) -> str:
    """Find an available IP address in the network range"""
    used_ip_set = set(used_ips.values())
    for ip in network.hosts():
        if str(ip) not in used_ip_set:
            return str(ip)
    raise Exception("No available IP addresses in the network range")

def configure_dhcp(
    ssh_host: str,
    mac_address: str,
    ssh_host2: str,
    ssh_username: str,
    ssh_password: str,
    static: bool = False,
    dhcp_range: str = "198.51.200.0/24"
) -> Tuple[bool, str]:
    """
    Configure DHCP for a MAC address via SSH
    
    Args:
        mac_address: MAC address to assign IP to
        ssh_host: Router's IP address
        ssh_username: SSH username
        ssh_password: SSH password
        static: Whether to assign a static IP
        dhcp_range: DHCP IP range in CIDR notation
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    # Validate MAC address format
    #mac_address = mac_address.lower().replace(':', '').replace('-', '')
    #if len(mac_address) != 12 or not all(c in '0123456789abcdef' for c in mac_address):
    #    return False, "Invalid MAC address format"

    # Format MAC address consistently
    mac_formatted = ':'.join(mac_address[i:i+2] for i in range(0, 12, 2))

    try:
        network = ipaddress.ip_network(dhcp_range)
        used_ips = load_used_ips()

        # Create SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ssh_host, username=ssh_username, password=ssh_password)

        if static:
            # Check if MAC already has a static IP
            if mac_address in used_ips:
                assigned_ip = used_ips[mac_address]
            else:
                # Find and assign new IP
                assigned_ip = find_available_ip(network, used_ips)
                used_ips[mac_address] = assigned_ip
                save_used_ips(used_ips)

            # Configure static DHCP binding
            commands = [
                'configure terminal',
                f'ip dhcp pool static_{mac_address}',
                f'host {assigned_ip} 255.255.255.0',
                f'client-identifier {mac_formatted}',
                'default-router 198.51.200.1'
                'exit',
                'exit',
                'write memory'
            ]
        else:
            # Configure dynamic DHCP
            commands = [
                'configure terminal',
                'ip dhcp pool dynamic',
                f'network {network.network_address} {network.netmask}',
                'default-router 198.51.200.1'
                'exit',
                'exit',
                'write memory'
            ]
            
        ssh_client = ssh.invoke_shell()
        ssh_client.send("ssh username@{ssh_host2}\n")
        time.sleep(2)
        ssh_client.send("{ssh_password}\n")
        time.sleep(2)
        # Execute commands
        for cmd in commands:
            ssh_client.send(cmd)
            time.sleep(0.1)

        ssh.close()
        
        if static:
            return True, f"Static IP {assigned_ip} assigned to MAC {mac_formatted}"
        else:
            return True, f"Dynamic DHCP configured for MAC {mac_formatted}"

    except Exception as e:
        return False, f"Error: {str(e)}"

def fetch_dhcp_clients(
    ssh_host: str,
    ssh_username: str,
    ssh_password: str,
    output_file: str = "dhcp_clients.txt"
) -> Tuple[bool, str]:
    """
    Fetch all DHCPv4 clients from the router and save to a file
    
    Args:
        ssh_host: Router's IP address
        ssh_username: SSH username
        ssh_password: SSH password
        output_file: Path to output file
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        # Create SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ssh_host, username=ssh_username, password=ssh_password)

        # Execute show command to get DHCP bindings
        stdin, stdout, stderr = ssh.exec_command('show ip dhcp binding')
        output = stdout.read().decode()
        error = stderr.read().decode()

        if error:
            return False, f"Error fetching DHCP clients: {error}"

        # Parse and format the output
        formatted_output = f"DHCP Clients - Retrieved at {datetime.datetime.now()}\n"
        formatted_output += "=" * 50 + "\n\n"
        formatted_output += output

        # Save to file
        with open(output_file, 'w') as f:
            f.write(formatted_output)

        ssh.close()
        return True, f"DHCP clients saved to {output_file}"

    except Exception as e:
        return False, f"Error: {str(e)}"
