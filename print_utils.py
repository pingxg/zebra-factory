import win32print
import win32api


def print_zebra(zpl_data=None, printer_name='zebra'):
    # Open the printer
    hprinter = win32print.OpenPrinter(printer_name)
    try:
        # Start the print job
        pdc = win32print.StartDocPrinter(hprinter, 1, ("ZPL Document", None, "RAW"))

        # Send raw data to the printer
        win32print.WritePrinter(hprinter, zpl_data.encode())

        # End the print job
        win32print.EndDocPrinter(hprinter)
    finally:
        win32print.ClosePrinter(hprinter)


def print_document(filename, printer_name="EPSON25CEF5 (ET-2810 Series)"):
    if printer_name is None:
        printer_name = win32print.GetDefaultPrinter()
    
    # Set the printer to the specified one
    win32print.SetDefaultPrinter(printer_name)
    
    # Use the Windows shell to print the document
    win32api.ShellExecute(0, "print", filename, None, ".", 0)




zpl_data = """^XA  ; Start of label

; Draw a box (border) around the label
^FO20,20^GB750,500,4^FS

; Add a title text
^FO50,50^A0N,70,70^FDZebra Label^FS

; Add a subtitle text
^FO50,150^A0N,40,40^FDComplex Design Example^FS

; Draw a line separator
^FO50,210^GB700,4,4^FS

; Add a barcode (Code 128 with value '12345678')
^FO100,250^BY3^BCN,100,Y,N,N^FD12345678^FS

; Add text below the barcode
^FO100,380^A0N,40,40^FDScan the barcode above^FS

; Add a QR code with value 'https://www.zebra.com'
^FO500,250^BQN,2,10^FDQA,https://www.zebra.com^FS

; Add text next to the QR code
^FO500,400^A0N,40,40^FDVisit Zebra's Website^FS  

^XZ  ; End of label
"""
