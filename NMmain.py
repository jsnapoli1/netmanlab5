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

