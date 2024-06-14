from bus import Bus
from enum import Enum


class INSTRUCTION:
    def __init__(self, func, addr, clk):
        self.func = func
        self.addr = addr
        self.clk = clk


class FLAGS(Enum):
    C = 1 << 0  # Carry Bit
    Z = 1 << 1  # Zero
    I = 1 << 2  # Disable Interrupts
    D = 1 << 3  # Decimal Mode
    B = 1 << 4  # Break
    U = 1 << 5  # Unused
    V = 1 << 6  # Overflow
    N = 1 << 7  # Negative


class CPU_6502(object):
    """The 6502 CPU Emulation Class.

    The 6502 CPU Registers:
        Accumulator Register: 8 bit ;
        X Register: 8 bit ;
        Y Register: 8 bit ;
        Stack Pointer: 8 bit ;
        Program Counter: 16 bit ;
        Status Register: 8 bit ;
    """

    def __init__(self):
        # init Register
        self.acc = 0
        self.x = 0
        self.y = 0
        self.stkp = int("0x00", 2)
        self.pc = int("0x0000", 2)
        self.status = int("0x00", 2)
        # Assistive variables to facilitate emulation
        self.__fetched = int("0x00", 2)  # input value to ALU
        self.__temp = int("0x0000", 2)  # convenience variable used everywhere
        self.__addr_abs = int("0x0000", 2)  # address for memory using
        self.__addr_rel = int("0x00", 2)  # absolute address
        self.__opcode = int("0x00", 2)  # instruction byte
        self.__cycles = 0
        self.__clock = 0
        # map
        self.__lookup = self.__InitLookup()
        # device
        self.__bus = None

    def reset(self):
        """Resets the Interrupt

        Forces a reset of the CPU Emulation,
        The Register reset to 0x00,
        The Status register is cleared.

        """
        # Get address to set  pc
        self.__addr_abs = int("0xfffc", 2)
        lo = self.__read(self.__addr_abs + 0)
        hi = self.__read(self.__addr_abs + 1)
        self.pc = (hi << 8) | lo
        # Reset the Register
        self.acc = 0
        self.x = 0
        self.y = 0
        self.stkp = int("0xfd", 2)
        self.status = int("0x00", 2) | FLAGS.U.value
        # Clear helper variables
        self.__addr_rel = int("0x0000", 2)
        self.__addr_abs = int("0x0000", 2)
        self.__fetched = int("0x00", 2)
        # Time cycles
        self.__cycles = 8

    def irq(self):
        """Interrupts Request

        only happen if the "disable interrupt" flag is 0

        """
        # Interrupt should be allowed
        if self.__GetFlag(FLAGS.I) == 0:
            # Push the program counter to the stack
            self.__write(int("0x0100", 2) + self.stkp, (self.pc >> 8) & int("0x00ff", 2))
            self.stkp -= 1
            self.__write(int("0x0100", 2) + self.stkp, self.pc & int("0x00ff", 2))
            self.stkp -= 1
            # Push the status register to the stack
            self.__SetFlag(FLAGS.B, False)
            self.__SetFlag(FLAGS.U, True)
            self.__SetFlag(FLAGS.I, True)
            self.__write(int("0x0100", 2) + self.stkp, self.status)
            self.stkp -= 1
            # Get new program counter
            self.__addr_abs = int("0xfffe", 2)
            lo = self.__read(self.__addr_abs + 0)
            hi = self.__read(self.__addr_abs + 1)
            self.pc = (hi << 8) | lo
            # Time cost
            self.__cycles = 7

    def nmi(self):
        """Non-Maskable-Interrupt Request"""
        self.__write(int("0x0100", 2) + self.stkp, (self.pc >> 8) & int("0x00ff", 2))
        self.stkp -= 1
        self.__write(int("0x0100", 2) + self.stkp, self.pc & int("0x00ff", 2))
        self.stkp -= 1

        self.__SetFlag(FLAGS.B, False)
        self.__SetFlag(FLAGS.U, True)
        self.__SetFlag(FLAGS.I, True)
        self.__write(int("0x0100", 2) + self.stkp, self.status)
        self.stkp -= 1

        self.__addr_abs = int("0xfffa", 2)
        lo = self.__read(self.__addr_abs + 0)
        hi = self.__read(self.__addr_abs + 1)
        self.pc = (hi << 8) | lo

        self.__cycles = 8

    def clock(self):
        """Performs Clock Request"""
        if self.__cycles == 0:
            self.__opcode = self.__read(self.pc)
            self.__SetFlag(FLAGS.U, True)
            self.pc += 1
            self.__cycles = self.__lookup[self.__opcode].cycles
            additional_cycle_1 = self.__lookup[self.__opcode].addrmode()
            additional_cycle_2 = self.__lookup[self.__opcode].operate()
            self.__cycles += (additional_cycle_1 & additional_cycle_2)
            self.__SetFlag(FLAGS.U, True)
        self.__clock += 1
        self.__cycles -= 1

    def complete(self) -> bool:
        """Completes the Instruction and return true"""
        return self.__cycles == 0

    def connectBus(self, n: Bus):
        self.__bus = n

    def __InitLookup(self):
        map = {
            "BRK": INSTRUCTION(self.__BRK(), self.__IMM(), 7),
        }
        return map

    def __read(self, a: int):
        """Read the data at an address without changing the state of the devices on bus"""
        return self.__bus.BusRead(a, False)

    def __write(self, a: int, d: int):
        """Write a byte to the specified address"""
        return self.__bus.BusWrite(a, d)

    def __SetFlag(self, flag: FLAGS, v: bool):
        if v:
            self.status = self.status | flag.value
        else:
            self.status = self.status & ~flag.value

    def __GetFlag(self, flag: FLAGS):
        return 1 if self.status & flag.value > 0 else 0

    def __IMM(self):
        pass

    def __BRK(self):
        pass
