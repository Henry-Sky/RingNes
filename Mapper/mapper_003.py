"""
Author: Henry-Sky <https://github.com/Henry-Sky>
Date: 2024-06-18
"""

from Mapper.mapper import Mapper


class Mapper_003(Mapper):
    def __init__(self, prgBanks: int, chrBanks: int):
        super().__init__(prgBanks, chrBanks)
        self.nCHRBankSelect = 0x00

    def cpuMapRead(self, addr: int) -> (bool, int, int):
        if 0x8000 <= addr < 0xFFFF:
            if self._nPRGBanks == 1:
                mapped_addr = addr & 0x3FFF
                return True, mapped_addr, 0x00
            elif self._nPRGBanks == 2:
                mapped_addr = addr & 0x7FFF
                return True, mapped_addr, 0x00
        else:
            return False, addr, 0x00

    def cpuMapWrite(self, addr: int, data: int) -> (bool, int):
        if 0x8000 <= addr < 0xFFFF:
            self.nCHRBankSelect = data & 0x03
            mapped_addr = addr
        return False, mapped_addr

