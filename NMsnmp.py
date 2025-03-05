from pysnmp.hlapi.v3arch.asyncio import *
import json
import time
import matplotlib.pyplot as plt
from datetime import datetime
import asyncio

async def snmp_get(ip, version, community, oid):

    if version != 3:
        g = await get_cmd(
            SnmpEngine(),
            CommunityData(community, mpModel=version-1),
            await UdpTransportTarget.create((ip, 161)),
            ContextData(),
            ObjectType(ObjectIdentity(oid))
        )

    errorIndication, errorStatus, errorIndex, varBinds = g
    # Check for errors
    if errorIndication:
        return f"Error: {errorIndication}"
    elif errorStatus:
        return f"Error: {errorStatus.prettyPrint()} at {errorIndex}"
    else:
        # Extract the value from the response
        return varBinds[0][1]

async def get_interface_names(router, community):
    """Get interface names and their indices from a router"""
    interface_info = {}
    interface_names_oid = '1.3.6.1.2.1.2.2.1.2.'  # ifDescr
    
    for i in range(1,10):
    	oid_appended = interface_names_oid+str(i)
    	name = await snmp_get(router, version=2, community=community, oid=oid_appended)
    	if "Error" not in str(name):
       	    status = await get_interface_status(router, community, i)
       	    ipv4 = await get_ipv4_address(router, community, i)
       	    ipv6 = await get_ipv6_address(router,community,i)
       	    if "Error" not in str(status) and "Error" not in str(ipv4) and "Error" not in str(ipv6):
       	    	interface_info[i] = [str(name), str(status), str(ipv4), str(ipv6)]
       	    	
    return interface_info

async def get_interface_status(router, community, interface_index):
    """Get status for a specific interface"""
    interface_status_oid = '1.3.6.1.2.1.2.2.1.8.'  # ifOperStatus

    oid_appended = interface_status_oid+str(interface_index)
    status = await snmp_get(router,version=2,community=community,oid=oid_appended)

    return status

async def get_ipv4_address(router, community, i):
    """Get IPv4 addresses from a router"""
    ipv4_addresses_oid = '1.3.6.1.2.1.4.20.1.2'  # ipAdEntAddr
    
    objects = walk_cmd(SnmpEngine(), CommunityData(community), await UdpTransportTarget.create((router,161)), ContextData(), ObjectType(ObjectIdentity(ipv4_addresses_oid)), lexicographicMode=False)
    
    async for errorIndication, errorStatus, errorIndex, varBinds in objects:
    	for varBind in varBinds:
    	    if f"= {i}" in str(varBind):
    	        split_slot = str(varBind).split(" ")
    	        final_split = split_slot[0].split("mib-2.4.20.1.2.")
    	        return final_split[1]
    	    
    	    
    	    
async def get_ipv6_address(router, community, i):
    """Get IPv6 addresses from a router"""
    ipv6_addresses_oid = '1.3.6.1.2.1.55.1.8.1.2'  # ipv6AddrAddress
    
    objects = walk_cmd(SnmpEngine(), CommunityData(community), await UdpTransportTarget.create((router,161)), ContextData(), ObjectType(ObjectIdentity(ipv6_addresses_oid)), lexicographicMode=False)
    
    async for errorIndication, errorStatus, errorIndex, varBinds in objects:
    	for varBind in varBinds:
    	    print(varBind)
    	    if f"= {i}" in str(varBind):
    	        split_slot = str(varBind).split(" ")
    	        final_split = split_slot[0].split("mib-2.55.1.1.2.")
    	        return final_split[1]

async def get_router_info():
    # Dictionary to store router addresses
    router_addresses = {}
    # Dictionary to store interface status
    interface_status = {}
    
    # SNMP community string and target routers with their IPs
    community = 'public'


    # TODO: Legit fill this out

    router_ips = {
        'R1': '198.51.101.1',
        'R2': '192.168.2.2',
        'R3': '192.168.1.3',
        'R4': '198.51.100.1',
        'R5': '192.168.5.2'
    }
    
    for router_name, router_ip in router_ips.items():
        try:
            # Initialize nested dictionaries
            router_addresses[router_name] = {"addresses": {}}
            interface_status[router_name] = {}
            
            # Get interface names and their indices
            interfaces = await get_interface_names(router_ip, community)
            print(interfaces)
                
        except Exception as e:
            print(f"Error processing {router_name} ({router_ip}): {str(e)}")
            continue
    
    return router_addresses, interface_status

async def monitor_cpu_usage(router, community, duration=300, interval=5):
    """
    Monitor CPU usage of a router for specified duratio
    
    Args:
        router: Router hostname/IP
        community: SNMP community string
        duration: Monitoring duration in seconds (default 300 = 5 minutes)
        interval: Sampling interval in seconds (default 5)
    """
    # Cisco SNMP OID for CPU usage (5 second average)
    cpu_oid = '1.3.6.1.4.1.9.2.1.57.0'
    
    timestamps = []
    cpu_values = []
    start_time = time.time()
    
    print(f"Monitoring CPU usage for {router} for {duration} seconds...")

    while time.time() - start_time < duration:
        try:
            response = await snmp_get(router,version=2, community=community, oid=cpu_oid)
                
            timestamps.append(time.time() - start_time)
            cpu_values.append(response)
            
            await asyncio.sleep(interval)
            
        except Exception as e:
            print(f"Error during CPU monitoring: {str(e)}")
            continue
    
    # Create the graph
    plt.figure(figsize=(10, 6))
    plt.plot(timestamps, cpu_values, 'b-', label='CPU Usage')
    plt.title(f'CPU Usage for {router}')
    plt.xlabel('Time (seconds)')
    plt.ylabel('CPU Usage (%)')
    plt.grid(True)
    plt.legend()
    
    # Save the graph
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'cpu_usage_{router}_{timestamp}.jpg'
    plt.savefig(filename)
    plt.close()
    
    print(f"CPU usage graph saved as {filename}")
    return filename

async def main():
    # Get router information
    addresses, status = await get_router_info()
    
    # Print results
    print("\nRouter Addresses:")
    print(json.dumps(addresses, indent=2))
    
    print("\nInterface Status:")
    print(json.dumps(status, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
