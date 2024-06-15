from cpu import *


class Bus:
    def __init__(self):
        self.ram = [0 for i in range(64 * 1024)]
        self.cpu = Cpu6502()
        self.cpu.connectBus(self)

    def BusWrite(self, addr: int, data: int):
        if 0 < addr < len(self.ram):
            self.ram[addr] = data
        else:
            print("Address: {} out of range".format(addr))

    def BusRead(self, addr: int, readonly: bool) -> int:
        if 0 < addr < len(self.ram):
            return self.ram[addr]
        else:
            print("Address: {} out of range".format(addr))
            return 0
