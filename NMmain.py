import NMdhcp, NMgithub, NMsnmp, NMtcpdump
import paramiko
import time
from typing import Optional
import asyncio

def get_ipv6_from_slaac_server(
    router_ip: str,
    username: str,
    password: str,
    target_interface: str
) -> Optional[str]:
    """Get IPv6 address from SLAAC server logs"""
    try:
        # Connect to R4 (SLAAC server)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(router_ip, username=username, password=password)
        
        # Check IPv6 neighbor table for R5's address
        stdin, stdout, stderr = ssh.exec_command('show ipv6 neighbors')
        neighbors = stdout.read().decode()
        print(neighbors)
        
        # Parse output to find R5's IPv6 address
        # This is a simplified implementation - you'll need to adjust based on actual output format
        for line in neighbors.split('\n'):
            if target_interface in line:
                # Extract IPv6 address - adjust parsing based on actual format
                parts = line.split()
                print("hi")
                if len(parts) >= 2:
                    return parts[0]  # Assuming IPv6 address is first field
                
        return None
        
    except Exception as e:
        print(f"Error getting IPv6 from SLAAC: {str(e)}")
        return None
        
async def main():

    R4_IP = "198.51.100.1"  # Example IP - adjust as needed
    R5_IP = None  # Will be discovered via SLAAC
    USERNAME = "admin"  # Adjust credentials as needed
    PASSWORD = "cisco"
    
    # Step 1: Get R5's IPv6 address from R4 (SLAAC server)
    print("Step 1: Getting R5's IPv6 address from SLAAC server...")
    R5_IPv6 = get_ipv6_from_slaac_server(R4_IP, USERNAME, PASSWORD, "Fa0/0")
    if not R5_IPv6:
        print("Failed to get R5's IPv6 address")
        return
    print(f"R5's IPv6 address: {R5_IPv6}")
    
    # Step 2: Configure DHCP on R5
    print("\nStep 2: Configuring DHCP on R5...")
    
    # MAC addresses for R2 and R3 (example format - adjust as needed)
    R2_MAC = "ca02.31b1.0000"
    R3_MAC = "ca03.31c0.0000"

    # Configure static DHCP for R2
    success, message = NMdhcp.configure_dhcp(
    	R4_IP,
        R2_MAC, 
        R5_IPv6,  # Using IPv6 address we discovered
        USERNAME, 
        PASSWORD,
        static=True
    )
    print(f"R2 DHCP configuration: {message}")
    
    # Configure static DHCP for R3
    success, message = NMdhcp.configure_dhcp(
    	R4_IP,
        R3_MAC,
        R5_IPv6,
        USERNAME,
        PASSWORD,
        static=True
    )
    print(f"R3 DHCP configuration: {message}")
    
    # Configure dynamic DHCP for R4
    success, message = NMdhcp.configure_dhcp(
    	R4_IP,
        "ca04.31cf.0000",  # R4's MAC
        R5_IPv6,
        USERNAME,
        PASSWORD,
        static=False
    )
    print(f"R4 DHCP configuration: {message}")
    
    # Step 3: Get interface information via SNMP
    print("\nStep 3: Fetching interface information via SNMP...")
    router_addresses, interface_status = await NMsnmp.get_router_info()
    print("\nRouter Information:")
    for router, info in router_addresses.items():
        print(f"\n{router}:")
        for interface, addresses in info['addresses'].items():
            status = interface_status[router].get(interface, "unknown")
            print(f"  Interface: {interface} (Status: {status})")
            print(f"    IPv4: {addresses['v4']}")
            print(f"    IPv6: {addresses['v6']}")
    
    # Step 4: Monitor R1's CPU for 2 minutes
    print("\nStep 4: Monitoring R1's CPU usage...")
    cpu_graph = await NMsnmp.monitor_cpu_usage("198.51.101.1", "public", duration=120, interval=5)
    print(f"CPU usage graph saved as: {cpu_graph}")


    # TODO: Set up github config
    # git config --global user.name "Your Name"
    # git config --global user.email "your.email@example.com"
    # Generate a PAT for this class
    # git config --global credential.helper store
    # Then the first time you push, enter your GitHub username and PAT as password
    # make sure you git init the directory first <---- might not need to do this, I think it is done in code

    # Step 5: Push changes to GitHub
    print("\nStep 5: Pushing changes to GitHub...")
    success = NMgithub.push_to_github(
        ".",  # Current directory
        "https://github.com/jsnapoli1/netmanlab5.git",  # Replace with actual repo URL
        commit_message="Network configuration update"
    )
    if success:
        print("Successfully pushed changes to GitHub")
    else:
        print("Failed to push changes to GitHub")

if __name__ == "__main__":
    asyncio.run(main())

