"""
Author: Henry-Sky <https://github.com/Henry-Sky>
Date: 2024-06-18
"""

from Mapper.mapper import Mapper


class Mapper_000(Mapper):
    def __init__(self, prgBanks: int, chrBanks: int):
        super().__init__(prgBanks, chrBanks)

    def cpuMapRead(self, addr: int) -> (bool, int, int):
        data = 0x00
        if 0x8000 <= addr < 0xFFFF:
            mapped_addr = addr & (0x00007FFF if self._nPRGBanks > 1 else 0x00003FFF)
            return True, mapped_addr, data
        else:
            return False, addr, data

    def cpuMapWrite(self, addr: int, data: int) -> (bool, int):
        if 0x8000 <= addr < 0xFFFF:
            mapped_addr = addr & (0x00007FFF if self._nPRGBanks > 1 else 0x00003FFF)
            return True, mapped_addr
        else:
            return False, addr

    def ppuMapRead(self, addr: int) -> (bool, int):
        if 0x0000 <= addr < 0x1FFF:
            mapped_addr = addr
            return True, mapped_addr
        else:
            return False, addr

    def ppuMapWrite(self, addr: int, data: int) -> (bool, int):
        if 0x0000 <= addr < 0x1FFF:
            if self._nCHRBanks == 0:
                mapped_addr = addr
                return True, mapped_addr
        return False, addr
