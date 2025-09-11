import socket
import struct

class ArtNetSender:
    def __init__(self, ip="192.168.18.28", universe=0, port=6454):
        self.ip = ip
        self.port = port
        self.universe = universe
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def send_fixtures(self, fixtures):
        # Prépare le tableau DMX (512 canaux)
        dmx = [0] * 512
        
        for fixture in fixtures:
            # Choisit les valeurs RGB selon kick ou sequence
            if fixture["dimmer"]["id"] != "NA":
                d = fixture["dimmer"]["value"]
                addr_d = fixture["dimmer"]["id"] - 1
                            
            if fixture["kick_activated"]:
                r = fixture["kick_red"]["value"]
                g = fixture["kick_green"]["value"]
                b = fixture["kick_blue"]["value"]
            elif fixture["repos_activated"]:
                r = fixture["repos_red"]["value"]
                g = fixture["repos_green"]["value"]
                b = fixture["repos_blue"]["value"]
            else:
                r = fixture["sequence_red"]["value"]
                g = fixture["sequence_green"]["value"]
                b = fixture["sequence_blue"]["value"]

            
            addr_r = fixture["sequence_red"]["id"] - 1
            addr_g = fixture["sequence_green"]["id"] - 1
            addr_b = fixture["sequence_blue"]["id"] - 1
                

            
            # S'assurer que les valeurs sont dans la plage 0-255
            r = max(0, min(255, int(r)))
            g = max(0, min(255, int(g)))
            b = max(0, min(255, int(b)))
            
            # S'assurer que les adresses sont dans la plage valide
            if fixture["dimmer"]["id"] != "NA" and 0 <= addr_d < 512:
                dmx[addr_d] = d
            if 0 <= addr_r < 512:
                dmx[addr_r] = r
            if 0 <= addr_g < 512:
                dmx[addr_g] = g
            if 0 <= addr_b < 512:
                dmx[addr_b] = b

        # Envoie le paquet Art-Net
        self._send_artnet_packet(dmx)

    def _send_artnet_packet(self, dmx_data):
        # En-tête Art-Net standard
        packet = bytearray()
        packet.extend(b"Art-Net\x00")  # ID (8 bytes)
        packet.extend(struct.pack("<H", 0x5000))  # OpCode ArtDMX (2 bytes, little-endian)
        packet.extend(struct.pack(">H", 14))  # ProtVer (2 bytes, big-endian)
        packet.extend(struct.pack("B", 0))  # Sequence (1 byte)
        packet.extend(struct.pack("B", 0))  # Physical (1 byte)
        packet.extend(struct.pack("<H", self.universe))  # Universe (2 bytes, little-endian)
        packet.extend(struct.pack(">H", len(dmx_data)))  # Length (2 bytes, big-endian)
        packet.extend(dmx_data)  # Data (512 bytes max)

        try:
            self.sock.sendto(packet, (self.ip, self.port))
        except Exception as e:
            print(f"Erreur envoi Art-Net: {e}")

    def close(self):
        if self.sock:
            self.sock.close()