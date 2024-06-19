import random

from cartridge import Cartridge
from screen import Pixel
from sprite import Sprite
from utils import hex2int, MIRROR


class Ppu2c02:
    def __init__(self):
        self.__scanline = 0
        self.__cycle = 0
        self.__cart = None
        self.nmi = False
        self.frame_complete = False
        # Internal communications
        self.ppu_data_buffer = hex2int("0x00")
        self.address_latch = hex2int("0x00")
        self.fine_x = 0
        """loopy register: vram_addr and tram_addr
        5 bit : coarse_x
        5 bit : coarse_y
        1 bit : nametable_x
        1 bit : nametable_y
        3 bit : fine_y
        1 bit : unused
        """
        self.vram_addr = 0  # active "pointer" address into nametable to extract background tile info
        self.tram_addr = 0  # temporary store of information to be "transferred" into "pointer" at various times
        # 8 Registers for cpu[$2000~$2007]
        """control
            1 bit : nametable_x
            1 bit : nametable_y
            1 bit : increment_mode
            1 bit : pattern_sprite
            1 bit : pattern_background
            1 bit : sprite_size
            1 bit : slave_mode
            1 bit : enable_nmi
        """
        self.__control = 0
        """mask
            1 bit : grayscale
            1 bit : render_background_left
            1 bit : render_sprites_left
            1 bit : render_background
            1 bit : render_sprites
            1 bit : enhance_red
            1 bit : enhance_green
            1 bit : enhance_blue
        """
        self.__mask = 0
        """status
            5 bit : unused
            1 bit : sprite_overflow
            1 bit : sprite_zero_hit
            1 bit : vertical_blank
        """
        self.__status = 0
        # API
        self.palScreen = self.palInit()
        self.sprScreen = Sprite(256, 240)
        self.sprNameTable = [Sprite(256, 240), Sprite(256, 240)]
        self.sprPatternTable = [Sprite(128, 128), Sprite(128, 128)]
        # THE VIDEO MEMORY
        # 2KB = 2 * (960B[NameTable] + 64B[AttributeTable])
        self.__tblName = [[0 for x in range(1024)], [0 for x in range(1024)]]
        # 8KB = 2 * 4KB[PatternTable]
        self.__tblPattern = [[0 for i in range(4096)], [0 for i in range(4096)]]
        # 背景调色板 ?
        self.__tblPalette = [0 for i in range(32)]

        self.bg_next_tile_id = hex2int("0x00")
        self.bg_next_tile_attrib = hex2int("0x00")
        self.bg_next_tile_lsb = hex2int("0x00")
        self.bg_next_tile_msb = hex2int("0x00")
        self.bg_shifter_pattern_lo = hex2int("0x0000")
        self.bg_shifter_pattern_hi = hex2int("0x0000")
        self.bg_shifter_attrib_lo = hex2int("0x0000")
        self.bg_shifter_attrib_hi = hex2int("0x0000")

    def palInit(self) -> list:
        pals = [
            Pixel(84, 84, 84),
            Pixel(0, 30, 116),
            Pixel(8, 16, 144),
            Pixel(48, 0, 136),
            Pixel(68, 0, 100),
            Pixel(92, 0, 48),
            Pixel(84, 4, 0),
            Pixel(60, 24, 0),
            Pixel(32, 42, 0),
            Pixel(8, 58, 0),
            Pixel(0, 64, 0),
            Pixel(0, 60, 0),
            Pixel(0, 50, 60),
            Pixel(0, 0, 0),
            Pixel(0, 0, 0),
            Pixel(0, 0, 0),

            Pixel(152, 150, 152),
            Pixel(8, 76, 196),
            Pixel(48, 50, 236),
            Pixel(92, 30, 228),
            Pixel(136, 20, 176),
            Pixel(160, 20, 100),
            Pixel(152, 34, 32),
            Pixel(120, 60, 0),
            Pixel(84, 90, 0),
            Pixel(40, 114, 0),
            Pixel(8, 124, 0),
            Pixel(0, 118, 40),
            Pixel(0, 102, 120),
            Pixel(0, 0, 0),
            Pixel(0, 0, 0),
            Pixel(0, 0, 0),

            Pixel(236, 238, 236),
            Pixel(76, 154, 236),
            Pixel(120, 124, 236),
            Pixel(176, 98, 236),
            Pixel(228, 84, 236),
            Pixel(236, 88, 180),
            Pixel(236, 106, 100),
            Pixel(212, 136, 32),
            Pixel(160, 170, 0),
            Pixel(116, 196, 0),
            Pixel(76, 208, 32),
            Pixel(56, 204, 108),
            Pixel(56, 180, 204),
            Pixel(60, 60, 60),
            Pixel(0, 0, 0),
            Pixel(0, 0, 0),

            Pixel(236, 238, 236),
            Pixel(168, 204, 236),
            Pixel(188, 188, 236),
            Pixel(212, 178, 236),
            Pixel(236, 174, 236),
            Pixel(236, 174, 212),
            Pixel(236, 180, 176),
            Pixel(228, 196, 144),
            Pixel(204, 210, 120),
            Pixel(180, 222, 120),
            Pixel(168, 226, 144),
            Pixel(152, 226, 180),
            Pixel(160, 214, 228),
            Pixel(160, 162, 160),
            Pixel(0, 0, 0),
            Pixel(0, 0, 0),
        ]
        return pals

    def GetScreen(self):
        return self.sprScreen

    def GetNameTable(self, i: int):
        return self.sprNameTable[i]

    def GetPatternTable(self, i: int):
        return self.sprPatternTable[i]

    def connectCart(self, cart: Cartridge):
        self.__cart = cart

    def reset(self):
        self.fine_x = hex2int("0x00")
        self.address_latch = hex2int("0x00")
        self.ppu_data_buffer = hex2int("0x00")
        self.__scanline = 0
        self.__cycle = 0
        self.bg_next_tile_id = hex2int("0x00")
        self.bg_next_tile_attrib = hex2int("0x00")
        self.bg_next_tile_lsb = hex2int("0x00")
        self.bg_next_tile_msb = hex2int("0x00")
        self.bg_shifter_pattern_lo = hex2int("0x0000")
        self.bg_shifter_pattern_hi = hex2int("0x0000")
        self.bg_shifter_attrib_lo = hex2int("0x0000")
        self.bg_shifter_attrib_hi = hex2int("0x0000")
        self.__status = hex2int("0x00")
        self.vram_addr = hex2int("0x0000")
        self.tram_addr = hex2int("0x0000")

    def cpuWrite(self, addr: int, data: int):
        if addr == hex2int("0x0000"):  # Control
            self.__control = data
            self.tram_addr = (self.tram_addr & hex2int("0xc0")) | (self.__control & hex2int("0x3f"))
        elif addr == hex2int("0x0001"):  # Mask
            self.__mask = data
        elif addr == hex2int("0x0002"):  # Status
            pass
        elif addr == hex2int("0x0003"):  # OAM Address
            pass
        elif addr == hex2int("0x0004"):  # OAM Data
            pass
        elif addr == hex2int("0x0005"):  # Scroll
            if self.address_latch == 0:
                self.fine_x = data & hex2int("0x07")
                # tram_addr->coarse_x = data >> 3
                self.tram_addr = (self.tram_addr & hex2int("0x07ff")) | ((data >> 3) << 11)
                self.address_latch = 1
            else:
                # tram_addr->fine_y = data & 0x07
                self.tram_addr = (self.tram_addr & hex2int("0xfff1")) | (data & hex2int("0x07") << 1)
                # tram_addr->coarse_y = data >> 3
                self.tram_addr = (self.tram_addr & hex2int("0xf83f")) | ((data >> 3) << 6)
                self.address_latch = 0
        elif addr == hex2int("0x0006"):
            if self.address_latch == 0:
                self.tram_addr = ((data & hex2int("0x3f")) << 8) | (self.tram_addr & hex2int("0x00ff"))
                self.address_latch = 1
            else:
                self.tram_addr = (self.tram_addr & hex2int("0xff00")) | data
                self.vram_addr = self.tram_addr
                self.address_latch = 0
        elif addr == hex2int("0x0007"):
            self.ppuWrite(self.vram_addr, data)
            self.vram_addr += 32 if self.__control >= (1 << 5) else 1
        else:
            pass

    def cpuRead(self, addr: int, readonly: bool) -> int:
        """
        :param addr: The cpu readable address: $0x0000 ~ $0x0007
        :param readonly: If true do read without changing, only in debug mode
        :return: The data of ppu data buffer
        """
        data = hex2int("0x00")
        if readonly:
            """
            Reading behavior could affect the ppu contents，
            Hence it，we set the readonly option
            The option is used for reading without changing its status
            This is really only used for debug mode !
            """
            if addr == hex2int("0x0000"):
                data = self.__control
            elif addr == hex2int("0x0001"):
                data = self.__mask
            elif addr == hex2int("0x0002"):
                data = self.__status
            elif addr == hex2int("0x0003"):
                pass
            elif addr == hex2int("0x0004"):
                pass
            elif addr == hex2int("0x0005"):
                pass
            elif addr == hex2int("0x0006"):
                pass
            elif addr == hex2int("0x0007"):
                pass
            else:
                pass
        else:
            """
            Note that not all registers are capable of being reading
            So they just return 0x00
            """
            if addr == hex2int("0x0000"):
                pass
            elif addr == hex2int("0x0001"):
                pass
            elif addr == hex2int("0x0002"):
                """
                Only the top three bits contain status information
                Some game may use the bottom 5 bits "noise" as valid data
                """
                data = self.__status & hex2int("0xE0") | (self.ppu_data_buffer & hex2int("0x1F"))
                # Clear the vertical blanking flag (the high bit)
                self.__status = (self.__status | 1) ^ 1
                self.address_latch = 0
            elif addr == hex2int("0x0003"):
                pass
            elif addr == hex2int("0x0004"):
                pass
            elif addr == hex2int("0x0005"):
                pass
            elif addr == hex2int("0x0006"):
                pass
            elif addr == hex2int("0x0007"):
                data = self.ppu_data_buffer
                self.ppu_data_buffer = self.ppuRead(self.vram_addr)
                if self.vram_addr >= hex2int("0x3f00"):
                    data = self.ppu_data_buffer
                self.vram_addr += 32 if self.__control >= (1 << 5) else 1
            else:
                pass
        return data

    def ppuRead(self, addr: int, readonly=False) -> int:
        # [$2000~$3FFF]: 8KB PPU Register
        data = hex2int("0x00")
        addr &= hex2int("0x3fff")
        if self.__cart.ppuRead(addr, data):
            pass
        elif hex2int("0x0000") <= addr <= hex2int("0x1fff"):
            data = self.__tblPattern[(addr & hex2int("0x1000")) >> 12][addr & hex2int("0x0fff")]
        elif hex2int("0x2000") <= addr <= hex2int("0x3eff"):
            addr &= hex2int("0x0fff")
            if self.__cart.mirror == MIRROR.VERTICAL:
                if hex2int("0x0000") <= addr <= hex2int("0x03ff"):
                    data = self.__tblName[0][addr & hex2int("0x03ff")]
                elif hex2int("0x0400") <= addr <= hex2int("0x07ff"):
                    data = self.__tblName[1][addr & hex2int("0x03ff")]
                elif hex2int("0x0800") <= addr <= hex2int("0x0bff"):
                    data = self.__tblName[0][addr & hex2int("0x03ff")]
                elif hex2int("0x0c00") <= addr <= hex2int("0x0fff"):
                    data = self.__tblName[1][addr & hex2int("0x03ff")]
            elif self.__cart.mirror == MIRROR.HORIZONTAL:
                if hex2int("0x0000") <= addr <= hex2int("0x03ff"):
                    data = self.__tblName[0][addr & hex2int("0x03ff")]
                elif hex2int("0x0400") <= addr <= hex2int("0x07ff"):
                    data = self.__tblName[0][addr & hex2int("0x03ff")]
                elif hex2int("0x0800") <= addr <= hex2int("0x0bff"):
                    data = self.__tblName[1][addr & hex2int("0x03ff")]
                elif hex2int("0x0c00") <= addr <= hex2int("0x0fff"):
                    data = self.__tblName[1][addr & hex2int("0x03ff")]
        elif hex2int("0x3f00") <= addr <= hex2int("0x3fff"):
            addr &= hex2int("0x001f")
            if addr == hex2int("0x0010"):
                addr = hex2int("0x0000")
            elif addr == hex2int("0x0014"):
                addr = hex2int("0x0004")
            elif addr == hex2int("0x0018"):
                addr = hex2int("0x0008")
            elif addr == hex2int("0x001c"):
                addr = hex2int("0x000c")
            data = self.__tblPalette[addr] & (hex2int("0x30") if self.__mask >= (1 << 7) else hex2int("0x3f"))
        return data

    def ppuWrite(self, addr: int, data: int):
        # [$2000~$3FFF]: 8KB PPU Register
        addr &= hex2int("0x3fff")
        if self.__cart.ppuWrite(addr, data):
            pass
        elif hex2int("0x0000") <= addr <= hex2int("0x1fff"):
            self.__tblPattern[(addr & hex2int("0x1000")) >> 12][addr & hex2int("0x0fff")] = data
        elif hex2int("0x2000") <= addr <= hex2int("0x3eff"):
            addr &= hex2int("0x0fff")
            if self.__cart.mirror == MIRROR.VERTICAL:
                if hex2int("0x0000") <= addr <= hex2int("0x03ff"):
                    self.__tblName[0][addr & hex2int("0x03ff")] = data
                elif hex2int("0x0400") <= addr <= hex2int("0x07ff"):
                    self.__tblName[1][addr & hex2int("0x03ff")] = data
                elif hex2int("0x0800") <= addr <= hex2int("0x0bff"):
                    self.__tblName[0][addr & hex2int("0x03ff")] = data
                elif hex2int("0x0c00") <= addr <= hex2int("0x0fff"):
                    self.__tblName[1][addr & hex2int("0x03ff")] = data
            elif self.__cart.mirror == MIRROR.HORIZONTAL:
                if hex2int("0x0000") <= addr <= hex2int("0x03ff"):
                    self.__tblName[0][addr & hex2int("0x03ff")] = data
                elif hex2int("0x0400") <= addr <= hex2int("0x07ff"):
                    self.__tblName[0][addr & hex2int("0x03ff")] = data
                elif hex2int("0x0800") <= addr <= hex2int("0x0bff"):
                    self.__tblName[1][addr & hex2int("0x03ff")] = data
                elif hex2int("0x0c00") <= addr <= hex2int("0x0fff"):
                    self.__tblName[1][addr & hex2int("0x03ff")] = data
        elif hex2int("0x3f00") <= addr <= hex2int("0x3fff"):
            addr &= hex2int("0x001f")
            if addr == hex2int("0x0010"):
                addr = hex2int("0x0000")
            elif addr == hex2int("0x0014"):
                addr = hex2int("0x0004")
            elif addr == hex2int("0x0018"):
                addr = hex2int("0x0b08")
            elif addr == hex2int("0x001c"):
                addr = hex2int("0x000c")
            self.__tblPalette[addr] = data

    def clock(self):
        noise = hex2int("0x3f") if random.random() > 0.5 else hex2int("0x30")
        self.sprScreen.SetPixel(self.__cycle - 1, self.__scanline, self.palScreen[noise])

        self.__cycle += 1
        if self.__cycle >= 341:
            self.__cycle = 0
            self.__scanline += 1
            if self.__scanline >= 261:
                self.__scanline = -1
                self.frame_complete = True
