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
from utils import hex2int


class Bus:
    def __init__(self):
        self.__nSystemClockCounter = 0
        self.cpuRam = [0 for i in range(2 * 1024)]  # $0000 ~ $07FF NES 2KB RAM
        self.ppu = Ppu2c02()
        self.cpu = Cpu6502()
        self.cpu.connectBus(self)
        self.cart = None

    def cpuWrite(self, addr: int, data: int):
        if self.cart.cpuWrite(addr, data):
            pass
        elif 0 < addr < hex2int("0x1fff"):
            # 8KB [$0000~$1FFF]: 2KB Ram and 3 * 2KB Mirror Ram
            self.cpuRam[addr & hex2int("0x07ff")] = data
        elif hex2int("0x2000") <= addr <= hex2int("0x3fff"):
            # 8KB [$2000~$3FFF]: 1024 Mirror * 8B PPU Resister
            self.ppu.cpuWrite(addr & hex2int("0x0007"), data)
        else:
            print("Address: {} out of range".format(addr))

    def cpuRead(self, addr: int, readonly: bool) -> int:
        data = 0
        if self.cart.cpuRead(addr, data):
            pass
        elif 0 < addr < hex2int("0x1fff"):
            # 8KB [$0000~$1FFF]: 2KB Ram and 3 * 2KB Mirror Ram
            data = self.cpuRam[addr & hex2int("0x07ff")]
        elif hex2int("0x2000") <= addr <= hex2int("0x3fff"):
            # 8KB [$2000~$3FFF]: 1024 Mirror * 8B PPU Resister
            data = self.ppu.cpuRead(addr & hex2int("0x0007"), readonly)
        else:
            print("Address: {} out of range".format(addr))
        return data

    def insertCartridge(self, cart: Cartridge):
        self.cart = cart
        self.ppu.connectCart(self.cart)

    def reset(self):
        self.cpu.reset()
        self.__nSystemClockCounter = 0

    def clock(self):
        self.ppu.clock()
        if self.__nSystemClockCounter % 3 == 0:
            self.cpu.clock()
        self.__nSystemClockCounter += 1
