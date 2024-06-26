"""
Author: Henry-Sky <https://github.com/Henry-Sky>
Date: 2024-06-18
"""

"""Instruction

table ref: https://www.cnblogs.com/xiayong123/archive/2011/08/14/3717572.html

*****************************************************
*                 system memory                     *
*****************************************************
*  $0000 ~ $07FF  *        NES 2KB RAM              *
*****************************************************
*  $0800 ~ $0FFF  *  2KB Mirror from [$0000~$07FF]  *
*  $1000 ~ $17FF  *  2KB Mirror from [$0000~$07FF]  *
*  $1800 ~ $1FFF  *  2KB Mirror from [$0000~$07FF]  *
*****************************************************
*  $2000 ~ $2007  *  8Byte for PPU Register         *
*****************************************************
*  $2008 ~ $3FFF  *  Mirror for PPU Register        *
*****************************************************
*  $4000 ~ $4013  *       pAPU Register             *
*****************************************************
*  $4014 ~ $4014  *    OAM-DMA Register             *
*****************************************************
*                  ETC ... ...                      *
*****************************************************



*****************************************************
*                video memory                       *
*****************************************************
*  $0000 ~ $0FFF  *     Pattern Table 0 : 4KB       *
*****************************************************
*  $1000 ~ $1FFF  *     Pattern Table 1 : 4KB       *
*****************************************************
*  $2000 ~ $23BF  *     Name Table 0 : 960B         *
*****************************************************
*  $23C0 ~ $23FF  *     Attribute Table 0 : 64B     *
*****************************************************
*  $2700 ~ $27BF  *     Name Table 1 : 960B         *
*****************************************************
*  $27C0 ~ $27FF  *     Attribute Table 1 : 64B     *
*****************************************************

"""

from cpu import Cpu6502
from ppu import Ppu2c02
from cartridge import Cartridge


class Bus:
    def __init__(self):
        self.__nSystemClockCounter = 0
        self.cpuRam = [0 for i in range(2 * 1024)]  # $0000 ~ $07FF NES 2KB RAM
        self.ppu = Ppu2c02()
        self.cpu = Cpu6502()
        self.cpu.connectBus(self)
        self.__cart = None
        self.__bCartInserted = False

        self.dma_page = 0x00
        self.dma_addr = 0x00
        self.dma_data = 0x00

        self.dma_dummy = True
        self.dma_transfer = False

    def cpuWrite(self, addr: int, data: int):
        if self.__cart.cpuWrite(addr, data):
            pass
        elif 0 < addr < 0x1fff:
            # 8KB [$0000~$1FFF]: 2KB Ram and 3 * 2KB Mirror Ram
            self.cpuRam[addr & 0x07ff] = data
        elif 0x2000 <= addr <= 0x3fff:
            # 8KB [$2000~$3FFF]: 1024 Mirror * 8B PPU Resister
            self.ppu.cpuWrite(addr & 0x0007, data)

    def cpuRead(self, addr: int, readonly: bool) -> int:
        bCartRead, data = self.__cart.cpuRead(addr, readonly)
        if bCartRead:
            pass
        elif 0 < addr < 0x1fff:
            # 8KB [$0000~$1FFF]: 2KB Ram and 3 * 2KB Mirror Ram
            data = self.cpuRam[addr & 0x07ff]
        elif 0x2000 <= addr <= 0x3fff:
            # 8KB [$2000~$3FFF]: 1024 Mirror * 8B PPU Resister
            data = self.ppu.cpuRead(addr & 0x0007, readonly)
        return data

    def insertCartridge(self, cart: Cartridge):
        self.__cart = cart
        self.ppu.connectCart(self.__cart)
        self.__bCartInserted = True

    def reset(self):
        self.__cart.reset()
        self.cpu.reset()
        self.ppu.reset()
        self.__nSystemClockCounter = 0
        self.dma_page = 0x00
        self.dma_addr = 0x00
        self.dma_data = 0x00
        self.dma_dummy = True
        self.dma_transfer = False

    def clock(self):
        self.ppu.clock()
        if self.__nSystemClockCounter % 3 == 0:
            if self.dma_transfer:
                if self.dma_dummy:
                    if self.__nSystemClockCounter % 2 == 1:
                        self.dma_dummy = False
                else:
                    if self.__nSystemClockCounter % 2 == 0:
                        self.dma_data = self.cpuRead(self.dma_page << 8 | self.dma_addr, False)
                    else:
                        self.ppu.OAM[self.dma_addr] = self.dma_data
                        self.dma_addr += 1
                        if self.dma_addr == 0x00:
                            self.dma_transfer = False
                            self.dma_dummy = True
            else:
                self.cpu.clock()

        if self.ppu.nmi:
            self.ppu.nmi = False
            self.cpu.nmi()

        if self.__cart.GetMapper().irqState():
            self.__cart.GetMapper().irqClear()
            self.cpu.irq()

        self.__nSystemClockCounter += 1
