from enum import Enum


class INSTRUCTION:
    def __init__(self, operate, addrmode, cycles: int):
        self.operate = operate
        self.addrmode = addrmode
        self.cycles = cycles


class FLAGS(Enum):
    C = 1 << 0  # Carry Bit
    Z = 1 << 1  # Zero
    I = 1 << 2  # Disable Interrupts
    D = 1 << 3  # Decimal Mode
    B = 1 << 4  # Break
    U = 1 << 5  # Unused
    V = 1 << 6  # Overflow
    N = 1 << 7  # Negative


def hex2int(x):
    return int(x, 16)


class Cpu6502(object):
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
        self.stkp = hex2int("0x00")
        self.pc = hex2int("0x0000")
        self.status = hex2int("0x00")
        # Assistive variables to facilitate emulation
        self.__fetched = hex2int("0x00")  # input value to ALU
        self.__temp = hex2int("0x0000")  # convenience variable used everywhere
        self.__addr_abs = hex2int("0x0000")  # address for memory using
        self.__addr_rel = hex2int("0x00")  # absolute address
        self.__opcode = hex2int("0x00")  # instruction byte
        self.__cycles = 0
        self.__clock = 0
        # Map
        self.__lookup = self.__InitLookup()
        # Device
        self.__bus = None

    def reset(self):
        """Resets the Interrupt

        Forces a reset of the CPU Emulation,
        The Register reset to 0x00,
        The Status register is cleared.

        """
        # Get address to set  pc
        self.__addr_abs = hex2int("0xfffc")
        lo = self.__read(self.__addr_abs + 0)
        hi = self.__read(self.__addr_abs + 1)
        self.pc = (hi << 8) | lo
        # Reset the Register
        self.acc = 0
        self.x = 0
        self.y = 0
        self.stkp = hex2int("0xfd")
        self.status = hex2int("0x00") | FLAGS.U.value
        # Clear helper variables
        self.__addr_rel = hex2int("0x0000")
        self.__addr_abs = hex2int("0x0000")
        self.__fetched = hex2int("0x00")
        # Time cycles
        self.__cycles = 8

    def irq(self):
        """Interrupts Request

        only happen if the "disable interrupt" flag is 0

        """
        # Interrupt should be allowed
        if self.__GetFlag(FLAGS.I) == 0:
            # Push the program counter to the stack
            self.__write(hex2int("0x0100") + self.stkp, (self.pc >> 8) & hex2int("0x00ff"))
            self.stkp -= 1
            self.__write(hex2int("0x0100") + self.stkp, self.pc & hex2int("0x00ff"))
            self.stkp -= 1
            # Push the status register to the stack
            self.__SetFlag(FLAGS.B, False)
            self.__SetFlag(FLAGS.U, True)
            self.__SetFlag(FLAGS.I, True)
            self.__write(hex2int("0x0100") + self.stkp, self.status)
            self.stkp -= 1
            # Get new program counter
            self.__addr_abs = hex2int("0xfffe")
            lo = self.__read(self.__addr_abs + 0)
            hi = self.__read(self.__addr_abs + 1)
            self.pc = (hi << 8) | lo
            # Time cost
            self.__cycles = 7

    def nmi(self):
        """Non-Maskable-Interrupt Request"""
        self.__write(hex2int("0x0100") + self.stkp, (self.pc >> 8) & hex2int("0x00ff"))
        self.stkp -= 1
        self.__write(hex2int("0x0100") + self.stkp, self.pc & hex2int("0x00ff"))
        self.stkp -= 1

        self.__SetFlag(FLAGS.B, False)
        self.__SetFlag(FLAGS.U, True)
        self.__SetFlag(FLAGS.I, True)
        self.__write(hex2int("0x0100") + self.stkp, self.status)
        self.stkp -= 1

        self.__addr_abs = hex2int("0xfffa")
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

    def connectBus(self, n):
        self.__bus = n

    def __read(self, a: int):
        """Read the data at an address without changing the state of the devices on bus"""
        return self.__bus.BusRead(a, False)

    def __write(self, a: int, d: int):
        """Write a byte to the specified address"""
        return self.__bus.BusWrite(a, d)

    def __fetch(self) -> int:
        if not self.__lookup[self.__opcode].addrmode == self.__IMP:
            self.__fetched = self.__read(self.__addr_abs)
        return self.__fetched

    def __SetFlag(self, flag: FLAGS, v: bool):
        if v:
            self.status = self.status | flag.value
        else:
            self.status = self.status & ~flag.value

    def __GetFlag(self, flag: FLAGS):
        return 1 if (self.status & flag.value) > 0 else 0

    def __InitLookup(self):
        instruction_map = {
            "BRK": INSTRUCTION(self.__BRK, self.__IMM, 7),
        }
        return instruction_map

    """Addressing Mode
    
    The 6502 has a variety of addressing modes to access data in memory,
    some are direct and some are indirect etc.
    
    """

    def __IMP(self) -> int:
        self.__fetched = self.acc
        return 0

    def __IMM(self):
        self.pc += 1
        self.__addr_abs = self.pc
        return 0

    def __ZP0(self):
        self.__addr_abs = self.__read(self.pc)
        self.pc += 1
        self.__addr_abs &= hex2int("0x00ff")
        return 0

    def __ZPX(self):
        self.__addr_abs = (self.__read(self.pc) + self.x)
        self.pc += 1
        self.__addr_abs &= hex2int("0x00ff")
        return 0

    def __ZPY(self):
        self.__addr_abs = (self.__read(self.pc) + self.y)
        self.pc += 1
        self.__addr_abs &= hex2int("0x00ff")
        return 0

    def __REL(self):
        self.__addr_rel = self.__read(self.pc)
        self.pc += 1
        if (self.__addr_rel & hex2int("0x80")):
            self.__addr_rel |= hex2int("0xff00")
        return 0

    def __ABS(self):
        lo = self.__read(self.pc)
        self.pc += 1
        hi = self.__read(self.pc)
        self.pc += 1

        self.__addr_abs = (hi << 8) | lo
        return 0

    def __ABX(self):
        lo = self.__read(self.pc)
        self.pc += 1
        hi = self.__read(self.pc)
        self.pc += 1

        self.__addr_abs = (hi << 8) | lo
        self.__addr_abs += self.x

        if (self.__addr_abs & hex2int("0xff00")) != (hi << 8):
            return 1
        else:
            return 0

    def __ABY(self):
        lo = self.__read(self.pc)
        self.pc += 1
        hi = self.__read(self.pc)
        self.pc += 1

        self.__addr_abs = (hi << 8) | lo
        self.__addr_abs += self.y

        if (self.__addr_abs & hex2int("0xff00")) != (hi << 8):
            return 1
        else:
            return 0

    # The next 3 address modes use indirection (aka Pointers!)

    def __IND(self):
        ptr_lo = self.__read(self.pc)
        self.pc += 1
        ptr_hi = self.__read(self.pc)
        self.pc += 1

        ptr = (ptr_hi << 8) | ptr_lo

        if ptr_lo == hex2int("0xff"):
            self.__addr_abs = (self.__read(ptr & hex2int("0xff00")) << 8) | self.__read(ptr + 0)
        else:
            self.__addr_abs = (self.__read(ptr + 1) << 8) | self.__read(ptr + 0)

        return 0

    def __IZX(self):
        t = self.__read(self.pc)
        self.pc += 1
        lo = self.__read((t + self.x) & hex2int("0x00ff"))
        hi = self.__read((t + self.x + 1) & hex2int("0x00ff"))
        self.__addr_abs = (hi << 8) | lo

        return 0

    def __IZY(self):
        t = self.__read(self.pc)
        self.pc += 1
        lo = self.__read(t & hex2int("0x00ff"))
        hi = self.__read((t + 1) & hex2int("0x00ff"))
        self.__addr_abs = (hi << 8) | lo
        self.__addr_abs += self.y

        if (self.__addr_abs & hex2int("0xff00")) != (hi << 8):
            return 1
        else:
            return 0

    """Opcodes
    
    There are 56 "legitimate" opcodes provided by the 6502 CPU.
    
    """

    def __ADC(self):
        self.__fetch()
        self.__temp = self.acc + self.__fetched + self.__GetFlag(FLAGS.C)
        self.__SetFlag(FLAGS.C, self.__temp > 255)
        self.__SetFlag(FLAGS.Z, (self.__temp & hex2int("0x00ff")) == 0)
        self.__SetFlag(FLAGS.V, ((~self.acc ^ self.__fetched) & (self.acc ^ self.__temp) & hex2int("0x0080")) > 0)
        self.__SetFlag(FLAGS.N, (self.__temp & hex2int("0x0080")) > 0)
        self.acc = self.__temp & hex2int("0x00ff")
        return 1

    def __SBC(self):
        self.__fetch()
        value = (self.__fetched) ^ hex2int("0x00ff")
        self.__temp = self.acc + value + self.__GetFlag(FLAGS.C)
        self.__SetFlag(FLAGS.C, self.__temp & hex2int("0xff00") > 0)
        self.__SetFlag(FLAGS.Z, self.__temp & hex2int("0x00ff") == 0)
        self.__SetFlag(FLAGS.V, (self.__temp ^ self.acc) & (self.__temp ^ value) & hex2int("0x0080") > 0)
        self.__SetFlag(FLAGS.N, (self.__temp & hex2int("0x0080")) > 0)
        self.acc = self.__temp & hex2int("0x00ff")
        return 1

    def __AND(self):
        self.__fetch()
        self.acc = self.acc & self.__fetched
        self.__SetFlag(FLAGS.Z, self.acc == hex2int("0x00"))
        self.__SetFlag(FLAGS.N, self.acc & hex2int("0x80") > 0)
        return 1

    def __ASL(self):
        self.__fetch()
        self.__temp = self.__fetched << 1
        self.__SetFlag(FLAGS.C, self.__temp & hex2int("0xff00") > 0)
        self.__SetFlag(FLAGS.Z, self.__temp & hex2int("0x00ff") == 0)
        self.__SetFlag(FLAGS.N, (self.__temp & hex2int("0x0080")) > 0)
        if self.__lookup[self.__opcode].addrmode == self.__IMP:
            self.acc = self.__temp & hex2int("0x00ff")
        else:
            self.__write(self.__addr_abs, self.__temp & hex2int("0x00ff"))
        return 0

    def __BCC(self):
        if self.__GetFlag(FLAGS.C) == 0:
            self.__cycles += 1
            self.__addr_abs = self.pc + self.__addr_rel

            if self.__addr_abs & hex2int("0xff00") != (self.pc & hex2int("0xff00")):
                self.__cycles += 1
            self.pc = self.__addr_abs
        return 0

    def __BCS(self):
        if self.__GetFlag(FLAGS.C) == 1:
            self.__cycles += 1
            self.__addr_abs = self.pc + self.__addr_rel
            if self.__addr_abs & hex2int("0xff00") != (self.pc & hex2int("0xff00")):
                self.__cycles += 1
            self.pc = self.__addr_abs
        return 0

    def __BEQ(self):
        if self.__GetFlag(FLAGS.Z) == 1:
            self.__cycles += 1
            self.__addr_abs = self.pc + self.__addr_rel
            if (self.__addr_abs & hex2int("0xff00")) != (self.pc & hex2int("0xff00")):
                self.__cycles += 1
            self.pc = self.__addr_abs
        return 0

    def __BIT(self):
        self.__fetch()
        self.__temp = self.acc & self.__fetched
        self.__SetFlag(FLAGS.Z, self.__temp & hex2int("0x00ff") == 0)
        self.__SetFlag(FLAGS.N, self.__fetched & (1 << 7) > 0)
        self.__SetFlag(FLAGS.V, self.__fetched & (1 << 6) > 0)
        return 0

    def __BMI(self):
        if self.__GetFlag(FLAGS.N) == 1:
            self.__cycles += 1
            self.__addr_abs = self.pc + self.__addr_rel
            if (self.__addr_abs & hex2int("0xff00")) != (self.pc & hex2int("0xff00")):
                self.__cycles += 1
            self.pc = self.__addr_abs
        return 0

    def __BNE(self):
        if self.__GetFlag(FLAGS.Z) == 0:
            self.__cycles += 1
            self.__addr_abs = self.pc + self.__addr_rel
            if (self.__addr_abs & hex2int("0xff00")) != (self.pc & hex2int("0xff00")):
                self.__cycles += 1
            self.pc = self.__addr_abs
        return 0

    def __BPL(self):
        if self.__GetFlag(FLAGS.N) == 0:
            self.__cycles += 1
            self.__addr_abs = self.pc + self.__addr_rel
            if (self.__addr_abs & hex2int("0xff00")) != (self.pc & hex2int("0xff00")):
                self.__cycles += 1
            self.pc = self.__addr_abs
        return 0

    def __BRK(self):
        self.pc += 1
        self.__SetFlag(FLAGS.I, True)
        self.__write(hex2int("0x0100") + self.stkp, (self.pc >> 8) & hex2int("0x00ff"))
        self.stkp -= 1
        self.__write(hex2int("0x0100") + self.stkp, self.pc & hex2int("0x00ff"))
        self.stkp -= 1
        self.__SetFlag(FLAGS.B, True)
        self.__write(hex2int("0x0100") + self.stkp, self.status)
        self.stkp -= 1
        self.__SetFlag(FLAGS.B, False)
        self.pc = self.__read(hex2int("0xfffe")) | (self.__read(hex2int("0xffff")) << 8)
        return 0

    def __BVC(self):
        if self.__GetFlag(FLAGS.V) == 0:
            self.__cycles += 1
            self.__addr_abs = self.pc + self.__addr_rel
            if (self.__addr_abs & hex2int("0xff00")) != (self.pc & hex2int("0xff00")):
                self.__cycles += 1
            self.pc = self.__addr_abs
        return 0

    def __BVS(self):
        if self.__GetFlag(FLAGS.V) == 1:
            self.__cycles += 1
            self.__addr_abs = self.pc + self.__addr_rel
            if (self.__addr_abs & hex2int("0xff00")) != (self.pc & hex2int("0xff00")):
                self.__cycles += 1
            self.pc = self.__addr_abs
        return 0

    def __CLC(self):
        self.__SetFlag(FLAGS.C, False)
        return 0

    def __CLD(self):
        self.__SetFlag(FLAGS.D, False)
        return 0

    def __CLI(self):
        self.__SetFlag(FLAGS.I, False)
        return 0

    def __CLV(self):
        self.__SetFlag(FLAGS.V, False)
        return 0

    def __CMP(self):
        self.__fetch()
        self.__temp = self.acc - self.__fetched
        self.__SetFlag(FLAGS.C, self.acc >= self.__fetched)
        self.__SetFlag(FLAGS.Z, (self.__temp & hex2int("0x00ff")) == 0)
        self.__SetFlag(FLAGS.N, self.__temp & hex2int("0x0080") > 0)
        return 1

    def __CPX(self):
        self.__fetch()
        self.__temp = self.x - self.__fetched
        self.__SetFlag(FLAGS.C, self.x >= self.__fetched)
        self.__SetFlag(FLAGS.Z, (self.__temp & hex2int("0x00ff")) == 0)
        self.__SetFlag(FLAGS.N, self.__temp & hex2int("0x0080") > 0)
        return 0

    def __CPY(self):
        self.__fetch()
        self.__temp = self.y - self.__fetched
        self.__SetFlag(FLAGS.C, self.y >= self.__fetched)
        self.__SetFlag(FLAGS.Z, (self.__temp & hex2int("0x00ff")) == 0)
        self.__SetFlag(FLAGS.N, self.__temp & hex2int("0x0080") > 0)
        return 0

    def __DEC(self):
        self.__fetch()
        self.__temp = self.__fetched - 1
        self.__write(self.__addr_abs, self.__temp & hex2int("0x00ff"))
        self.__SetFlag(FLAGS.Z, (self.__temp & hex2int("0x00ff")) == 0)
        self.__SetFlag(FLAGS.N, self.__temp & hex2int("0x0080") > 0)
        return 0

    def __DEX(self):
        self.x -= 1
        self.__SetFlag(FLAGS.Z, self.x == hex2int("0x00"))
        self.__SetFlag(FLAGS.N, self.x & hex2int("0x80") > 0)
        return 0

    def __DEY(self):
        self.y -= 1
        self.__SetFlag(FLAGS.Z, self.y == hex2int("0x00"))
        self.__SetFlag(FLAGS.N, self.y & hex2int("0x00") > 0)
        return 0

    def __EOR(self):
        self.__fetch()
        self.acc ^= self.__fetched
        self.__SetFlag(FLAGS.Z, self.acc == hex2int("0x00"))
        self.__SetFlag(FLAGS.N, self.acc & hex2int("0x80") > 0)
        return 0

    def __INC(self):
        self.__fetch()
        self.__temp = self.__fetched + 1
        self.__write(self.__addr_abs, self.__temp & hex2int("0x00ff"))
        self.__SetFlag(FLAGS.Z, self.__temp & hex2int("0x00ff") == hex2int("0x0000"))
        self.__SetFlag(FLAGS.N, self.__temp & hex2int("0x0080") > 0)
        return 0

    def __INX(self):
        self.x += 1
        self.__SetFlag(FLAGS.Z, self.x == hex2int("0x00"))
        self.__SetFlag(FLAGS.N, self.x & hex2int("0x80") > 0)
        return 0

    def __INY(self):
        self.y += 1
        self.__SetFlag(FLAGS.Z, self.y == hex2int("0x00"))
        self.__SetFlag(FLAGS.N, self.y & hex2int("0x80") > 0)
        return 0

    def __JMP(self):
        self.pc = self.__addr_abs
        return 0

    def __JSR(self):
        self.pc -= 1
        self.__write(hex2int("0x0100") + self.stkp, (self.pc >> 8) & hex2int("0x00ff"))
        self.stkp -= 1
        self.__write(hex2int("0x0100") + self.stkp, self.pc & hex2int("0x00ff"))
        self.stkp -= 1
        self.pc = self.__addr_abs
        return 0

    def __LDA(self):
        self.__fetch()
        self.acc = self.__fetched
        self.__SetFlag(FLAGS.Z, self.acc == hex2int("0x00"))
        self.__SetFlag(FLAGS.N, self.acc & hex2int("0x80") > 0)
        return 1

    def __LDX(self):
        self.__fetch()
        self.x = self.__fetched
        self.__SetFlag(FLAGS.Z, self.x == hex2int("0x00"))
        self.__SetFlag(FLAGS.N, self.x & hex2int("0x80") > 0)
        return 1

    def __LDY(self):
        self.__fetch()
        self.y = self.__fetched
        self.__SetFlag(FLAGS.Z, self.y == hex2int("0x00"))
        self.__SetFlag(FLAGS.N, self.y & hex2int("0x80") > 0)
        return 1

    def __LSR(self):
        self.__fetch()
        self.__SetFlag(FLAGS.C, self.__fetched & hex2int("0x0001") > 0)
        self.__temp = self.__fetched >> 1
        self.__SetFlag(FLAGS.Z, self.__temp & hex2int("0x00ff") == 0)
        self.__SetFlag(FLAGS.N, self.__temp & hex2int("0x0080") > 0)
        if self.__lookup[self.__opcode].addrmode == self.__IMP:
            self.acc = self.__temp & hex2int("0x00ff")
        else:
            self.__write(self.__addr_abs, self.__temp & hex2int("0x00ff"))
        return 0

    def __NOP(self):
        if self.__opcode == hex2int("0xfc"):
            return 1
        else:
            return 0

    def __ORA(self):
        self.__fetch()
        self.acc |= self.__fetched
        self.__SetFlag(FLAGS.Z, self.acc == hex2int("0x00"))
        self.__SetFlag(FLAGS.N, self.acc & hex2int("0x80") > 0)
        return 1

    def __PHA(self):
        self.__write(hex2int("0x0100") + self.stkp, self.acc)
        self.stkp -= 1
        return 0

    def __PHP(self):
        self.__write(hex2int("0x0100") + self.stkp, self.status | FLAGS.B.value | FLAGS.U.value)
        self.__SetFlag(FLAGS.B, False)
        self.__SetFlag(FLAGS.U, False)
        self.stkp -= 1
        return 0

    def __PLA(self):
        self.stkp += 1
        self.acc = self.__read(hex2int("0x0100") + self.stkp)
        self.__SetFlag(FLAGS.Z, self.acc == hex2int("0x00"))
        self.__SetFlag(FLAGS.N, self.acc & hex2int("0x80") > 0)
        return 0

    def __PLP(self):
        self.stkp += 1
        self.status = self.__read(hex2int("0x0100") + self.stkp)
        self.__SetFlag(FLAGS.U, True)
        return 0

    def __ROL(self):
        self.__fetch()
        self.__temp = (self.__fetched << 1) | self.__GetFlag(FLAGS.C)
        self.__SetFlag(FLAGS.C, self.__temp & hex2int("0xff00") > 0)
        self.__SetFlag(FLAGS.Z, self.__temp & hex2int("0x00ff") == 0)
        self.__SetFlag(FLAGS.N, self.__temp & hex2int("0x0080") > 0)
        if self.__lookup[self.__opcode].addrmode == self.__IMP:
            self.acc = self.__temp & hex2int("0x00ff")
        else:
            self.__write(self.__addr_abs, self.__temp & hex2int("0x00ff"))
        return 0

    def __ROR(self):
        self.__fetch()
        self.__temp = (self.__GetFlag(FLAGS.C) << 7) | (self.__fetched >> 1)
        self.__SetFlag(FLAGS.C, self.__fetched & hex2int("0x01") > 0)
        self.__SetFlag(FLAGS.Z, self.__temp & hex2int("0x00ff") == 0)
        self.__SetFlag(FLAGS.N, self.__temp & hex2int("0x0080") > 0)
        if self.__lookup[self.__opcode].addrmode == self.__IMP:
            self.acc = self.__temp & hex2int("0x00ff")
        else:
            self.__write(self.__addr_abs, self.__temp & hex2int("0x00ff"))
        return 0

    def __RTI(self):
        self.stkp += 1
        self.status = self.__read(hex2int("0x0100") + self.stkp)
        self.status &= ~FLAGS.B.value
        self.status &= ~FLAGS.U.value
        self.stkp += 1
        self.pc = self.__read(hex2int("0x0100") + self.stkp)
        self.stkp += 1
        self.pc |= self.__read(hex2int("0x0100") + self.stkp) << 8
        return 0

    def __RTS(self):
        self.stkp += 1
        self.pc = self.__read(hex2int("0x0100") + self.stkp)
        self.stkp += 1
        self.pc |= self.__read(hex2int("0x0100") + self.stkp) << 8
        self.pc += 1
        return 0

    def __SEC(self):
        self.__SetFlag(FLAGS.C, True)
        return 0

    def __SED(self):
        self.__SetFlag(FLAGS.D, True)
        return 0

    def __SEI(self):
        self.__SetFlag(FLAGS.I, True)
        return 0

    def __STA(self):
        self.__write(self.__addr_abs, self.acc)
        return 0

    def __STX(self):
        self.__write(self.__addr_abs, self.x)
        return 0

    def __STY(self):
        self.__write(self.__addr_abs, self.y)
        return 0

    def __TAX(self):
        self.x = self.acc
        self.__SetFlag(FLAGS.Z, self.x == hex2int("0x00"))
        self.__SetFlag(FLAGS.N, self.x & hex2int("0x80") > 0)
        return 0

    def __TAY(self):
        self.y = self.acc
        self.__SetFlag(FLAGS.Z, self.y == hex2int("0x00"))
        self.__SetFlag(FLAGS.N, self.y & hex2int("0x80") > 0)
        return 0

    def __TSX(self):
        self.x = self.stkp
        self.__SetFlag(FLAGS.Z, self.x == hex2int("0x00"))
        self.__SetFlag(FLAGS.N, self.x & hex2int("0x80") > 0)
        return 0

    def __TXA(self):
        self.acc = self.x
        self.__SetFlag(FLAGS.Z, self.acc == hex2int("0x00"))
        self.__SetFlag(FLAGS.N, self.acc & hex2int("0x80") > 0)
        return 0

    def __TXS(self):
        self.stkp = self.x
        return 0

    def __TYA(self):
        self.acc = self.y
        self.__SetFlag(FLAGS.Z, self.acc == hex2int("0x00"))
        self.__SetFlag(FLAGS.N, self.acc & hex2int("0x80") > 0)
        return 0

    def __XXX(self):
        return 0

    """disassembly function
    
    This function turns the binary insruction code into human readable form.
    
    """
    def __disassemble(self, nstart:int, nstop:int):
        pass

