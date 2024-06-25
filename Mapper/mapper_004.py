"""
Author: Henry-Sky <https://github.com/Henry-Sky>
Date: 2024-06-18
"""

from Mapper.mapper import Mapper
from utils import MIRROR


class Mapper_004(Mapper):
    def __init__(self, prgBanks: int, chrBanks: int):
        super().__init__(prgBanks, chrBanks)
        # The extent RAM address $0x6000 ~ $0x7FFF
        self.vRAMStatic = [0 for i in range(32 * 1024)]
        # Control variables
        self.nTargetRegister = 0x00
        self.bPRGBankMode = False
        self.bCHRInversion = False
        self.mirrormode = MIRROR.HORIZONTAL

        self.pRegister = [0 for i in range(8)]
        self.pCHRBank = [0 for i in range(8)]
        self.pPRGBank = [0 for i in range(4)]

        self.bIRQActive = False
        self.bIRQEnable = False
        self.bIRQUpdate = False
        self.nIRQCounter = 0x0000
        self.nIRQReload = 0x00000

    def cpuMapRead(self, addr: int) -> (bool, int, int):
        if 0x6000 <= addr <= 0x7FFF:
            # Read the ram on cartridge
            mapped_addr = 0xFFFFFFFF
            data = self.vRAMStatic[addr & 0x1FFF]
            return True, mapped_addr, data
        elif 0x8000 <= addr <= 0x9FFFF:
            mapped_addr = self.pPRGBank[0] + (addr & 0x1FFF)
            return True, mapped_addr, 0x00
        elif 0xA000 <= addr <= 0xBFFF:
            # Address for Register Control
            mapped_addr = self.pPRGBank[1] + (addr & 0x1FFF)
            return True, mapped_addr, 0x00
        elif 0xC000 <= addr <= 0xDFFF:
            mapped_addr = self.pPRGBank[2] + (addr & 0x1FFF)
            return True, mapped_addr, 0x00
        elif 0xE000 <= addr <= 0xFFFF:
            mapped_addr = self.pPRGBank[3] + (addr & 0x1FFF)
            return True, mapped_addr, 0x00
        return False, 0x00, 0x00

    def cpuMapWrite(self, addr: int, data: int) -> (bool, int):
        if 0x6000 <= addr <= 0x7FFF:
            # Write to static ram on cartridge
            mapped_addr = 0xFFFFFFFF
            self.vRAMStatic[addr & 0x1FFF] = data
            return True, mapped_addr
        elif 0x8000 <= addr <= 0x9FFF:
            # Bank Select!
            if not addr & 0x0001:
                self.nTargetRegister = data & 0x07
                self.bPRGBankMode = data & 0x40
                self.bCHRInversion = data & 0x80
            else:
                self.pRegister[self.nTargetRegister] = data
                if self.bCHRInversion:
                    self.pCHRBank[0] = self.pRegister[2] * 0x0400
                    self.pCHRBank[1] = self.pRegister[3] * 0x0400
                    self.pCHRBank[2] = self.pRegister[4] * 0x0400
                    self.pCHRBank[3] = self.pRegister[5] * 0x0400
                    self.pCHRBank[4] = (self.pRegister[0] & 0xFE) * 0x0400
                    self.pCHRBank[5] = self.pRegister[0] * 0x0400 + 0x0400
                    self.pCHRBank[6] = (self.pRegister[1] & 0xFE) * 0x0400
                    self.pCHRBank[7] = self.pRegister[1] * 0x0400 + 0x0400
                else:
                    self.pCHRBank[0] = (self.pRegister[0] & 0xFE) * 0x0400
                    self.pCHRBank[1] = self.pRegister[0] * 0x0400 + 0x0400
                    self.pCHRBank[2] = (self.pRegister[1] & 0xFE) * 0x0400
                    self.pCHRBank[3] = self.pRegister[1] * 0x0400 + 0x0400
                    self.pCHRBank[4] = self.pRegister[2] * 0x0400
                    self.pCHRBank[5] = self.pRegister[3] * 0x0400
                    self.pCHRBank[6] = self.pRegister[4] * 0x0400
                    self.pCHRBank[7] = self.pRegister[5] * 0x0400
                if self.bPRGBankMode:
                    self.pPRGBank[2] = (self.pRegister[6] & 0x3F) * 0x2000
                    self.pPRGBank[0] = (self._nPRGBanks * 2 - 2) * 0x2000
                else:
                    self.pPRGBank[0] = (self.pRegister[6] & 0x3F) * 0x2000
                    self.pPRGBank[2] = (self._nPRGBanks * 2 - 2) * 0x2000
                self.pPRGBank[1] = (self.pRegister[7] & 0x3F) * 0x2000
                self.pPRGBank[3] = (self._nPRGBanks * 2 - 1) * 0x2000
            return False, 0x00
        elif 0xA000 <= addr <= 0xBFFF:
            if not addr & 0x0001:
                if data & 0x01:
                    self.mirrormode = MIRROR.HORIZONTAL
                else:
                    self.mirrormode = MIRROR.VERTICAL
            else:
                # PRG Ram Protect
                pass
            return False, 0x00
        elif 0xC000 <= addr <= 0xDFFF:
            if not addr & 0x0001:
                self.nIRQReload = data
            else:
                self.nIRQCounter = 0x0000
            return False, 0x00
        elif 0xE000 <= addr <= 0xFFFF:
            if not addr & 0x0001:
                self.bIRQEnable = False
                self.bIRQActive = False
            else:
                self.bIRQEnable = True
            return False, 0x00
        return False, 0x00
