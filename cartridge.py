from mapper import Mapper
from utils import MIRROR, hex2int


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
            # If "trainer" exists, just read past it
            if mapper1 & hex2int("0x04") > 0:
                f.read(512)
            # File Type
            nFileType = 1
            # According to file type, set nPRG and nCHR
            if nFileType == 0:
                pass
            elif nFileType == 1:
                self.nPRGBanks = prg_rom_chunks
                self.vPRGMemory = list(f.read(self.nPRGBanks * 16384))

                self.nCHRBanks = chr_rom_chunks
                self.vCHRMemory = list(f.read(self.nCHRBanks * 8192))
            # mirror type
            self.mirror = MIRROR.VERTICAL if mapper1 & hex2int("0x01") > 0 else MIRROR.HORIZONTAL
            # mapper selection
            self.nMapperID = ((mapper2 >> 4) << 4) | (mapper1 >> 4)
            if self.nMapperID == 0:
                pass
            elif self.nMapperID == 1:
                pass
            self.pMapper = Mapper(self.nPRGBanks, self.nCHRBanks)

        self.bImageValid = True

    def ImageValid(self) -> bool:
        return self.bImageValid

    def cpuWrite(self, addr: int, data: int) -> bool:
        mapped_addr = 0
        if self.pMapper.cpuMapWrite(addr, mapped_addr):
            self.vPRGMemory[mapped_addr] = data
            return True
        else:
            return False

    def cpuRead(self, addr: int, data: int) -> bool:
        mapped_addr = 0
        if self.pMapper.cpuMapRead(addr, mapped_addr):
            data = self.vPRGMemory[mapped_addr]
            return True
        else:
            return False

    def ppuWrite(self, addr: int, data: int) -> bool:
        mapped_addr = 0
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
