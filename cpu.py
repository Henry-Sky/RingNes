"""
Author: Henry-Sky <https://github.com/Henry-Sky>
Date: 2024-06-23
"""

from utils import INSTRUCTION, FLAGS


class Cpu6502(object):
    """The 6502 CPU Emulation:

    """

    def __init__(self):
        """CPU Register

        A: The byte-wide register with arithmetic logic unit (ALU), supports using status register.
        X, Y: The byte-wide register for addressing modes, Also be used as loop counters easily.
        PC: The 2-byte Program Counter register, Supports 65536 direct memory locations.
        Stkp: The byte-wide Stack Pointer register.

        """
        self.a = 0x00
        self.x = 0x00
        self.y = 0x00
        self.pc = 0x0000
        self.stkp = 0x00
        self.status = 0b00000000
        # Assistive variables to facilitate emulation
        self.__fetched = 0x00  # input value to ALU
        self.__temp = 0x0000  # convenience variable used everywhere
        self.__addr_abs = 0x0000  # address for memory using
        self.__addr_rel = 0x00  # absolute address
        self.__opcode = 0x00  # instruction byte
        # Clock and Cycle
        self.__cycles = 0
        self.__clock = 0
        # Instruction map
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
        self.__addr_abs = 0xFFFC
        lo = self.__read(self.__addr_abs + 0)
        hi = self.__read(self.__addr_abs + 1)
        # Reset Vector 2-byte from 0xFFFC and 0xFFFD
        self.pc = (hi << 8) | lo
        # Reset the Register
        self.a = 0x00
        self.x = 0x00
        self.y = 0x00
        self.stkp = 0xFD  # Stack: $0x0100 ~ $0x01FF (0x0100 + stkp)
        self.status = (0x00 | FLAGS.U.value)
        # Clear helper variables
        self.__addr_rel = 0x0000
        self.__addr_abs = 0x0000
        self.__fetched = 0x00
        # Time cycles
        self.__cycles = 8

    def irq(self):
        """Interrupts Request:
        only happen if the "disable interrupt" flag is 0
        """
        # Interrupt should be allowed
        if self.__GetFlag(FLAGS.I) == 0:
            # Push the program counter data to the stack
            self.__write(0x0100 + self.stkp, (self.pc >> 8) & 0x00ff)
            self.stkp -= 1
            self.__write(0x0100 + self.stkp, self.pc & 0x00ff)
            self.stkp -= 1
            # Push the status data to the stack
            self.__SetFlag(FLAGS.B, False)
            self.__SetFlag(FLAGS.U, True)
            self.__SetFlag(FLAGS.I, True)
            self.__write(0x0100 + self.stkp, self.status)
            self.stkp -= 1
            # Get new program counter
            self.__addr_abs = 0xFFFE
            lo = self.__read(self.__addr_abs + 0)
            hi = self.__read(self.__addr_abs + 1)
            self.pc = (hi << 8) | lo
            # Time cost
            self.__cycles = 7

    def nmi(self):
        """Non-Maskable-Interrupt:

        """
        # Push program counter to stack
        self.__write(0x0100 + self.stkp, (self.pc >> 8) & 0x00FF)
        self.stkp -= 1
        self.__write(0x0100 + self.stkp, self.pc & 0x00FF)
        self.stkp -= 1
        # update flag
        self.__SetFlag(FLAGS.B, False)
        self.__SetFlag(FLAGS.U, True)
        self.__SetFlag(FLAGS.I, True)
        self.__write(0x0100 + self.stkp, self.status)
        self.stkp -= 1
        # Set new pc
        self.__addr_abs = 0xFFFA
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
        # Update counter per clock
        self.__clock += 1
        self.__cycles -= 1

    def complete(self) -> bool:
        """Completes the Instruction and return true"""
        return self.__cycles == 0

    def connectBus(self, n):
        self.__bus = n

    def __read(self, addr: int):
        """Read the data at an address without changing the state of the devices on bus"""
        return self.__bus.cpuRead(addr, False)

    def __write(self, addr: int, data: int):
        """Write a byte to the specified address"""
        return self.__bus.cpuWrite(addr, data)

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
        instruction_array = [
            INSTRUCTION("BRK", self.__BRK, self.__IMM, 7),  # 0x00
            INSTRUCTION("ORA", self.__ORA, self.__IZX, 6),  # 0x01
            INSTRUCTION("???", self.__XXX, self.__IMP, 2),  # 0x02
            INSTRUCTION("???", self.__XXX, self.__IMP, 8),  # 0x03
            INSTRUCTION("???", self.__NOP, self.__IMP, 3),
            INSTRUCTION("ORA", self.__ORA, self.__ZP0, 3),
            INSTRUCTION("ASL", self.__ASL, self.__ZP0, 5),
            INSTRUCTION("???", self.__XXX, self.__IMP, 5),
            INSTRUCTION("PHP", self.__PHP, self.__IMP, 3),
            INSTRUCTION("ORA", self.__ORA, self.__IMM, 2),
            INSTRUCTION("ASL", self.__ASL, self.__IMP, 2),
            INSTRUCTION("???", self.__XXX, self.__IMP, 2),
            INSTRUCTION("???", self.__NOP, self.__IMP, 4),
            INSTRUCTION("ORA", self.__ORA, self.__ABS, 4),
            INSTRUCTION("ASL", self.__ASL, self.__ABS, 6),
            INSTRUCTION("???", self.__XXX, self.__IMP, 6),
            INSTRUCTION("BPL", self.__BPL, self.__REL, 2),
            INSTRUCTION("ORA", self.__ORA, self.__IZY, 5),
            INSTRUCTION("???", self.__XXX, self.__IMP, 2),
            INSTRUCTION("???", self.__XXX, self.__IMP, 8),
            INSTRUCTION("???", self.__NOP, self.__IMP, 4),
            INSTRUCTION("ORA", self.__ORA, self.__ZPX, 4),
            INSTRUCTION("ASL", self.__ASL, self.__ZPX, 6),
            INSTRUCTION("???", self.__XXX, self.__IMP, 6),
            INSTRUCTION("CLC", self.__CLC, self.__IMP, 2),
            INSTRUCTION("ORA", self.__ORA, self.__ABY, 4),
            INSTRUCTION("???", self.__NOP, self.__IMP, 2),
            INSTRUCTION("???", self.__XXX, self.__IMP, 7),
            INSTRUCTION("???", self.__NOP, self.__IMP, 4),
            INSTRUCTION("ORA", self.__ORA, self.__ABX, 4),
            INSTRUCTION("ASL", self.__ASL, self.__ABX, 7),
            INSTRUCTION("???", self.__XXX, self.__IMP, 7),
            INSTRUCTION("JSR", self.__JSR, self.__ABS, 6),
            INSTRUCTION("AND", self.__AND, self.__IZX, 6),
            INSTRUCTION("???", self.__XXX, self.__IMP, 2),
            INSTRUCTION("???", self.__XXX, self.__IMP, 8),
            INSTRUCTION("BIT", self.__BIT, self.__ZP0, 3),
            INSTRUCTION("AND", self.__AND, self.__ZP0, 3),
            INSTRUCTION("ROL", self.__ROL, self.__ZP0, 5),
            INSTRUCTION("???", self.__XXX, self.__IMP, 5),
            INSTRUCTION("PLP", self.__PLP, self.__IMP, 4),
            INSTRUCTION("AND", self.__AND, self.__IMM, 2),
            INSTRUCTION("ROL", self.__ROL, self.__IMP, 2),
            INSTRUCTION("???", self.__XXX, self.__IMP, 2),
            INSTRUCTION("BIT", self.__BIT, self.__ABS, 4),
            INSTRUCTION("AND", self.__AND, self.__ABS, 4),
            INSTRUCTION("ROL", self.__ROL, self.__ABS, 6),
            INSTRUCTION("???", self.__XXX, self.__IMP, 6),
            INSTRUCTION("BMI", self.__BMI, self.__REL, 2),
            INSTRUCTION("AND", self.__AND, self.__IZY, 5),
            INSTRUCTION("???", self.__XXX, self.__IMP, 2),
            INSTRUCTION("???", self.__XXX, self.__IMP, 8),
            INSTRUCTION("???", self.__NOP, self.__IMP, 4),
            INSTRUCTION("AND", self.__AND, self.__ZPX, 4),
            INSTRUCTION("ROL", self.__ROL, self.__ZPX, 6),
            INSTRUCTION("???", self.__XXX, self.__IMP, 6),
            INSTRUCTION("SEC", self.__SEC, self.__IMP, 2),
            INSTRUCTION("AND", self.__AND, self.__ABY, 4),
            INSTRUCTION("???", self.__NOP, self.__IMP, 2),
            INSTRUCTION("???", self.__XXX, self.__IMP, 7),
            INSTRUCTION("???", self.__NOP, self.__IMP, 4),
            INSTRUCTION("AND", self.__AND, self.__ABX, 4),
            INSTRUCTION("ROL", self.__ROL, self.__ABX, 7),
            INSTRUCTION("???", self.__XXX, self.__IMP, 7),
            INSTRUCTION("RTI", self.__RTI, self.__IMP, 6),
            INSTRUCTION("EOR", self.__EOR, self.__IZX, 6),
            INSTRUCTION("???", self.__XXX, self.__IMP, 2),
            INSTRUCTION("???", self.__XXX, self.__IMP, 8),
            INSTRUCTION("???", self.__NOP, self.__IMP, 3),
            INSTRUCTION("EOR", self.__EOR, self.__ZP0, 3),
            INSTRUCTION("LSR", self.__LSR, self.__ZP0, 5),
            INSTRUCTION("???", self.__XXX, self.__IMP, 5),
            INSTRUCTION("PHA", self.__PHA, self.__IMP, 3),
            INSTRUCTION("EOR", self.__EOR, self.__IMM, 2),
            INSTRUCTION("LSR", self.__LSR, self.__IMP, 2),
            INSTRUCTION("???", self.__XXX, self.__IMP, 2),
            INSTRUCTION("JMP", self.__JMP, self.__ABS, 3),
            INSTRUCTION("EOR", self.__EOR, self.__ABS, 4),
            INSTRUCTION("LSR", self.__LSR, self.__ABS, 6),
            INSTRUCTION("???", self.__XXX, self.__IMP, 6),
            INSTRUCTION("BVC", self.__BVC, self.__REL, 2),
            INSTRUCTION("EOR", self.__EOR, self.__IZY, 5),
            INSTRUCTION("???", self.__XXX, self.__IMP, 2),
            INSTRUCTION("???", self.__XXX, self.__IMP, 8),
            INSTRUCTION("???", self.__NOP, self.__IMP, 4),
            INSTRUCTION("EOR", self.__EOR, self.__ZPX, 4),
            INSTRUCTION("LSR", self.__LSR, self.__ZPX, 6),
            INSTRUCTION("???", self.__XXX, self.__IMP, 6),
            INSTRUCTION("CLI", self.__CLI, self.__IMP, 2),
            INSTRUCTION("EOR", self.__EOR, self.__ABY, 4),
            INSTRUCTION("???", self.__NOP, self.__IMP, 2),
            INSTRUCTION("???", self.__XXX, self.__IMP, 7),
            INSTRUCTION("???", self.__NOP, self.__IMP, 4),
            INSTRUCTION("EOR", self.__EOR, self.__ABX, 4),
            INSTRUCTION("LSR", self.__LSR, self.__ABX, 7),
            INSTRUCTION("???", self.__XXX, self.__IMP, 7),
            INSTRUCTION("RTS", self.__RTS, self.__IMP, 6),
            INSTRUCTION("ADC", self.__ADC, self.__IZX, 6),
            INSTRUCTION("???", self.__XXX, self.__IMP, 2),
            INSTRUCTION("???", self.__XXX, self.__IMP, 8),
            INSTRUCTION("???", self.__NOP, self.__IMP, 3),
            INSTRUCTION("ADC", self.__ADC, self.__ZP0, 3),
            INSTRUCTION("ROR", self.__ROR, self.__ZP0, 5),
            INSTRUCTION("???", self.__XXX, self.__IMP, 5),
            INSTRUCTION("PLA", self.__PLA, self.__IMP, 4),
            INSTRUCTION("ADC", self.__ADC, self.__IMM, 2),
            INSTRUCTION("ROR", self.__ROR, self.__IMP, 2),
            INSTRUCTION("???", self.__XXX, self.__IMP, 2),
            INSTRUCTION("JMP", self.__JMP, self.__IND, 5),
            INSTRUCTION("ADC", self.__ADC, self.__ABS, 4),
            INSTRUCTION("ROR", self.__ROR, self.__ABS, 6),
            INSTRUCTION("???", self.__XXX, self.__IMP, 6),
            INSTRUCTION("BVS", self.__BVS, self.__REL, 2),
            INSTRUCTION("ADC", self.__ADC, self.__IZY, 5),
            INSTRUCTION("???", self.__XXX, self.__IMP, 2),
            INSTRUCTION("???", self.__XXX, self.__IMP, 8),
            INSTRUCTION("???", self.__NOP, self.__IMP, 4),
            INSTRUCTION("ADC", self.__ADC, self.__ZPX, 4),
            INSTRUCTION("ROR", self.__ROR, self.__ZPX, 6),
            INSTRUCTION("???", self.__XXX, self.__IMP, 6),
            INSTRUCTION("SEI", self.__SEI, self.__IMP, 2),
            INSTRUCTION("ADC", self.__ADC, self.__ABY, 4),
            INSTRUCTION("???", self.__NOP, self.__IMP, 2),
            INSTRUCTION("???", self.__XXX, self.__IMP, 7),
            INSTRUCTION("???", self.__NOP, self.__IMP, 4),
            INSTRUCTION("ADC", self.__ADC, self.__ABX, 4),
            INSTRUCTION("ROR", self.__ROR, self.__ABX, 7),
            INSTRUCTION("???", self.__XXX, self.__IMP, 7),
            INSTRUCTION("???", self.__NOP, self.__IMP, 2),
            INSTRUCTION("STA", self.__STA, self.__IZX, 6),
            INSTRUCTION("???", self.__NOP, self.__IMP, 2),
            INSTRUCTION("???", self.__XXX, self.__IMP, 6),
            INSTRUCTION("STY", self.__STY, self.__ZP0, 3),
            INSTRUCTION("STA", self.__STA, self.__ZP0, 3),
            INSTRUCTION("STX", self.__STX, self.__ZP0, 3),
            INSTRUCTION("???", self.__XXX, self.__IMP, 3),
            INSTRUCTION("DEY", self.__DEY, self.__IMP, 2),
            INSTRUCTION("???", self.__NOP, self.__IMP, 2),
            INSTRUCTION("TXA", self.__TXA, self.__IMP, 2),
            INSTRUCTION("???", self.__XXX, self.__IMP, 2),
            INSTRUCTION("STY", self.__STY, self.__ABS, 4),
            INSTRUCTION("STA", self.__STA, self.__ABS, 4),
            INSTRUCTION("STX", self.__STX, self.__ABS, 4),
            INSTRUCTION("???", self.__XXX, self.__IMP, 4),
            INSTRUCTION("BCC", self.__BCC, self.__REL, 2),
            INSTRUCTION("STA", self.__STA, self.__IZY, 6),
            INSTRUCTION("???", self.__XXX, self.__IMP, 2),
            INSTRUCTION("???", self.__XXX, self.__IMP, 6),
            INSTRUCTION("STY", self.__STY, self.__ZPX, 4),
            INSTRUCTION("STA", self.__STA, self.__ZPX, 4),
            INSTRUCTION("STX", self.__STX, self.__ZPY, 4),
            INSTRUCTION("???", self.__XXX, self.__IMP, 4),
            INSTRUCTION("TYA", self.__TYA, self.__IMP, 2),
            INSTRUCTION("STA", self.__STA, self.__ABY, 5),
            INSTRUCTION("TXS", self.__TXS, self.__IMP, 2),
            INSTRUCTION("???", self.__XXX, self.__IMP, 5),
            INSTRUCTION("???", self.__NOP, self.__IMP, 5),
            INSTRUCTION("STA", self.__STA, self.__ABX, 5),
            INSTRUCTION("???", self.__XXX, self.__IMP, 5),
            INSTRUCTION("???", self.__XXX, self.__IMP, 5),
            INSTRUCTION("LDY", self.__LDY, self.__IMM, 2),
            INSTRUCTION("LDA", self.__LDA, self.__IZX, 6),
            INSTRUCTION("LDX", self.__LDX, self.__IMM, 2),
            INSTRUCTION("???", self.__XXX, self.__IMP, 6),
            INSTRUCTION("LDY", self.__LDY, self.__ZP0, 3),
            INSTRUCTION("LDA", self.__LDA, self.__ZP0, 3),
            INSTRUCTION("LDX", self.__LDX, self.__ZP0, 3),
            INSTRUCTION("???", self.__XXX, self.__IMP, 3),
            INSTRUCTION("TAY", self.__TAY, self.__IMP, 2),
            INSTRUCTION("LDA", self.__LDA, self.__IMM, 2),
            INSTRUCTION("TAX", self.__TAX, self.__IMP, 2),
            INSTRUCTION("???", self.__XXX, self.__IMP, 2),
            INSTRUCTION("LDY", self.__LDY, self.__ABS, 4),
            INSTRUCTION("LDA", self.__LDA, self.__ABS, 4),
            INSTRUCTION("LDX", self.__LDX, self.__ABS, 4),
            INSTRUCTION("???", self.__XXX, self.__IMP, 4),
            INSTRUCTION("BCS", self.__BCS, self.__REL, 2),
            INSTRUCTION("LDA", self.__LDA, self.__IZY, 5),
            INSTRUCTION("???", self.__XXX, self.__IMP, 2),
            INSTRUCTION("???", self.__XXX, self.__IMP, 5),
            INSTRUCTION("LDY", self.__LDY, self.__ZPX, 4),
            INSTRUCTION("LDA", self.__LDA, self.__ZPX, 4),
            INSTRUCTION("LDX", self.__LDX, self.__ZPY, 4),
            INSTRUCTION("???", self.__XXX, self.__IMP, 4),
            INSTRUCTION("CLV", self.__CLV, self.__IMP, 2),
            INSTRUCTION("LDA", self.__LDA, self.__ABY, 4),
            INSTRUCTION("TSX", self.__TSX, self.__IMP, 2),
            INSTRUCTION("???", self.__XXX, self.__IMP, 4),
            INSTRUCTION("LDY", self.__LDY, self.__ABX, 4),
            INSTRUCTION("LDA", self.__LDA, self.__ABX, 4),
            INSTRUCTION("LDX", self.__LDX, self.__ABY, 4),
            INSTRUCTION("???", self.__XXX, self.__IMP, 4),
            INSTRUCTION("CPY", self.__CPY, self.__IMM, 2),
            INSTRUCTION("CMP", self.__CMP, self.__IZX, 6),
            INSTRUCTION("???", self.__NOP, self.__IMP, 2),
            INSTRUCTION("???", self.__XXX, self.__IMP, 8),
            INSTRUCTION("CPY", self.__CPY, self.__ZP0, 3),
            INSTRUCTION("CMP", self.__CMP, self.__ZP0, 3),
            INSTRUCTION("DEC", self.__DEC, self.__ZP0, 5),
            INSTRUCTION("???", self.__XXX, self.__IMP, 5),
            INSTRUCTION("INY", self.__INY, self.__IMP, 2),
            INSTRUCTION("CMP", self.__CMP, self.__IMM, 2),
            INSTRUCTION("DEX", self.__DEX, self.__IMP, 2),
            INSTRUCTION("???", self.__XXX, self.__IMP, 2),
            INSTRUCTION("CPY", self.__CPY, self.__ABS, 4),
            INSTRUCTION("CMP", self.__CMP, self.__ABS, 4),
            INSTRUCTION("DEC", self.__DEC, self.__ABS, 6),
            INSTRUCTION("???", self.__XXX, self.__IMP, 6),
            INSTRUCTION("BNE", self.__BNE, self.__REL, 2),
            INSTRUCTION("CMP", self.__CMP, self.__IZY, 5),
            INSTRUCTION("???", self.__XXX, self.__IMP, 2),
            INSTRUCTION("???", self.__XXX, self.__IMP, 8),
            INSTRUCTION("???", self.__NOP, self.__IMP, 4),
            INSTRUCTION("CMP", self.__CMP, self.__ZPX, 4),
            INSTRUCTION("DEC", self.__DEC, self.__ZPX, 6),
            INSTRUCTION("???", self.__XXX, self.__IMP, 6),
            INSTRUCTION("CLD", self.__CLD, self.__IMP, 2),
            INSTRUCTION("CMP", self.__CMP, self.__ABY, 4),
            INSTRUCTION("NOP", self.__NOP, self.__IMP, 2),
            INSTRUCTION("???", self.__XXX, self.__IMP, 7),
            INSTRUCTION("???", self.__NOP, self.__IMP, 4),
            INSTRUCTION("CMP", self.__CMP, self.__ABX, 4),
            INSTRUCTION("DEC", self.__DEC, self.__ABX, 7),
            INSTRUCTION("???", self.__XXX, self.__IMP, 7),
            INSTRUCTION("CPX", self.__CPX, self.__IMM, 2),
            INSTRUCTION("SBC", self.__SBC, self.__IZX, 6),
            INSTRUCTION("???", self.__NOP, self.__IMP, 2),
            INSTRUCTION("???", self.__XXX, self.__IMP, 8),
            INSTRUCTION("CPX", self.__CPX, self.__ZP0, 3),
            INSTRUCTION("SBC", self.__SBC, self.__ZP0, 3),
            INSTRUCTION("INC", self.__INC, self.__ZP0, 5),
            INSTRUCTION("???", self.__XXX, self.__IMP, 5),
            INSTRUCTION("INX", self.__INX, self.__IMP, 2),
            INSTRUCTION("SBC", self.__SBC, self.__IMM, 2),
            INSTRUCTION("NOP", self.__NOP, self.__IMP, 2),
            INSTRUCTION("???", self.__XXX, self.__IMP, 2),
            INSTRUCTION("CPX", self.__CPX, self.__ABS, 4),
            INSTRUCTION("SBC", self.__SBC, self.__ABS, 4),
            INSTRUCTION("INC", self.__INC, self.__ABS, 6),
            INSTRUCTION("???", self.__XXX, self.__IMP, 6),
            INSTRUCTION("BEQ", self.__BEQ, self.__REL, 2),
            INSTRUCTION("SBC", self.__SBC, self.__IZY, 5),
            INSTRUCTION("???", self.__XXX, self.__IMP, 2),
            INSTRUCTION("???", self.__XXX, self.__IMP, 8),
            INSTRUCTION("???", self.__NOP, self.__IMP, 4),
            INSTRUCTION("SBC", self.__SBC, self.__ZPX, 4),
            INSTRUCTION("INC", self.__INC, self.__ZPX, 6),
            INSTRUCTION("???", self.__XXX, self.__IMP, 6),
            INSTRUCTION("SED", self.__SED, self.__IMP, 2),
            INSTRUCTION("SBC", self.__SBC, self.__ABY, 4),
            INSTRUCTION("NOP", self.__NOP, self.__IMP, 2),
            INSTRUCTION("???", self.__XXX, self.__IMP, 7),
            INSTRUCTION("???", self.__NOP, self.__IMP, 4),
            INSTRUCTION("SBC", self.__SBC, self.__ABX, 4),
            INSTRUCTION("INC", self.__INC, self.__ABX, 7),
            INSTRUCTION("???", self.__XXX, self.__IMP, 7)
        ]
        return instruction_array

    """Addressing Mode
    
    The 6502 has a variety of addressing modes to access data in memory,
    some are direct and some are indirect etc.
    
    """

    def __IMP(self) -> int:
        """Implicit Addressing:
        Implied directly by the function of the instruction itself
        :return: 0 cycle
        """
        self.__fetched = self.a
        return 0

    def __IMM(self) -> int:
        """Immediate Addressing:
        Directly specify an 8 bit constant within the instruction.
        :return: 0 cycle
        """
        self.pc += 1
        self.__addr_abs = self.pc
        return 0

    def __ZP0(self) -> int:
        """Zero Page Addressing:
        Using only zero page addressing ($0x0000~$0x00FF, 256B per page)
        :return: 0 cycle
        """
        self.__addr_abs = self.__read(self.pc)
        self.pc += 1
        self.__addr_abs &= 0x00FF
        return 0

    def __ZPX(self) -> int:
        """Zero Page X Addressing:
        Taking the 8 bit zero-page address from the instruction and adding the current value of the X register.
        :return: 0 cycle
        """
        self.__addr_abs = (self.__read(self.pc) + self.x)
        self.pc += 1
        self.__addr_abs &= 0x00FF
        return 0

    def __ZPY(self) -> int:
        """Zero Page Y Addressing:
        Taking the 8 bit zero-page address from the instruction and adding the current value of the Y register.
        :return: 0 cycle
        """
        self.__addr_abs = (self.__read(self.pc) + self.y)
        self.pc += 1
        self.__addr_abs &= 0x00FF
        return 0

    def __REL(self) -> int:
        """Relative Addressing:
        Contain a signed 8 bit relative offset which is added to program counter if the condition is true.
        :return: 0 cycle
        """
        self.__addr_rel = self.__read(self.pc)
        self.pc += 1
        if self.__addr_rel & 0x80:
            self.__addr_rel |= 0xFF00
        return 0

    def __ABS(self) -> int:
        """Absolute Addressing:
        Instructions using absolute addressing contain a full 16-bit address to identify the target location.
        :return: 0 cycle
        """
        lo = self.__read(self.pc)
        self.pc += 1
        hi = self.__read(self.pc)
        self.pc += 1
        self.__addr_abs = (hi << 8) | lo
        return 0

    def __ABX(self) -> int:
        """Absolute X Addressing:
        Taking the 16-bit address from the instruction and added the contents of the X register.
        :return: 0 or 1 cycle
        """
        lo = self.__read(self.pc)
        self.pc += 1
        hi = self.__read(self.pc)
        self.pc += 1
        self.__addr_abs = (hi << 8) | lo
        self.__addr_abs += self.x

        if (self.__addr_abs & 0xFF00) != (hi << 8):
            return 1
        else:
            return 0

    def __ABY(self) -> int:
        """Absolute Y Addressing:
        Taking the 16-bit address from the instruction and added the contents of the Y register.
        :return: 0 or 1 cycle
        """
        lo = self.__read(self.pc)
        self.pc += 1
        hi = self.__read(self.pc)
        self.pc += 1
        self.__addr_abs = (hi << 8) | lo
        self.__addr_abs += self.y

        if (self.__addr_abs & 0xFF00) != (hi << 8):
            return 1
        else:
            return 0

    # The next 3 address modes use indirection (aka Pointers!)

    def __IND(self) -> int:
        """Indirect Addressing:
        Contains a 16-bit address which identifies the location of another 16-bit memory address
        which is the real target of the instruction.
        :return: 0 cycle
        """
        ptr_lo = self.__read(self.pc)
        self.pc += 1
        ptr_hi = self.__read(self.pc)
        self.pc += 1
        ptr = (ptr_hi << 8) | ptr_lo
        # The page problem
        if ptr_lo == 0xFF:
            self.__addr_abs = (self.__read(ptr & 0xFF00) << 8) | self.__read(ptr + 0)
        else:
            self.__addr_abs = (self.__read(ptr + 1) << 8) | self.__read(ptr + 0)
        return 0

    def __IZX(self) -> int:
        """Indirect X Addressing:
        Taken from the instruction and the X register added to it (with zero page wrap around)
        :return: 0 cycle
        """
        tmp = self.__read(self.pc)
        self.pc += 1
        lo = self.__read((tmp + self.x) & 0x00FF)
        hi = self.__read((tmp + self.x + 1) & 0x00FF)
        self.__addr_abs = (hi << 8) | lo
        return 0

    def __IZY(self) -> int:
        """Indirect Y Addressing:
        Taken from the instruction and the Y register added to it (with zero page wrap around)
        :return: 0 or 1 cycle
        """
        tmp = self.__read(self.pc)
        self.pc += 1
        lo = self.__read(tmp & 0x00FF)
        hi = self.__read((tmp + 1) & 0x00FF)
        self.__addr_abs = (hi << 8) | lo
        self.__addr_abs += self.y

        if (self.__addr_abs & 0xFF00) != (hi << 8):
            return 1
        else:
            return 0

    """Opcodes
    There are 56 "legitimate" opcodes provided by the 6502 CPU.
    Thanks to https://www.oxyron.de/html/opcodes02.html
    and https://www.nesdev.org/obelisk-6502-guide/reference.html
    """

    def __ADC(self) -> int:
        """ADC - Add with Carry:
        This instruction adds the contents of a memory location to the accumulator together with the carry bit.
        If overflow occurs the carry bit is set, this enables multiple byte addition to be performed.
        :return: 1 cycle
        """
        self.__fetch()
        self.__temp = self.a + self.__fetched + self.__GetFlag(FLAGS.C)
        self.__SetFlag(FLAGS.C, self.__temp > 255)
        self.__SetFlag(FLAGS.Z, (self.__temp & 0x00ff) == 0)
        self.__SetFlag(FLAGS.V, ((~self.a ^ self.__fetched) & (self.a ^ self.__temp) & 0x0080) > 0)
        self.__SetFlag(FLAGS.N, (self.__temp & 0x0080) > 0)
        self.a = self.__temp & 0x00ff
        return 1

    def __AND(self) -> int:
        """AND - Logical AND:
        A logical AND is performed, bit by bit, on the accumulator contents using the contents of a byte of memory.
        :return: 1 cycle
        """
        self.__fetch()
        self.a = self.a & self.__fetched
        self.__SetFlag(FLAGS.Z, self.a == 0x00)
        self.__SetFlag(FLAGS.N, self.a & 0x80 > 0)
        return 1

    def __SBC(self) -> int:
        """

        :return:
        """
        self.__fetch()
        value = self.__fetched ^ 0x00FF
        self.__temp = self.a + value + self.__GetFlag(FLAGS.C)
        self.__SetFlag(FLAGS.C, self.__temp & 0xFF00 > 0)
        self.__SetFlag(FLAGS.Z, self.__temp & 0x00FF == 0)
        self.__SetFlag(FLAGS.V, (self.__temp ^ self.a) & (self.__temp ^ value) & 0x0080 > 0)
        self.__SetFlag(FLAGS.N, (self.__temp & 0x0080) > 0)
        self.a = self.__temp & 0x00FF
        return 1

    def __ASL(self) -> int:
        """Arithmetic Shift Left:
        This operation shifts all the bits of the accumulator or memory contents one bit left.
        Bit 0 is set to 0 and bit 7 is placed in the carry flag.
        The effect of this operation is to multiply the memory contents by 2 (ignoring 2's complement considerations),
        setting the carry if the result will not fit in 8 bits.
        :return: 0 cycle
        """
        self.__fetch()
        self.__temp = self.__fetched << 1
        self.__SetFlag(FLAGS.C, self.__temp & 0xFF00 > 0)
        self.__SetFlag(FLAGS.Z, self.__temp & 0x00FF == 0)
        self.__SetFlag(FLAGS.N, (self.__temp & 0x0080) > 0)
        if self.__lookup[self.__opcode].addrmode == self.__IMP:
            self.a = self.__temp & 0x00FF
        else:
            self.__write(self.__addr_abs, self.__temp & 0x00FF)
        return 0

    def __BCC(self) -> int:
        """Branch if Carry Clear:
        If the carry flag is clear then add the relative displacement to the program counter to cause a branch to a new location.
        :return: 0 cycle
        """
        if self.__GetFlag(FLAGS.C) == 0:
            self.__cycles += 1
            self.__addr_abs = self.pc + self.__addr_rel

            if (self.__addr_abs & 0xFF00) != (self.pc & 0xFF00):
                self.__cycles += 1
            self.pc = self.__addr_abs
        return 0

    def __BCS(self) -> int:
        """Branch if Carry Set:
        If the carry flag is set then add the relative displacement to the program counter to cause a branch to a new location.
        :return: 0 cycle
        """
        if self.__GetFlag(FLAGS.C) == 1:
            self.__cycles += 1
            self.__addr_abs = self.pc + self.__addr_rel
            if self.__addr_abs & 0xFF00 != (self.pc & 0xFF00):
                self.__cycles += 1
            self.pc = self.__addr_abs
        return 0

    def __BEQ(self) -> int:
        """Branch if Equal:
        If the zero flag is set then add the relative displacement to the program counter to cause a branch to a new location.
        :return: 0 cycle
        """
        if self.__GetFlag(FLAGS.Z) == 1:
            self.__cycles += 1
            self.__addr_abs = self.pc + self.__addr_rel
            if (self.__addr_abs & 0xFF00) != (self.pc & 0xFF00):
                self.__cycles += 1
            self.pc = self.__addr_abs
        return 0

    def __BIT(self) -> int:
        """Bit Test:
        This instructions is used to test if one or more bits are set in a target memory location.
        The mask pattern in A is ANDed with the value in memory to set or clear the zero flag, but the result is not kept.
        Bits 7 and 6 of the value from memory are copied into the N and V flags.
        :return: 0 cycle
        """
        self.__fetch()
        self.__temp = self.a & self.__fetched
        self.__SetFlag(FLAGS.Z, self.__temp & 0x00FF == 0)
        self.__SetFlag(FLAGS.N, self.__fetched & (1 << 7) > 0)
        self.__SetFlag(FLAGS.V, self.__fetched & (1 << 6) > 0)
        return 0

    def __BMI(self) -> int:
        """Branch if Minus:
        If the negative flag is set then add the relative displacement to the program counter to cause a branch to a new location.
        :return: 0 cycle
        """
        if self.__GetFlag(FLAGS.N) == 1:
            self.__cycles += 1
            self.__addr_abs = self.pc + self.__addr_rel
            if (self.__addr_abs & 0xFF00) != (self.pc & 0xFF00):
                self.__cycles += 1
            self.pc = self.__addr_abs
        return 0

    def __BNE(self) -> int:
        """Branch if Not Equal:
        If the zero flag is clear then add the relative displacement to the program counter to cause a branch to a new location.
        :return: 0 cycle
        """
        if self.__GetFlag(FLAGS.Z) == 0:
            self.__cycles += 1
            self.__addr_abs = self.pc + self.__addr_rel
            if (self.__addr_abs & 0xFF00) != (self.pc & 0xFF00):
                self.__cycles += 1
            self.pc = self.__addr_abs
        return 0

    def __BPL(self) -> int:
        """Branch if Positive:
        If the negative flag is clear then add the relative displacement to the program counter to cause a branch to a new location.
        :return: 0 cycle
        """
        if self.__GetFlag(FLAGS.N) == 0:
            self.__cycles += 1
            self.__addr_abs = self.pc + self.__addr_rel
            if (self.__addr_abs & 0xFF00) != (self.pc & 0xFF00):
                self.__cycles += 1
            self.pc = self.__addr_abs
        return 0

    def __BRK(self) -> int:
        """Force Interrupt:
        The BRK instruction forces the generation of an interrupt request.
        The program counter and processor status are pushed on the stack.
        Then the IRQ interrupt vector at $FFFE/F is loaded into the PC and the break flag in the status set to one.
        :return: 0 cycle
        """
        self.pc += 1
        self.__SetFlag(FLAGS.I, True)  # Set the Interrupt flag
        self.__write(0x0100 + self.stkp, (self.pc >> 8) & 0x00FF)
        self.stkp -= 1
        self.__write(0x0100 + self.stkp, self.pc & 0x00FF)
        self.stkp -= 1
        self.__SetFlag(FLAGS.B, True)
        self.__write(0x0100 + self.stkp, self.status)
        self.stkp -= 1
        self.__SetFlag(FLAGS.B, False)
        self.pc = self.__read(0xFFFE) | (self.__read(0xFFFF) << 8)
        return 0

    def __BVC(self) -> int:
        """Branch if Overflow Clear:
        If the overflow flag is clear then add the relative displacement to the program counter to cause a branch to a new location.
        :return: 0 cycle
        """
        if self.__GetFlag(FLAGS.V) == 0:
            self.__cycles += 1
            self.__addr_abs = self.pc + self.__addr_rel
            if (self.__addr_abs & 0xFF00) != (self.pc & 0xFF00):
                self.__cycles += 1
            self.pc = self.__addr_abs
        return 0

    def __BVS(self) -> int:
        """Branch if Overflow Set:
        If the overflow flag is set then add the relative displacement to the program counter to cause a branch to a new location.
        :return: 0 cycle
        """
        if self.__GetFlag(FLAGS.V) == 1:
            self.__cycles += 1
            self.__addr_abs = self.pc + self.__addr_rel
            if (self.__addr_abs & 0xFF00) != (self.pc & 0xFF00):
                self.__cycles += 1
            self.pc = self.__addr_abs
        return 0

    def __CLC(self) -> int:
        """Clear Carry Flag:
        Set the carry flag to zero.
        :return: 0 cycle
        """
        self.__SetFlag(FLAGS.C, False)
        return 0

    def __CLD(self) -> int:
        """Clear Decimal Mode:
        Sets the decimal mode flag to zero.
        :return: 0 cycle
        """
        self.__SetFlag(FLAGS.D, False)
        return 0

    def __CLI(self) -> int:
        """Clear Interrupt Disable:
        Clears the interrupt disable flag allowing normal interrupt requests to be serviced.
        :return: 0 cycle
        """
        self.__SetFlag(FLAGS.I, False)
        return 0

    def __CLV(self) -> int:
        """Clear Overflow Flag:
        Clears the overflow flag.
        :return: 0 cycle
        """
        self.__SetFlag(FLAGS.V, False)
        return 0

    def __CMP(self) -> int:
        """Compare:
        This instruction compares the contents of the accumulator with another memory held value
        and sets the zero and carry flags as appropriate.
        :return: 1 cycle
        """
        self.__fetch()
        self.__temp = self.a - self.__fetched
        self.__SetFlag(FLAGS.C, self.a >= self.__fetched)
        self.__SetFlag(FLAGS.Z, (self.__temp & 0x00FF) == 0)
        self.__SetFlag(FLAGS.N, self.__temp & 0x0080 > 0)
        return 1

    def __CPX(self) -> int:
        """Compare X Register:
        This instruction compares the contents of the X register with another memory held value
        and sets the zero and carry flags as appropriate.
        :return: 0 cycle
        """
        self.__fetch()
        self.__temp = self.x - self.__fetched
        self.__SetFlag(FLAGS.C, self.x >= self.__fetched)
        self.__SetFlag(FLAGS.Z, (self.__temp & 0x00FF) == 0)
        self.__SetFlag(FLAGS.N, self.__temp & 0x0080 > 0)
        return 0

    def __CPY(self) -> int:
        """Compare Y Register:
        This instruction compares the contents of the Y register with another memory held value
        and sets the zero and carry flags as appropriate.
        :return: 0 cycle
        """
        self.__fetch()
        self.__temp = self.y - self.__fetched
        self.__SetFlag(FLAGS.C, self.y >= self.__fetched)
        self.__SetFlag(FLAGS.Z, (self.__temp & 0x00FF) == 0)
        self.__SetFlag(FLAGS.N, self.__temp & 0x0080 > 0)
        return 0

    def __DEC(self) -> int:
        """Decrement Memory:
        Subtracts one from the value held at a specified memory location setting the zero and negative flags as appropriate.
        :return: 0 cycle
        """
        self.__fetch()
        self.__temp = self.__fetched - 1
        self.__write(self.__addr_abs, self.__temp & 0x00FF)
        self.__SetFlag(FLAGS.Z, (self.__temp & 0x00FF) == 0)
        self.__SetFlag(FLAGS.N, self.__temp & 0x0080 > 0)
        return 0

    def __DEX(self) -> int:
        """Decrement X Register:
        Subtracts one from the X register setting the zero and negative flags as appropriate.
        :return: 0 cycle
        """
        self.x -= 1
        self.__SetFlag(FLAGS.Z, self.x == 0x00)
        self.__SetFlag(FLAGS.N, self.x & 0x80 > 0)
        return 0

    def __DEY(self) -> int:
        """Decrement Y Register:
        Subtracts one from the Y register setting the zero and negative flags as appropriate.
        :return: 0 cycle
        """
        self.y -= 1
        self.__SetFlag(FLAGS.Z, self.y == 0x00)
        self.__SetFlag(FLAGS.N, self.y & 0x80 > 0)
        return 0

    def __EOR(self) -> int:
        """Exclusive OR:
        An exclusive OR is performed, bit by bit, on the accumulator contents using the contents of a byte of memory.
        :return: 0 cycle
        """
        self.__fetch()
        self.a ^= self.__fetched
        self.__SetFlag(FLAGS.Z, self.a == 0x00)
        self.__SetFlag(FLAGS.N, self.a & 0x80 > 0)
        return 0

    def __INC(self) -> int:
        """Increment Memory:
        Adds one to the value held at a specified memory location setting the zero and negative flags as appropriate.
        :return: 0 cycle
        """
        self.__fetch()
        self.__temp = self.__fetched + 1
        self.__write(self.__addr_abs, self.__temp & 0x00FF)
        self.__SetFlag(FLAGS.Z, self.__temp & 0x00FF == 0x00)
        self.__SetFlag(FLAGS.N, self.__temp & 0x0080 > 0)
        return 0

    def __INX(self) -> int:
        """Increment X Register:
        Adds one to the X register setting the zero and negative flags as appropriate.
        :return: 0 cycle
        """
        self.x += 1
        self.__SetFlag(FLAGS.Z, self.x == 0x00)
        self.__SetFlag(FLAGS.N, self.x & 0x80 > 0)
        return 0

    def __INY(self) -> int:
        """Increment Y Register:
        Adds one to the Y register setting the zero and negative flags as appropriate.
        :return: 0 cycle
        """
        self.y += 1
        self.__SetFlag(FLAGS.Z, self.y == 0x00)
        self.__SetFlag(FLAGS.N, self.y & 0x80 > 0)
        return 0

    def __JMP(self) -> int:
        """Jump:
        Sets the program counter to the address specified by the operand.
        :return: 0 cycle
        """
        self.pc = self.__addr_abs
        return 0

    def __JSR(self) -> int:
        """Jump to Subroutine:
        The JSR instruction pushes the address (minus one) of the return point on to the stack
        ]and then sets the program counter to the target memory address.
        :return: 0 cycle
        """
        self.pc -= 1
        self.__write(0x0100 + self.stkp, (self.pc >> 8) & 0x00FF)
        self.stkp -= 1
        self.__write(0x0100 + self.stkp, self.pc & 0x00FF)
        self.stkp -= 1
        self.pc = self.__addr_abs
        return 0

    def __LDA(self) -> int:
        """Load Accumulator:
        Loads a byte of memory into the accumulator setting the zero and negative flags as appropriate.
        :return: 0 cycle
        """
        self.__fetch()
        self.a = self.__fetched
        self.__SetFlag(FLAGS.Z, self.a == 0x00)
        self.__SetFlag(FLAGS.N, self.a & 0x80 > 0)
        return 1

    def __LDX(self) -> int:
        """Load X Register:
        Loads a byte of memory into the X register setting the zero and negative flags as appropriate.
        :return: 0 cycle
        """
        self.__fetch()
        self.x = self.__fetched
        self.__SetFlag(FLAGS.Z, self.x == 0x00)
        self.__SetFlag(FLAGS.N, self.x & 0x80 > 0)
        return 1

    def __LDY(self) -> int:
        """Load Y Register:
        Loads a byte of memory into the Y register setting the zero and negative flags as appropriate.
        :return: 0 cycle
        """
        self.__fetch()
        self.y = self.__fetched
        self.__SetFlag(FLAGS.Z, self.y == 0x00)
        self.__SetFlag(FLAGS.N, self.y & 0x80 > 0)
        return 1

    def __LSR(self) -> int:
        """Logical Shift Right:
        Each of the bits in A or M is shift one place to the right.
        The bit that was in bit 0 is shifted into the carry flag. Bit 7 is set to zero.
        :return: 0 cycle
        """
        self.__fetch()
        self.__SetFlag(FLAGS.C, self.__fetched & 0x0001 > 0)
        self.__temp = self.__fetched >> 1
        self.__SetFlag(FLAGS.Z, self.__temp & 0x00FF == 0)
        self.__SetFlag(FLAGS.N, self.__temp & 0x0080 > 0)
        if self.__lookup[self.__opcode].addrmode == self.__IMP:
            self.a = self.__temp & 0x00FF
        else:
            self.__write(self.__addr_abs, self.__temp & 0x00FF)
        return 0

    def __NOP(self) -> int:
        """No Operation:
        The NOP instruction causes no changes to the processor other than the normal incrementing
         of the program counter to the next instruction.
        :return: 0 or 1 cycle
        """
        if self.__opcode == 0xFC:
            return 1
        else:
            return 0

    def __ORA(self) -> int:
        """Logical Inclusive OR:
        An inclusive OR is performed, bit by bit, on the accumulator contents using the contents of a byte of memory.
        :return: 1 cycle
        """
        self.__fetch()
        self.a |= self.__fetched
        self.__SetFlag(FLAGS.Z, self.a == 0x00)
        self.__SetFlag(FLAGS.N, self.a & 0x80 > 0)
        return 1

    def __PHA(self) -> int:
        """Push Accumulator:
        Pushes a copy of the accumulator on to the stack.
        :return: 0 cycle
        """
        self.__write(0x0100 + self.stkp, self.a)
        self.stkp -= 1
        return 0

    def __PHP(self) -> int:
        """Push Processor Status:
        Pushes a copy of the status flags on to the stack.
        :return: 0 cycle
        """
        self.__write(0x0100 + self.stkp, self.status | FLAGS.B.value | FLAGS.U.value)
        self.__SetFlag(FLAGS.B, False)
        self.__SetFlag(FLAGS.U, False)
        self.stkp -= 1
        return 0

    def __PLA(self) -> int:
        """Pull Accumulator:
        Pulls an 8 bit value from the stack and into the accumulator. The zero and negative flags are set as appropriate.
        :return: 0 cycle
        """
        self.stkp += 1
        self.a = self.__read(0x0100 + self.stkp)
        self.__SetFlag(FLAGS.Z, self.a == 0x00)
        self.__SetFlag(FLAGS.N, self.a & 0x80 > 0)
        return 0

    def __PLP(self) -> int:
        """Pull Processor Status:
        Pulls an 8 bit value from the stack and into the processor flags.
        The flags will take on new states as determined by the value pulled.
        :return: 0 cycle
        """
        self.stkp += 1
        self.status = self.__read(0x0100 + self.stkp)
        self.__SetFlag(FLAGS.U, True)
        return 0

    def __ROL(self) -> int:
        """Rotate Left:
        Move each of the bits in either A or M one place to the left.
        Bit 0 is filled with the current value of the carry flag whilst the old bit 7 becomes the new carry flag value.
        :return: 0 cycle
        """
        self.__fetch()
        self.__temp = (self.__fetched << 1) | self.__GetFlag(FLAGS.C)
        self.__SetFlag(FLAGS.C, self.__temp & 0xFF00 > 0)
        self.__SetFlag(FLAGS.Z, self.__temp & 0X00FF == 0)
        self.__SetFlag(FLAGS.N, self.__temp & 0X0080 > 0)
        if self.__lookup[self.__opcode].addrmode == self.__IMP:
            self.a = self.__temp & 0X00FF
        else:
            self.__write(self.__addr_abs, self.__temp & 0X00FF)
        return 0

    def __ROR(self) -> int:
        """Rotate Right:
        Move each of the bits in either A or M one place to the right.
        Bit 7 is filled with the current value of the carry flag whilst the old bit 0 becomes the new carry flag value.
        :return: 0 cycle
        """
        self.__fetch()
        self.__temp = (self.__GetFlag(FLAGS.C) << 7) | (self.__fetched >> 1)
        self.__SetFlag(FLAGS.C, self.__fetched & 0x01 > 0)
        self.__SetFlag(FLAGS.Z, self.__temp & 0x00FF == 0)
        self.__SetFlag(FLAGS.N, self.__temp & 0X0080 > 0)
        if self.__lookup[self.__opcode].addrmode == self.__IMP:
            self.a = self.__temp & 0X00FF
        else:
            self.__write(self.__addr_abs, self.__temp & 0x00FF)
        return 0

    def __RTI(self) -> int:
        """Return from Interrupt:
        The RTI instruction is used at the end of an interrupt processing routine.
        It pulls the processor flags from the stack followed by the program counter.
        :return: 0 cycle
        """
        self.stkp += 1
        self.status = self.__read(0x0100 + self.stkp)
        self.status &= ~FLAGS.B.value
        self.status &= ~FLAGS.U.value
        self.stkp += 1
        self.pc = self.__read(0x0100 + self.stkp)
        self.stkp += 1
        self.pc |= self.__read(0x0100 + self.stkp) << 8
        return 0

    def __RTS(self) -> int:
        """Return from Subroutine:
        The RTS instruction is used at the end of a subroutine to return to the calling routine.
        It pulls the program counter (minus one) from the stack.
        :return: 0 cycle
        """
        self.stkp += 1
        self.pc = self.__read(0x0100 + self.stkp)
        self.stkp += 1
        self.pc |= self.__read(0x0100 + self.stkp) << 8
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
        self.__write(self.__addr_abs, self.a)
        return 0

    def __STX(self):
        self.__write(self.__addr_abs, self.x)
        return 0

    def __STY(self):
        self.__write(self.__addr_abs, self.y)
        return 0

    def __TAX(self):
        self.x = self.a
        self.__SetFlag(FLAGS.Z, self.x == 0x00)
        self.__SetFlag(FLAGS.N, self.x & 0x80 > 0)
        return 0

    def __TAY(self):
        self.y = self.a
        self.__SetFlag(FLAGS.Z, self.y == 0x00)
        self.__SetFlag(FLAGS.N, self.y & 0x80 > 0)
        return 0

    def __TSX(self):
        self.x = self.stkp
        self.__SetFlag(FLAGS.Z, self.x == 0x00)
        self.__SetFlag(FLAGS.N, self.x & 0x80 > 0)
        return 0

    def __TXA(self):
        self.a = self.x
        self.__SetFlag(FLAGS.Z, self.a == 0x00)
        self.__SetFlag(FLAGS.N, self.a & 0x80 > 0)
        return 0

    def __TXS(self):
        self.stkp = self.x
        return 0

    def __TYA(self):
        self.a = self.y
        self.__SetFlag(FLAGS.Z, self.a == 0x00)
        self.__SetFlag(FLAGS.N, self.a & 0x80 > 0)
        return 0

    def __XXX(self):
        return 0

    """disassembly function
    
    This function turns the binary insruction code into human readable form.
    
    """

    def __disassemble(self, nstart: int, nstop: int):
        pass
