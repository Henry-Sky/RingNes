from utils import hex2int


class Mapper(object):
    def __init__(self, prgBanks: int, chrBanks: int):
        self._nPRGBanks = prgBanks
        self._nCHRBanks = chrBanks

    def cpuMapRead(self, addr: int, mapped_addr: int) -> bool:
        if hex2int("0x8000") <= addr <= hex2int("0xFFFF"):
            mapped_addr = addr & (hex2int("0x7fff") if self._nPRGBanks > 1 else hex2int("0x3fff"))
            return True
        else:
            return False

    def cpuMapWrite(self, addr: int, mapped_addr: int) -> bool:
        if hex2int("0x8000") <= addr <= hex2int("0xFFFF"):
            mapped_addr = addr & (hex2int("0x7fff") if self._nPRGBanks > 1 else hex2int("0x3fff"))
            return True
        else:
            return False

    def ppuMapRead(self, addr: int, mapped_addr: int) -> bool:
        if hex2int("0x0000") <= addr <= hex2int("0x1fff"):
            mapped_addr = addr
            return True
        else:
            return False

    def ppuMapWrite(self, addr: int, mapped_addr: int) -> bool:
        if hex2int("0x0000") <= addr <= hex2int("0x1fff"):
            if self._nCHRBanks == 0:
                mapped_addr = addr
                return True
            else:
                return False
        else:
            return False