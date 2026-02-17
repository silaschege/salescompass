import socket
from . import escpos_templates as codes

class ReceiptPrinter:
    """
    Driver for ESC/POS compatible printers.
    Supports Network (TCP) and Local (File/Port) connections.
    """
    
    def __init__(self, connection_type='network', host=None, port=9100, path=None, width=48):
        self.connection_type = connection_type
        self.host = host
        self.port = port
        self.path = path
        self.width = width
        self.buffer = b''

    def connect(self):
        """Establish connection or initialize buffer."""
        self.buffer = codes.InitializePrinter
        return True

    def write(self, data):
        """Add data to buffer."""
        if isinstance(data, str):
            self.buffer += data.encode('ascii', errors='replace')
        else:
            self.buffer += data

    def text(self, msg, align='left', bold=False, double_height=False, double_width=False):
        """Add formatted text."""
        if align == 'center':
            self.write(codes.AlignCenter)
        elif align == 'right':
            self.write(codes.AlignRight)
        else:
            self.write(codes.AlignLeft)

        if bold: self.write(codes.BoldOn)
        if double_height: self.write(codes.DoubleHeightOn)
        if double_width: self.write(codes.DoubleWidthOn)

        self.write(msg + '\n')

        # Reset
        if bold: self.write(codes.BoldOff)
        if double_height: self.write(codes.DoubleHeightOff)
        if double_width: self.write(codes.DoubleWidthOff)
        self.write(codes.AlignLeft)

    def line(self, char='-'):
        """Print a horizontal line."""
        self.write(codes.get_line(self.width, char) + '\n')

    def cut(self):
        """Cut the paper."""
        self.write(codes.FeedAndCut)

    def drawer_kick(self):
        """Kick the cash drawer."""
        self.write(codes.DrawerKick2)

    def send(self):
        """Send the buffered commands to the printer."""
        if self.connection_type == 'network':
            if not self.host:
                return False, "No host provided for network printer."
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(5)
                    s.connect((self.host, self.port))
                    s.sendall(self.buffer)
                return True, "Sent to network printer."
            except Exception as e:
                return False, str(e)
        
        elif self.connection_type == 'usb' or self.connection_type == 'serial':
            if not self.path:
                return False, "No port/path provided for local printer."
            try:
                with open(self.path, 'wb') as f:
                    f.write(self.buffer)
                return True, "Sent to local printer."
            except Exception as e:
                return False, str(e)
        
        return False, "Unsupported connection type."

    def clear(self):
        """Clear the buffer."""
        self.buffer = b''

    @staticmethod
    def discover_network_printers(subnet=None):
        """
        Scans the network for devices with port 9100 open.
        """
        import socket
        import threading
        from concurrent.futures import ThreadPoolExecutor
        
        if not subnet:
            # Try to get local subnet
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                s.close()
                ip_prefix = '.'.join(local_ip.split('.')[:-1]) + '.'
            except:
                ip_prefix = '192.168.1.'
        else:
            ip_prefix = subnet
            
        found_printers = []
        
        def check_ip(ip):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                if s.connect_ex((ip, 9100)) == 0:
                    try:
                        name = socket.gethostbyaddr(ip)[0]
                    except:
                        name = "Network Printer"
                    found_printers.append({'ip': ip, 'name': name, 'port': 9100})
                    
        with ThreadPoolExecutor(max_workers=50) as executor:
            ips = [ip_prefix + str(i) for i in range(1, 255)]
            executor.map(check_ip, ips)
            
        return found_printers
