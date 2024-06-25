from enum import Enum


class INSTRUCTION:
    def __init__(self, opname, operate, addrmode, cycles: int):
        self.opname = opname
        self.operate = operate
        self.addrmode = addrmode
        self.cycles = cycles


class TILE:
    def __init__(self, y: int, id: int, attr: int, x: int):
        self.y = y
        self.id = id
        self.attribute = attr
        self.x = x


class FLAGS(Enum):
    N = 1 << 7  # Negative Flag (1 when result is negative)
    V = 1 << 6  # Overflow Flag (1 on signed overflow)
    U = 1 << 5  # Unused (always 1)
    B = 1 << 4  # Break Flag (1 when interrupt was caused by a BRK)
    D = 1 << 3  # Decimal Mode (1 when CPU in BCD mode)
    I = 1 << 2  # IRQ Flag
    Z = 1 << 1  # Zero Flag (1 when all bits of a result are 0)
    C = 1 << 0  # Carry Flag (1 on unsigned overflow)


class MIRROR(Enum):
    HARDWARE = "hardware"
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    ONESCREEN_LO = "onescreen_lo"
    ONESCREEN_HI = "onescreen_hi"


class Pixel:
    def __init__(self, red: int, green: int, blue: int, alpha=0xff):
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


def PalInit() -> list:
    pals = [
        Pixel(84, 84, 84),
        Pixel(0, 30, 116),
        Pixel(8, 16, 144),
        Pixel(48, 0, 136),
        Pixel(68, 0, 100),
        Pixel(92, 0, 48),
        Pixel(84, 4, 0),
        Pixel(60, 24, 0),
        Pixel(32, 42, 0),
        Pixel(8, 58, 0),
        Pixel(0, 64, 0),
        Pixel(0, 60, 0),
        Pixel(0, 50, 60),
        Pixel(0, 0, 0),
        Pixel(0, 0, 0),
        Pixel(0, 0, 0),

        Pixel(152, 150, 152),
        Pixel(8, 76, 196),
        Pixel(48, 50, 236),
        Pixel(92, 30, 228),
        Pixel(136, 20, 176),
        Pixel(160, 20, 100),
        Pixel(152, 34, 32),
        Pixel(120, 60, 0),
        Pixel(84, 90, 0),
        Pixel(40, 114, 0),
        Pixel(8, 124, 0),
        Pixel(0, 118, 40),
        Pixel(0, 102, 120),
        Pixel(0, 0, 0),
        Pixel(0, 0, 0),
        Pixel(0, 0, 0),

        Pixel(236, 238, 236),
        Pixel(76, 154, 236),
        Pixel(120, 124, 236),
        Pixel(176, 98, 236),
        Pixel(228, 84, 236),
        Pixel(236, 88, 180),
        Pixel(236, 106, 100),
        Pixel(212, 136, 32),
        Pixel(160, 170, 0),
        Pixel(116, 196, 0),
        Pixel(76, 208, 32),
        Pixel(56, 204, 108),
        Pixel(56, 180, 204),
        Pixel(60, 60, 60),
        Pixel(0, 0, 0),
        Pixel(0, 0, 0),

        Pixel(236, 238, 236),
        Pixel(168, 204, 236),
        Pixel(188, 188, 236),
        Pixel(212, 178, 236),
        Pixel(236, 174, 236),
        Pixel(236, 174, 212),
        Pixel(236, 180, 176),
        Pixel(228, 196, 144),
        Pixel(204, 210, 120),
        Pixel(180, 222, 120),
        Pixel(168, 226, 144),
        Pixel(152, 226, 180),
        Pixel(160, 214, 228),
        Pixel(160, 162, 160),
        Pixel(0, 0, 0),
        Pixel(0, 0, 0),
    ]
    return pals
