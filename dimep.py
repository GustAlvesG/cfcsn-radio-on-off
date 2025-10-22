from escpos.printer import Usb

printer = Usb(0x04b8, 0x0e15, 0, 0, 0)

printer.text("Hello, ESC/POS World!\n")
printer.cut() # Cut the paper