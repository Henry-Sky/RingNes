"""
Author: Henry-Sky <https://github.com/Henry-Sky>
Date: 2024-06-18
"""

from Mapper.mapper import Mapper
from utils import MIRROR


class Mapper_001(Mapper):
    def __init__(self, prgBanks: int, chrBanks: int):
        super().__init__(prgBanks, chrBanks)
        self.nCHRBankSelect4Lo = 0x00
        self.nCHRBankSelect4Hi = 0x00
        self.nCHRBankSelect8 = 0x00

        self.nPRGBankSelect16Lo = 0x00
        self.nPRGBankSelect16Hi = 0x00
        self.nPRGBankSelect32 = 0x00

        self.nLoadRegister = 0x00
        self.nLoadRegisterCount = 0x00
        self.nControlRegister = 0x00

        self.mirrormode = MIRROR.HORIZONTAL

        self.vRAMStatic = [0 for i in range(32 * 1024)]

    def cpuMapRead(self, addr: int) -> (bool, int, int):
        if 0x6000 <= addr <= 0x7FFF:
            mapped_addr = 0xFFFFFFFF  # Read is from cartridge
            data = self.vRAMStatic[addr & 0x1FFF]
            return True, mapped_addr, data
        elif addr >= 0x8000:
            if self.nControlRegister & 0b01000:
                # 16K Mode
                if 0x8000 <= addr <= 0xBFFF:
                    mapped_addr = self.nPRGBankSelect16Lo * 0x4000 + (addr & 0x3FFF)
                    return True, mapped_addr, 0x00
                elif 0xC000 <= addr <= 0xFFFF:
                    mapped_addr = self.nPRGBankSelect16Hi * 0x4000 + (addr & 0x3FFF)
                    return True, mapped_addr, 0x00
            else:
                mapped_addr = self.nPRGBankSelect32 * 0x8000 + (addr & 0x7FFF)
                return True, mapped_addr, 0x00
        else:
            return False, 0x00, 0x00

    def cpuMapWrite(self, addr: int, data: int) -> (bool, int):
        if 0x6000 <= addr <= 0x7FFF:
            mapped_addr = 0xFFFFFFFF
            self.vRAMStatic[addr & 0x1FFF] = data
            return True, mapped_addr
        if addr >= 0x8000:
            if data & 0x80:
                self.nLoadRegister = 0x00
                self.nLoadRegisterCount = 0
                self.nControlRegister |= 0x0C
            else:
                self.nLoadRegister >>= 1
                self.nLoadRegister |= (data & 0x01) << 4
                self.nLoadRegisterCount += 1

                if self.nLoadRegisterCount == 5:
                    nTargetRegister = (addr >> 13) & 0x03
                    if nTargetRegister == 0:
                        self.nControlRegister = self.nLoadRegister & 0x1F
                        flag = self.nControlRegister & 0x03
                        if flag == 0:
                            self.mirrormode = MIRROR.ONESCREEN_LO
                        elif flag == 1:
                            self.mirrormode = MIRROR.ONESCREEN_HI
                        elif flag == 2:
                            self.mirrormode = MIRROR.VERTICAL
                        elif flag == 3:
                            self.mirrormode = MIRROR.HORIZONTAL
                    elif nTargetRegister == 1:  # 0xA000 ~ 0xBFFF
                        if self.nControlRegister & 0b10000:
                            self.nCHRBankSelect4Lo = self.nLoadRegister & 0x1F
                        else:
                            self.nCHRBankSelect8 = self.nLoadRegister & 0x1E
                    elif nTargetRegister == 2:
                        if self.nControlRegister & 0b10000:
                            self.nCHRBankSelect4Hi = self.nLoadRegister & 0x1F
                    elif nTargetRegister == 3:
                        nRPGMode = (self.nControlRegister >> 2) & 0x03
                        if nRPGMode == 0 or nRPGMode == 1:
                            self.nPRGBankSelect32 = (self.nLoadRegister & 0x0E) >> 1
                        elif nRPGMode == 2:
                            self.nPRGBankSelect16Lo = 0
                            self.nPRGBankSelect16Hi = self.nLoadRegister & 0x0F
                        elif nRPGMode == 3:
                            self.nPRGBankSelect16Lo = self.nLoadRegister & 0x0F
                            self.nPRGBankSelect16Hi = self._nPRGBanks - 1
                    self.nLoadRegister = 0x00
                    self.nLoadRegisterCount = 0
        return False, 0x00