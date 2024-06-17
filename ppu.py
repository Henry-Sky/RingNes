from cartridge import Cartridge
from utils import hex2int


class Ppu2c02:
    def __init__(self):
        self.__scanline = 0
        self.__cycle = 0
        self.frame_complete = False
        self.__cart = None

    def connectCart(self, cart: Cartridge):
        self.__cart = cart

    def cpuWrite(self, addr: int, data: int):
        if addr == 0:  # Control
            pass
        elif addr == 1:  # Mask
            pass
        elif addr == 2:  # Status
            pass
        elif addr == 3:  # OAM Address
            pass
        elif addr == 4:  # OAM Data
            pass
        elif addr == 5:  # Scroll
            pass
        elif addr == 6:  # PPU Address
            pass
        elif addr == 7:  # PPU Data
            pass
        else:
            pass

    def cpuRead(self, addr: int, readonly: bool) -> int:
        data = 0
        if addr == 0:
            return data
        elif addr == 1:
            return data
        elif addr == 2:
            return data
        elif addr == 3:
            return data
        elif addr == 4:
            return data
        elif addr == 5:
            return data
        elif addr == 6:
            return data
        elif addr == 7:
            return data
        else:
            return data

    def ppuRead(self, addr: int, readonly: bool) -> int:
        data = 0
        addr &= hex2int("0x3fff")
        if self.__cart.ppuRead(addr, readonly):
            pass
        return data

    def ppuWrite(self, addr: int, data: int):
        addr &= hex2int("0x3fff")
        if self.__cart.ppuWrite(addr, data):
            pass

    def clock(self):
        self.__cycle += 1
        if self.__cycle >= 341:
            self.__cycle = 0
            self.__scanline += 1
            if self.__scanline >= 261:
                self.__scanline = -1
                self.frame_complete = True
