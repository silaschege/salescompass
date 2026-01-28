# ESC/POS Control Codes (Bytes)

# Initialization
ESC = b'\x1b'
GS = b'\x1d'
InitializePrinter = ESC + b'@'

# Alignment
AlignLeft = ESC + b'a\x00'
AlignCenter = ESC + b'a\x01'
AlignRight = ESC + b'a\x02'

# Text Formatting
FontStandard = ESC + b'M\x00'
FontSmall = ESC + b'M\x01'
BoldOn = ESC + b'E\x01'
BoldOff = ESC + b'E\x00'
UnderlineOn = ESC + b'-\x01'
UnderlineOff = ESC + b'-\x00'
DoubleHeightOn = ESC + b'!\x10'
DoubleHeightOff = ESC + b'!\x00'
DoubleWidthOn = ESC + b'!\x20'
DoubleWidthOff = ESC + b'!\x00'
FullSizeOn = ESC + b'!\x30'
FullSizeOff = ESC + b'!\x00'

# Feed & Cut
FeedAndCut = GS + b'V\x00'
FeedAndCutPartial = GS + b'V\x01'

# Cash Drawer
DrawerKick2 = ESC + b'p\x00\x19\xfa'  # Pin 2
DrawerKick5 = ESC + b'p\x01\x19\xfa'  # Pin 5

# Barcode (Simple Code128)
BarcodeHRI_Below = GS + b'H\x02'
BarcodeHeight = GS + b'h\x64'  # 100 dots
BarcodeWidth = GS + b'w\x03'
BarcodeCode128 = GS + b'k\x49'  # Code128 selection

# Templates
DASHED_LINE = "-"
DOUBLE_LINE = "="

def get_line(width=48, char='-'):
    return char * width
