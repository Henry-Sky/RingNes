import sys
from ppu import Ppu2c02
from utils import hex2int
from PyQt5 import QtWidgets


class Pixel(object):
    def __init__(self, red: int, green: int, blue: int, alpha=hex2int("0xff")):
        self.red = red
        self.green = green
        self.blue = blue
        self.alpha = alpha
        self.n = self.red | (self.green << 8) | (self.blue << 16) | (self.alpha << 24)


ColorMap = {
    "GREY": Pixel(192, 192, 192),
    "DARK_GREY": Pixel(128, 128, 128),
    "VERY_DARK_GREY": Pixel(64, 64, 64),
    "RED": Pixel(255, 0, 0),
    "DARK_RED": Pixel(128, 0, 0),
    "VERY_DARK_RED": Pixel(64, 0, 0),
    "YELLOW": Pixel(255, 255, 0),
    "DARK_YELLOW": Pixel(128, 128, 0),
    "VERY_DARK_YELLOW": Pixel(64, 64, 0),
    "GREEN": Pixel(0, 255, 0),
    "DARK_GREEN": Pixel(0, 128, 0),
    "VERY_DARK_GREEN": Pixel(0, 64, 0),
    "CYAN": Pixel(0, 255, 255),
    "DARK_CYAN": Pixel(0, 128, 128),
    "VERY_DARK_CYAN": Pixel(0, 64, 64),
    "BLUE": Pixel(0, 0, 255),
    "DARK_BLUE": Pixel(0, 0, 128),
    "VERY_DARK_BLUE": Pixel(0, 0, 64),
    "MAGENTA": Pixel(255, 0, 255),
    "DARK_MAGENTA": Pixel(128, 0, 128),
    "VERY_DARK_MAGENTA": Pixel(64, 0, 64),
    "WHITE": Pixel(255, 255, 255),
    "BLACK": Pixel(0, 0, 0),
    "BLANK": Pixel(0, 0, 0, 0),
}


class Screen(object):
    def __init__(self, screen_w, screen_h, debug = False):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.ppu = None

    def connectPPU(self, p: Ppu2c02):
        self.ppu = p

    def DrawScreen(self):
        app = QtWidgets.QApplication(sys.argv)
        window = QtWidgets.QWidget()
        window.setWindowTitle('Nes')
        window.resize(self.screen_w, self.screen_h)
        window.show()
        sys.exit(app.exec_())

