import ppu
from cpu import Cpu6502
from ppu import Ppu2c02
from cartridge import Cartridge
from utils import hex2int


class Bus:
    def __init__(self):
        self.__nSystemClockCounter = 0
        # 2 kb ram for cpu
        self.cpuRam = [0 for i in range(2 * 1024)]
        self.ppu = Ppu2c02()
        self.cpu = Cpu6502()
        self.cpu.connectBus(self)
        # self.cart = None

    def cpuWrite(self, addr: int, data: int):
        if self.cart.cpuWrite(addr, data):
            pass
        elif 0 < addr < hex2int("0x1fff"):
            self.cpuRam[addr & hex2int("0x07ff")] = data
        elif hex2int("0x2000") <= addr <= hex2int("0x3fff"):
            self.ppu.cpuWrite(addr & hex2int("0x0007"), data)
        else:
            print("Address: {} out of range".format(addr))

    def cpuRead(self, addr: int, readonly: bool) -> int:
        data = 0
        if self.cart.cpuRead(addr, data):
            pass
        elif 0 < addr < hex2int("0x1fff"):
            data = self.cpuRam[addr & hex2int("0x07ff")]
        elif hex2int("0x2000") <= addr <= hex2int("0x3fff"):
            data = ppu.read(addr & hex2int("0x0007"), readonly)
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
