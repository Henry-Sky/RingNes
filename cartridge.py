"""
Author: Henry-Sky <https://github.com/Henry-Sky>
Date: 2024-06-18
"""

from Mapper.mapper import Mapper
from Mapper.mapper_000 import Mapper_000
from Mapper.mapper_001 import Mapper_001
from Mapper.mapper_002 import Mapper_002
from Mapper.mapper_003 import Mapper_003
from Mapper.mapper_004 import Mapper_004
from utils import MIRROR


class Cartridge(object):
    def __init__(self, path):
        self.bImageValid = False

        self.nMapperID = 0
        self.nPRGBanks = 0
        self.nCHRBanks = 0

        self.vPRGMemory = []
        self.vCHRMemory = []
        self.mirror = None
        self.pMapper = None

        with open(path, 'rb') as f:
            name = str(f.read(4), encoding='utf-8')
            prg_rom_chunks = int.from_bytes(f.read(1), byteorder='little')
            chr_rom_chunks = int.from_bytes(f.read(1), byteorder='little')
            mapper1 = int.from_bytes(f.read(1), byteorder='little')
            mapper2 = int.from_bytes(f.read(1), byteorder='little')
            prg_ram_size = int.from_bytes(f.read(1), byteorder='little')
            tv_system1 = int.from_bytes(f.read(1), byteorder='little')
            tv_system2 = int.from_bytes(f.read(1), byteorder='little')
            unused = int.from_bytes(f.read(5), byteorder='little')
            # Print Cartridge INFO
            print(
                "Cartridge Info:\n" +
                "\tName: {}\n".format(name) +
                "\tPRG Chunks: {}\n".format(prg_rom_chunks) +
                "\tCHR Chunks: {}\n".format(chr_rom_chunks) +
                "\tMapper1: {}\n".format(mapper1) +
                "\tMapper2: {}\n".format(mapper2) +
                "\tPRG RAM Size: {}\n".format(prg_ram_size) +
                "\tTV System 1: {}\n".format(tv_system1) +
                "\tTV System 2: {}\n".format(tv_system2) +
                "\tUnused: {}\n".format(unused)
            )

            # File Type
            nFileType = 2 if (mapper2 & 0x0C) == 0x08 else 1
            # According to file type, set nPRG and nCHR
            if nFileType == 1:
                self.nPRGBanks = prg_rom_chunks
                self.vPRGMemory = list(f.read(self.nPRGBanks * 16384))  # PRG SIZE = nPRG * 16KB
                self.nCHRBanks = chr_rom_chunks
                self.vCHRMemory = list(f.read(self.nCHRBanks * 8192))  # CHR SIZE = nCHR * 8KB
            elif nFileType == 2:
                pass

            # mirror type
            self.mirror = MIRROR.VERTICAL if mapper1 & 0x01 > 0 else MIRROR.HORIZONTAL
            # mapper selection
            self.nMapperID = ((mapper2 >> 4) << 4) | (mapper1 >> 4)
            if self.nMapperID == 0:
                self.pMapper = Mapper_000(self.nPRGBanks, self.nCHRBanks)
            elif self.nMapperID == 1:
                self.pMapper = Mapper_001(self.nPRGBanks, self.nCHRBanks)
            elif self.nMapperID == 2:
                self.pMapper = Mapper_002(self.nPRGBanks, self.nCHRBanks)
            elif self.nMapperID == 3:
                self.pMapper = Mapper_003(self.nPRGBanks, self.nCHRBanks)
            elif self.nMapperID == 4:
                self.pMapper = Mapper_004(self.nPRGBanks, self.nCHRBanks)
            else:
                self.pMapper = Mapper(self.nPRGBanks, self.nCHRBanks)
        self.bImageValid = True

    def ImageValid(self) -> bool:
        return self.bImageValid

    def cpuWrite(self, addr: int, data: int) -> bool:
        flag, mapped_addr = self.pMapper.cpuMapWrite(addr, data)
        if flag:
            self.vPRGMemory[mapped_addr] = data
            return True
        else:
            return False

    def cpuRead(self, addr: int, readonly: bool) -> (bool, int):
        flag, mapped_addr, data = self.pMapper.cpuMapRead(addr)
        if flag:
            data = self.vPRGMemory[mapped_addr]
            return True, data
        else:
            return False, 0x00

    def ppuWrite(self, addr: int, data: int) -> bool:
        mapped_addr = 0x0000
        if self.pMapper.ppuMapWrite(addr, mapped_addr):
            self.vCHRMemory[mapped_addr] = data
            return True
        else:
            return False

    def ppuRead(self, addr: int, data: int) -> bool:
        mapped_addr = 0
        if self.pMapper.ppuMapRead(addr, mapped_addr):
            data = self.vCHRMemory[mapped_addr]
            return True
        else:
            return False
