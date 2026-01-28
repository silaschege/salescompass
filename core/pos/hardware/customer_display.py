from . import escpos_templates as codes

class CustomerDisplay:
    """
    Helper for Customer Pole Displays (usually 2x20 VFD).
    Supports common ESC/POS line display commands.
    """
    
    def __init__(self, port_path=None, width=20):
        self.port_path = port_path
        self.width = width
        self.buffer = b''

    def clear(self):
        """Clear the display."""
        # ESC [ 2 J is a common clear command for VFDs, but ESC @ works for many
        self.buffer = codes.InitializePrinter
        return self

    def show_text(self, line1="", line2=""):
        """Format text for a 2-line display."""
        # Pad lines to width
        l1 = line1[:self.width].ljust(self.width)
        l2 = line2[:self.width].ljust(self.width)
        
        self.buffer += l1.encode('ascii', errors='replace')
        self.buffer += b'\n' # Move to next line (VFD specific)
        self.buffer += l2.encode('ascii', errors='replace')
        
        return self.send()

    def send(self):
        """Send the buffer to the display port."""
        if not self.port_path:
            return False, "No display port configured."
            
        try:
            with open(self.port_path, 'wb') as f:
                f.write(self.buffer)
            return True, "Data sent to display."
        except Exception as e:
            return False, str(e)
