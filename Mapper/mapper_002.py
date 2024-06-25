"""
Author: Henry-Sky <https://github.com/Henry-Sky>
Date: 2024-06-18
"""

from Mapper.mapper import Mapper


class Mapper_002(Mapper):
    def __init__(self, prgBanks: int, chrBanks: int):
        super().__init__(prgBanks, chrBanks)
        self.nPRGBankSelectLo = 0x00
        self.nPRGBankSelectHi = 0x00

    def cpuMapRead(self, addr: int) -> (bool, int, int):
        if 0x8000 <= addr < 0xBFFF:
            mapped_addr = self.nPRGBankSelectLo * 0x4000 + (addr & 0x3FFF)
            return True, mapped_addr, 0x00
        elif 0xC000 <= addr < 0xFFFF:
            mapped_addr = self.nPRGBankSelectHi * 0x4000 + (addr & 0x3FFF)
            return True, mapped_addr, 0x00
        else:
            return False, addr, 0x00

    def cpuMapWrite(self, addr: int, data: int) -> (bool, int):
        if 0x8000 <= addr < 0xFFFF:
            self.nPRGBankSelectLo = data & 0x0F
        return False