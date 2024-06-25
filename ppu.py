"""
Author: Henry-Sky <https://github.com/Henry-Sky>
Date: 2024-06-24
"""

from cartridge import Cartridge
from sprite import Sprite
from utils import TILE, MIRROR, Pixel, PalInit


class Ppu2c02:
    def __init__(self):
        self.__scanline = 0
        self.__cycle = 0
        self.odd_frame = False

        self.__cart = None

        self.nmi = False
        self.scanline_trigger = False
        self.frame_complete = False

        # Internal communications
        self.ppu_data_buffer = 0x00
        self.address_latch = 0x00
        self.fine_x = 0

        self.vram_addr = 0x0000  # active "pointer" address into nametable to extract background tile info
        """vram_addr: 16 bit
        
         | Low
         |  5 bit : coarse_x
         |  5 bit : coarse_y
         |  1 bit : nametable_x
         |  1 bit : nametable_y
         |  3 bit : fine_y
         |  1 bit : unused
         | High       
         
        """
        self.tram_addr = 0x0000  # temporary store of information to be "transferred" into "pointer" at various times
        """tram_addr: 16 bit

         | Low
         |  5 bit : coarse_x
         |  5 bit : coarse_y
         |  1 bit : nametable_x
         |  1 bit : nametable_y
         |  3 bit : fine_y
         |  1 bit : unused
         | High       

        """
        # 8 Registers for cpu[$2000~$2007]
        self.__control = 0b00000000
        """control
        
         | Low
         |   1 bit : nametable_x         
         |   1 bit : nametable_y         
         |   1 bit : increment_mode     
         |   1 bit : pattern_sprite    
         |   1 bit : pattern_background  
         |   1 bit : sprite_size       
         |   1 bit : slave_mode        
         |   1 bit : enable_nmi     
         | high
         
        """
        self.__mask = 0b00000000
        """mask
        
         | Low
         |   1 bit : grayscale
         |   1 bit : render_background_left
         |   1 bit : render_sprites_left
         |   1 bit : render_background
         |   1 bit : render_sprites
         |   1 bit : enhance_red
         |   1 bit : enhance_green
         |   1 bit : enhance_blue
         | high
            
        """
        self.__status = 0b00000000
        """status
        
         | Low
         |   5 bit : unused     
         |   1 bit : sprite_overflow
         |   1 bit : sprite_zero_hit
         |   1 bit : vertical_blank
         | high
         
        """

        self.palScreen = PalInit()
        self.sprScreen = Sprite(256, 240)
        self.sprNameTable = [Sprite(256, 240)] * 2
        self.sprPatternTable = [Sprite(128, 128)] * 2

        # 2KB = 2 * (960B[NameTable] + 64B[AttributeTable])
        self.__tblName = [[0] * 1024] * 2
        # 8KB = 2 * 4KB[PatternTable]
        self.__tblPattern = [[0] * 4096] * 2
        # Colour Rom
        self.__tblPalette = [0] * 32

        # Background rendering
        self.bg_next_tile_id = 0x00
        self.bg_next_tile_attrib = 0x00
        self.bg_next_tile_lsb = 0x00
        self.bg_next_tile_msb = 0x00
        self.bg_shifter_pattern_lo = 0x0000
        self.bg_shifter_pattern_hi = 0x0000
        self.bg_shifter_attrib_lo = 0x0000
        self.bg_shifter_attrib_hi = 0x0000

        #  Foreground rendering
        self.oam_addr = 0x00
        self.OAM = [TILE(0x00, 0x00, 0x00, 0x00)] * 64
        self.sprite_count = 0
        self.spriteScanline = [TILE(0, 0, 0, 0)] * 8
        self.sprite_shifter_pattern_lo = [0b0] * 8
        self.sprite_shifter_pattern_hi = [0b0] * 8
        self.bSpriteZEroHitPossible = False
        self.bSpriteZeroBeingRendered = False

    def GetScreen(self):
        return self.sprScreen

    def GetNameTable(self, i: int):
        return self.sprNameTable[i]

    def GetPatternTable(self, i: int, palette: int):
        """

        This function draw the CHR ROM for a given pattern table into a Sprite.
        Pattern tables consist os 16 x 16 "tiles or characters"

        A tile consist of 8 x 8 pixels
        On NES pixel are 2 bits witch gives 4 different colours of specific palette
        There are 8 palettes to choose from

        Characters on NES
        ~~~~~~~~~~~~~~~~~
        The NES stores characters using 2-bit pixels. These are not stored sequentially
        but in singular bit planes. For example:

        2-Bit Pixels       LSB Bit Plane     MSB Bit Plane
        0 0 0 0 0 0 0 0	  0 0 0 0 0 0 0 0   0 0 0 0 0 0 0 0
        0 1 1 0 0 1 1 0	  0 1 1 0 0 1 1 0   0 0 0 0 0 0 0 0
        0 1 2 0 0 2 1 0	  0 1 1 0 0 1 1 0   0 0 1 0 0 1 0 0
        0 0 0 0 0 0 0 0 = 0 0 0 0 0 0 0 0 + 0 0 0 0 0 0 0 0
        0 1 1 0 0 1 1 0	  0 1 1 0 0 1 1 0   0 0 0 0 0 0 0 0
        0 0 1 1 1 1 0 0	  0 0 1 1 1 1 0 0   0 0 0 0 0 0 0 0
        0 0 0 2 2 0 0 0	  0 0 0 1 1 0 0 0   0 0 0 1 1 0 0 0
        0 0 0 0 0 0 0 0	  0 0 0 0 0 0 0 0   0 0 0 0 0 0 0 0

        The planes are stored as 8 bytes of LSB, followed by 8 bytes of MSB

        """
        for y in range(16):
            for x in range(16):
                nOffset = y * 256 + x * 16
                for row in range(8):
                    tile_lsb = self.ppuRead(i * 0x1000 + nOffset + row + 0x0000)
                    tile_msb = self.ppuRead(i * 0x1000 + nOffset + row + 0x0008)
                    for col in range(8):
                        pixel = (tile_lsb & 0x01) + (tile_msb & 0x01)
                        tile_lsb >>= 1
                        tile_msb >>= 1
                        self.sprPatternTable[i].SetPixel(
                            x=(x * 8) + (7 - col),
                            y=(y * 8) + row,
                            p=self.GetColourFromPaletteRam(palette, pixel)
                        )
        # Finally return the updated sprite representing the pattern table
        return self.sprPatternTable[i]

    def GetColourFromPaletteRam(self, palette: int, pixel: int) -> Pixel:
        """
        Taking a specified palette and pixel index
        Return the appropriate screen colour
        """
        return self.palScreen[self.ppuRead(0x3F00 + (palette << 2) + pixel) & 0x3F]

    def connectCart(self, cart: Cartridge):
        self.__cart = cart

    def reset(self):
        self.fine_x = 0x00
        self.address_latch = 0x00
        self.ppu_data_buffer = 0x00
        self.__scanline = 0
        self.__cycle = 0
        self.bg_next_tile_id = 0x00
        self.bg_next_tile_attrib = 0x00
        self.bg_next_tile_lsb = 0x00
        self.bg_next_tile_msb = 0x00
        self.bg_shifter_pattern_lo = 0x0000
        self.bg_shifter_pattern_hi = 0x0000
        self.bg_shifter_attrib_lo = 0x0000
        self.bg_shifter_attrib_hi = 0x0000
        self.__status = 0x00
        self.vram_addr = 0x0000
        self.tram_addr = 0x0000

    def cpuWrite(self, addr: int, data: int):
        if addr == 0x0000:  # Control
            self.__control = data
            self.tram_addr = (self.tram_addr & 0xC0) | (self.__control & 0x3F)
        elif addr == 0x0001:  # Mask
            self.__mask = data
        elif addr == 0x0002:  # Status: Not readable
            pass
        elif addr == 0x0003:  # OAM Address: Not readable
            pass
        elif addr == 0x0004:  # OAM Data
            tx = data & 0xFF_00_00_00 >> 24
            ta = data & 0x00_FF_00_00 >> 16
            ti = data & 0x00_00_FF_00 >> 8
            ty = data & 0x00_00_00_FF >> 0
            self.OAM[self.oam_addr] = TILE(ty, ti, ta, tx)
        elif addr == 0x0005:  # Scroll
            if self.address_latch == 0:
                self.fine_x = data & 0x0007
                # tram_addr->coarse_x = data >> 3
                self.tram_addr = (self.tram_addr & 0x07FF) | ((data >> 3) << 11)
                self.address_latch = 1
            else:
                # tram_addr->fine_y = data & 0x07
                self.tram_addr = (self.tram_addr & 0xFFF1) | (data & 0x07 << 1)
                # tram_addr->coarse_y = data >> 3
                self.tram_addr = (self.tram_addr & 0xF83F) | ((data >> 3) << 6)
                self.address_latch = 0
        elif addr == 0x0006:
            if self.address_latch == 0:
                self.tram_addr = ((data & 0x3F) << 8) | (self.tram_addr & 0x00FF)
                self.address_latch = 1
            else:
                self.tram_addr = (self.tram_addr & 0xFF00) | data
                self.vram_addr = self.tram_addr
                self.address_latch = 0
        elif addr == 0x0007:
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
        data = 0x00
        if readonly:
            """
            Reading behavior could affect the ppu contents，
            Hence it，we set the readonly option
            The option is used for reading without changing its status
            This is really only used for debug mode !
            """
            if addr == 0x0000:  # Control
                data = self.__control
            elif addr == 0x0001:  # Mask
                data = self.__mask
            elif addr == 0x0002:  # Status
                data = self.__status
            elif addr == 0x0003:  # OAM Address
                pass
            elif addr == 0x0004:  # OAM Data
                pass
            elif addr == 0x0005:  # Scroll
                pass
            elif addr == 0x0006:  # PPU Address
                pass
            elif addr == 0x0007:  # PPU Data
                pass
        else:
            """
            Note that not all registers are capable of being reading
            So they just return 0x00
            """
            if addr == 0x0000:
                # Control : Not readable
                pass
            elif addr == 0x0001:
                # Mask : Not readable
                pass
            elif addr == 0x0002:
                """
                Only the top three bits contain status information
                Some game may use the bottom 5 bits "noise" as valid data
                """
                data = self.__status & 0xE0 | (self.ppu_data_buffer & 0x1F)
                # Clear the vertical blanking flag
                self.__status &= 0x7F
                self.address_latch = 0
            elif addr == 0x0003:
                pass
            elif addr == 0x0004:
                data = self.OAM[self.oam_addr]
            elif addr == 0x0005:
                pass
            elif addr == 0x0006:
                pass
            elif addr == 0x0007:
                data = self.ppu_data_buffer
                self.ppu_data_buffer = self.ppuRead(self.vram_addr)
                if self.vram_addr >= 0x3F00:
                    data = self.ppu_data_buffer
                self.vram_addr += 32 if self.__control >= (1 << 5) else 1
            else:
                pass
        return data

    def ppuRead(self, addr: int, readonly=False) -> int:
        """

        1. Get address to PPU range
        2. Judge ppu address
            case 0x0000-0x1FFF : Pattern Tables

            case 0x2000-0x2FFF : Name Tables
            case 0x3000-0x3EFF : Mirrors

            case 0x3F00-0x3F1F : Palette RAM
            case 0x3F20-0x3FFF : Mirrors

        """
        addr &= 0x3FFF
        flag, data = self.__cart.ppuRead(addr)
        if flag:
            pass
        elif 0x0000 <= addr <= 0x1FFF:
            data = self.__tblPattern[(addr & 0x1000) >> 12][addr & 0x0FFF]
        elif 0x2000 <= addr <= 0x3EFF:
            addr &= 0x0FFF
            if self.__cart.Mirror() == MIRROR.VERTICAL:
                if 0x0000 <= addr <= 0x03FF:
                    data = self.__tblName[0][addr & 0x03FF]
                elif 0x0400 <= addr <= 0x07FF:
                    data = self.__tblName[1][addr & 0x03FF]
                elif 0x0800 <= addr <= 0x0BFF:
                    data = self.__tblName[0][addr & 0x03FF]
                elif 0x0c00 <= addr <= 0x0FFF:
                    data = self.__tblName[1][addr & 0x03FF]
            elif self.__cart.Mirror() == MIRROR.HORIZONTAL:
                if 0x0000 <= addr <= 0x03FF:
                    data = self.__tblName[0][addr & 0x03FF]
                elif 0x0400 <= addr <= 0x07ff:
                    data = self.__tblName[0][addr & 0x03FF]
                elif 0x0800 <= addr <= 0x0bff:
                    data = self.__tblName[1][addr & 0x03FF]
                elif 0x0c00 <= addr <= 0x0FFF:
                    data = self.__tblName[1][addr & 0x03FF]
        elif 0x3F00 <= addr <= 0x3FFF:
            addr &= 0x001f
            if addr == 0x0010:
                addr = 0x0000
            elif addr == 0x0014:
                addr = 0x0004
            elif addr == 0x0018:
                addr = 0x0008
            elif addr == 0x001c:
                addr = 0x000c
            data = self.__tblPalette[addr] & (0x30 if self.__mask >= (1 << 7) else 0x3F)
        return data

    def ppuWrite(self, addr: int, data: int):
        """

        1. Get address to PPU range
        2. Judge ppu address
            case 0x0000-0x1FFF : Pattern Tables

            case 0x2000-0x2FFF : Name Tables
            case 0x3000-0x3EFF : Mirrors

            case 0x3F00-0x3F1F : Palette RAM
            case 0x3F20-0x3FFF : Mirrors

        """
        addr &= 0x3FFF
        if self.__cart.ppuWrite(addr, data):
            pass
        elif 0x0000 <= addr <= 0x1FFF:
            self.__tblPattern[(addr & 0x1000) >> 12][addr & 0x0FFF] = data
        elif 0x2000 <= addr <= 0x3EFF:
            addr &= 0x0FFF
            if self.__cart.mirror == MIRROR.VERTICAL:
                if 0x0000 <= addr <= 0x03FF:
                    self.__tblName[0][addr & 0x03FF] = data
                elif 0x0400 <= addr <= 0x07ff:
                    self.__tblName[1][addr & 0x03FF] = data
                elif 0x0800 <= addr <= 0x0Bff:
                    self.__tblName[0][addr & 0x03FF] = data
                elif 0x0c00 <= addr <= 0x0FFF:
                    self.__tblName[1][addr & 0x03FF] = data
            elif self.__cart.mirror == MIRROR.HORIZONTAL:
                if 0x0000 <= addr <= 0x03FF:
                    self.__tblName[0][addr & 0x03FF] = data
                elif 0x0400 <= addr <= 0x07FF:
                    self.__tblName[0][addr & 0x03FF] = data
                elif 0x0800 <= addr <= 0x0BFF:
                    self.__tblName[1][addr & 0x03FF] = data
                elif 0x0C00 <= addr <= 0x0FFF:
                    self.__tblName[1][addr & 0x03FF] = data
        elif 0x3F00 <= addr <= 0x3FFF:
            addr &= 0x001F
            if addr == 0x0010:
                addr = 0x0000
            elif addr == 0x0014:
                addr = 0x0004
            elif addr == 0x0018:
                addr = 0x0B08
            elif addr == 0x001C:
                addr = 0x000C
            self.__tblPalette[addr] = data

    def clock(self):
        # Increment the background tile "pointer" one tile/column horizontally
        def IncrementScrollX():
            # Only if rendering is enabled
            if (self.__mask & (1 << 3)) or (self.__mask & (1 << 4)):
                if self.vram_addr & 0x0000001F == 31:
                    self.vram_addr &= 0x0000FFE0
                    self.vram_addr ^= (1 << 10)
                else:
                    self.vram_addr += 1

        def IncrementScrollY():
            if (self.__mask & (1 << 3)) or (self.__mask & (1 << 4)):
                if (self.vram_addr & 0x00007000) >> 12 < 7:
                    self.vram_addr += 0x1000
                else:
                    self.vram_addr &= 0x00008FFF
                    if self.vram_addr & 0x000003E0 >> 5 == 29:
                        # Set the coarse_y = 0
                        self.vram_addr &= 0x0000FC1F
                        # Set the ~nametable_y
                        self.vram_addr ^= (1 << 11)
                    elif self.vram_addr & 0x000003E0 >> 5 == 31:
                        # Set the coarse_y = 0
                        self.vram_addr &= 0x0000FC1F
                    else:
                        # Set the coarse_y ++
                        self.vram_addr += (1 << 5)

        def TransferAddressX():
            if (self.__mask & (1 << 3)) or (self.__mask & (1 << 4)):
                # set vram_name_tablex = tram_name_table.
                self.vram_addr &= ~0x0400
                self.vram_addr ^= (self.tram_addr & 0x00000400)
                # coarse_x
                self.vram_addr &= ~0x001F
                self.vram_addr ^= (self.tram_addr & 0x0000001F)

        def TransferAddressY():
            if (self.__mask & (1 << 3)) or (self.__mask & (1 << 4)):
                self.vram_addr &= ~0x7000
                self.vram_addr ^= (self.tram_addr & 0x00007000)
                self.vram_addr &= ~0x0800
                self.vram_addr ^= (self.tram_addr & 0x00000800)
                self.vram_addr &= ~0x03E0
                self.vram_addr ^= (self.tram_addr & 0x000003E0)

        def LoadBackgroundShifters():
            self.bg_shifter_pattern_lo = (self.bg_shifter_pattern_lo & 0x0000FF00) | self.bg_next_tile_lsb
            self.bg_shifter_pattern_hi = (self.bg_shifter_pattern_hi & 0x0000FF00) | self.bg_next_tile_msb

            self.bg_shifter_attrib_lo = (self.bg_shifter_attrib_lo & 0x0000FF00) | (
                0xFF if (self.bg_next_tile_attrib & 0x00000001) else 0x00)
            self.bg_shifter_attrib_hi = (self.bg_shifter_attrib_hi & 0x0000FF00) | (
                0xFF if (self.bg_next_tile_attrib & 0x00000002) else 0x00)

        def UpdateShifters():
            if self.__mask & 0x08:
                self.bg_shifter_pattern_lo <<= 1
                self.bg_shifter_pattern_lo &= 0x0000FFFF
                self.bg_shifter_pattern_hi <<= 1
                self.bg_shifter_pattern_hi &= 0x0000FFFF

                self.bg_shifter_attrib_lo <<= 1
                self.bg_shifter_attrib_lo &= 0x0000FFFF
                self.bg_shifter_attrib_hi <<= 1
                self.bg_shifter_attrib_hi &= 0x0000FFFF

            if self.__mask & 0x08 and 1 <= self.__cycle < 258:
                for x in range(self.sprite_count):
                    if self.spriteScanline[x].x > 0:
                        self.spriteScanline[x].x -= 1
                    else:
                        self.sprite_shifter_pattern_lo[x] <<= 1
                        self.sprite_shifter_pattern_hi[x] <<= 1

        if -1 <= self.__scanline < 240:
            if (self.__scanline == 0 and self.__cycle == 0 and self.odd_frame
                    and ((self.__mask & (1 << 3)) or (self.__mask & (1 << 4)))):
                self.__cycle = 1

            if self.__cycle == 1 and self.__scanline == -1:
                # Effectively start of new frame, so clear vertical blank flag
                self.__status &= 0x00000080  # Clear vertical_blank
                self.__status &= 0x00000020  # Clear sprite_overflow
                self.__status &= 0x00000040  # Clear sprite_zero_hit
                for i in range(8):
                    self.sprite_shifter_pattern_lo[i] = 0
                    self.sprite_shifter_pattern_hi[i] = 0

            if 2 <= self.__cycle < 258 or 321 <= self.__cycle < 338:
                """
                
                2 <= self.__cycle < 258 : 这段时间是每条扫描线的主要渲染阶段，PPU 在这个范围内执行背景和精灵的像素绘制。
                扫描线 240 到 260 是垂直空白期间（VBlank），此时屏幕不进行渲染，PPU 处理其他任务，如设置垂直空白标志、通知 CPU 当前帧已完成渲染等。
                321 <= self.__cycle < 338 : 这是每条扫描线的最后一个部分，用于准备下一条扫描线的渲染数据。
                
                """
                UpdateShifters()
                flag = (self.__cycle - 1) % 8
                if flag == 0:
                    LoadBackgroundShifters()
                    # Fetch the next background tile ID
                    self.bg_next_tile_id = self.ppuRead(0x2000 | (self.vram_addr & 0x00000FFF))
                    pass

                elif flag == 2:
                    self.bg_next_tile_attrib = self.ppuRead(0x23C0 | (self.vram_addr & 0x00000800)
                                                            | (self.vram_addr & 0x00000400)
                                                            | ((self.vram_addr & 0x000003E0 >> 7) << 3)
                                                            | (self.vram_addr & 0x0000001F >> 2))
                    if (self.vram_addr & 0x000003E0 >> 5) & 0x02:
                        self.bg_next_tile_attrib >>= 4
                    if (self.vram_addr & 0x0000001F) & 0x02:
                        self.bg_next_tile_attrib >>= 2
                    self.bg_next_tile_attrib &= 0x00000003
                    pass

                elif flag == 4:
                    addr = (self.__control & 0x00000010 << 8) + (self.bg_next_tile_id << 4) + (
                                self.vram_addr & 0x00007000 >> 12 + 0)
                    self.bg_next_tile_lsb = self.ppuRead(addr)
                    pass

                elif flag == 6:
                    addr = (self.__control & 0x00000010 << 8) + (self.bg_next_tile_id << 4) + (
                                self.vram_addr & 0x7000 >> 12 + 8)
                    self.bg_next_tile_msb = self.ppuRead(addr)
                    pass

                elif flag == 7:
                    IncrementScrollX()
                    pass

            if self.__cycle == 256:
                # End of a scanline, increase Y scroll
                IncrementScrollY()

            if self.__cycle == 257:
                # Reset the x position to start a new Scanline
                LoadBackgroundShifters()
                TransferAddressX()

            if self.__cycle == 338 or self.__cycle == 340:
                #
                self.bg_next_tile_id = self.ppuRead(0x2000 | (self.vram_addr & 0x00000FFF))

            if 280 <= self.__cycle < 305:
                if self.__scanline == -1:
                    TransferAddressY()

            # Foreground Rendering

            if self.__cycle == 257 and self.__scanline >= 0:
                self.spriteScanline = [TILE(0xFF, 0xFF, 0xFF, 0xFF)] * 8
                self.sprite_count = 0
                for i in range(8):
                    self.sprite_shifter_pattern_lo[i] = 0
                    self.sprite_shifter_pattern_hi[i] = 0

                nOAMEntry = 0
                self.bSpriteZEroHitPossible = False

                while nOAMEntry < 64 and self.sprite_count < 9:
                    diff = self.__scanline - self.OAM[nOAMEntry].y

                    if 0 <= diff < (16 if self.__control & 0x00000020 else 8) and self.sprite_count < 8:
                        if self.sprite_count < 8:
                            if nOAMEntry == 0:
                                self.bSpriteZEroHitPossible = True
                            self.spriteScanline[self.sprite_count] = self.OAM[nOAMEntry]
                        self.sprite_count += 1
                    nOAMEntry += 1

                self.__status &= 0b11011111 if self.sprite_count >= 8 else 0xFF

            if self.__cycle == 340:

                sprite_pattern_bits_lo = 0xFF
                sprite_pattern_bits_hi = 0xFF
                sprite_pattern_addr_lo = 0xFF
                sprite_pattern_addr_hi = 0xFF

                for i in range(self.sprite_count):
                    if not self.__control & 0b00100000:
                        if not self.spriteScanline[i].attribute & 0x80:
                            sprite_pattern_addr_lo = ((self.__control & 0x08 << 9) |
                                                      (self.spriteScanline[i].id << 4) |
                                                      (self.__scanline - self.spriteScanline[i].y))
                        else:
                            sprite_pattern_addr_lo = ((self.__control & 0x08 << 9) |
                                                      (self.spriteScanline[i].id << 4) |
                                                      (7 - (self.__scanline - self.spriteScanline[i].y)))
                    else:
                        if not self.spriteScanline[i].attribute & 0x80:
                            if self.__scanline - self.spriteScanline[i].y < 8:
                                sprite_pattern_addr_lo = (((self.spriteScanline[i].id & 0x01) << 12) |
                                                          ((self.spriteScanline[i].id & 0xFE) << 4) |
                                                          ((self.__scanline - self.spriteScanline[i].y) & 0x07))
                            else:
                                sprite_pattern_addr_lo = (((self.spriteScanline[i].id & 0x01) << 12) |
                                                          (((self.spriteScanline[i].id & 0xFE) + 1) << 4) |
                                                          ((self.__scanline - self.spriteScanline[i].y) & 0x07))
                        else:
                            if self.__scanline - self.spriteScanline[i].y < 8:
                                sprite_pattern_addr_lo = (((self.spriteScanline[i].id & 0x01) << 12) |
                                                          (((self.spriteScanline[i].id & 0xFE) + 1) << 4) |
                                                          ((7 - (self.__scanline - self.spriteScanline[i].y)) & 0x07))
                            else:
                                sprite_pattern_addr_lo = (((self.spriteScanline[i].id & 0x01) << 12) |
                                                          ((self.spriteScanline[i].id & 0xFE) << 4) |
                                                          ((7 - (self.__scanline - self.spriteScanline[i].y)) & 0x07))

                    sprite_pattern_addr_hi = sprite_pattern_addr_lo + 8
                    sprite_pattern_bits_lo = self.ppuRead(sprite_pattern_addr_lo)
                    sprite_pattern_bits_hi = self.ppuRead(sprite_pattern_addr_hi)

                    if self.spriteScanline[i].attribute & 0x40:
                        def flipbyte(a):
                            a = (a & 0xF0) >> 4 | (a & 0x0F) << 4
                            a = (a & 0xCC) >> 2 | (a & 0x33) << 2
                            a = (a & 0xAA) >> 1 | (a & 0x55) << 1
                            return a

                        sprite_pattern_bits_lo = flipbyte(sprite_pattern_bits_lo)
                        sprite_pattern_bits_hi = flipbyte(sprite_pattern_bits_hi)

                    self.sprite_shifter_pattern_lo[i] = sprite_pattern_bits_lo
                    self.sprite_shifter_pattern_hi[i] = sprite_pattern_bits_hi

        if self.__scanline == 240:
            # Post Render Scanline - Do Nothing!
            pass

        if 241 <= self.__scanline < 261:
            if self.__scanline == 241 and self.__cycle == 1:
                self.__status |= 0b10000000
                if self.__control & 0b10000000:
                    self.nmi = True

        # Background
        bg_pixel = 0x00
        bg_palette = 0x00
        if self.__mask & 0x08:
            if self.__mask & 0x02 or self.__cycle >= 9:
                bit_mux = 0x8000 >> self.fine_x
                p0_pixel = 1 if (self.bg_shifter_pattern_lo & bit_mux) > 0 else 0
                p1_pixel = 1 if (self.bg_shifter_pattern_hi & bit_mux) > 0 else 0

                bg_pixel = (p1_pixel << 1) | p0_pixel

                bg_pal0 = (self.bg_shifter_attrib_lo & bit_mux) > 0
                bg_pal1 = (self.bg_shifter_attrib_hi & bit_mux) > 0

                bg_palette = (bg_pal1 << 1) | bg_pal0

        # Foreground
        fg_pixel = 0x00
        fg_palette = 0x00
        fg_priority = 0x00

        if self.__mask & 0x10 or self.__cycle >= 9:
            self.bSpriteZeroBeingRendered = False
            for i in range(self.sprite_count):
                if self.spriteScanline[i].x == 0:
                    fg_pixel_lo = (self.sprite_shifter_pattern_lo[i] & 0x80) > 0
                    fg_pixel_hi = (self.sprite_shifter_pattern_hi[i] & 0x80) > 0
                    fg_pixel = (fg_pixel_hi << 1) | fg_pixel_lo

                    fg_palette = (self.spriteScanline[i].attribute & 0x03) + 0x04
                    fg_priority = (self.spriteScanline[i].attribute & 0x20) == 0

                    if fg_pixel != 0:
                        if i == 0:
                            self.bSpriteZeroBeingRendered = True

        # Combine sprite and background
        pixel = 0x00
        palette = 0x00
        if bg_pixel == 0 and fg_pixel == 0:
            pixel = 0x00
            palette = 0x00
        elif bg_pixel == 0 and fg_pixel > 0:
            pixel = fg_pixel
            palette = fg_palette
        elif bg_pixel > 0 and fg_pixel == 0:
            pixel = bg_pixel
            palette = bg_palette
        elif bg_pixel > 0 and fg_pixel > 0:
            if fg_priority:
                pixel = fg_pixel
                palette = fg_palette
            else:
                pixel = bg_pixel
                palette = bg_palette

            if self.bSpriteZEroHitPossible and self.bSpriteZeroBeingRendered:
                if self.__mask & 0x80 and self.__mask & 0x10:
                    if not (self.__mask & 0x02 or self.__mask & 0x04):
                        if 9 <= self.__cycle < 258:
                            self.__status |= 0b01000000
                    else:
                        if 1 <= self.__cycle < 258:
                            self.__status |= 0b01000000

        self.sprScreen.SetPixel(self.__cycle - 1, self.__scanline, self.GetColourFromPaletteRam(palette, pixel))

        self.__cycle += 1
        if self.__mask & 0x08 and self.__mask & 0x10:
            if self.__cycle == 260 and self.__scanline < 240:
                self.__cart.GetMapper().scanline()

        if self.__cycle >= 341:
            self.__cycle = 0
            self.__scanline += 1
            if self.__scanline >= 261:
                self.__scanline = -1
                self.frame_complete = True
                self.odd_frame = not self.odd_frame
