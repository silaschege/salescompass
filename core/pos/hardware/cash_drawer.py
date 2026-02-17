from .receipt_printer import ReceiptPrinter

class CashDrawer:
    """
    Helper for Cash Drawer operations.
    Most drawers are connected to the receipt printer's DK port.
    """
    
    def __init__(self, printer=None):
        self.printer = printer

    def open(self):
        """
        Send the opening signal to the drawer.
        If a printer is provided, it sends the pulse via escape codes.
        """
        if self.printer and isinstance(self.printer, ReceiptPrinter):
            self.printer.connect()
            self.printer.drawer_kick()
            return self.printer.send()
        
        return False, "No printer connection configured to trigger drawer."
