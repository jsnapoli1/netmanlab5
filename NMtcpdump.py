from scapy.all import rdpcap
from scapy.layers.l2 import Ether
from typing import Optional

def get_interface_mac(pcap_file: str, interface_name: str) -> Optional[str]:

    try:
        # read pcap file
        packets = rdpcap(pcap_file)
        
        # check each packet for interface info
        for packet in packets:
            if Ether in packet:
                src_mac = packet[Ether].src
                
                # You might need to implement additional logic here to match
                # the interface_name with the correct MAC address based on your
                # specific requirements
                
                # For now, returning the first source MAC found
                # This is a simplified implementation

                # return src mac
                return src_mac
                
        return None
        
    except Exception as e:
        print(f"Error reading pcap file: {str(e)}")
        return None

def format_mac_address(mac: str) -> str:

    mac = mac.replace(':', '').replace('-', '').replace('.', '')
    return ':'.join(mac[i:i+2] for i in range(0, 12, 2))
    
def main():
	file = "Lab5_tcpdump.pcap"
	interface = "R2-F0/0"
	mac = get_interface_mac(file, interface)
	formatted_mac = format_mac_address(mac)
	print(formatted_mac)
	interface = "R3-F0/0"
	mac = get_interface_mac(file, interface)
	formatted_mac = format_mac_address(mac)
	print(formatted_mac)
	
if __name__ == "__main__":
	main()
	
	
	
	
	
	
