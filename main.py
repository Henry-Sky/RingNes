from bus import Bus
from screen import Screen
from utils import ColorMap
from cartridge import Cartridge


class RingNES(object):
    def __init__(self):
        self.nes = Bus()
        self.cart = Cartridge("./Rom/mario.nes")
        self.screen = None

        self.bEmulationRun = False
        self.fResidualTime = 0.0

    def Start(self):
        if self.onUserCreate():
            pass

    def onUserCreate(self) -> bool:
        if not self.cart.bImageValid:
            return False
        # Insert Cartridge
        self.nes.insertCartridge(self.cart)
        # Reset NES
        self.nes.reset()
        return True

    def onUserUpdate(self, fElapsedTime) -> bool:
        self.nes.ppu.GetScreen().Clear(ColorMap["DARK_BLUE"])
        if self.bEmulationRun:
            if self.fResidualTime > 0.0:
                self.fResidualTime -= fElapsedTime
            else:
                self.fResidualTime += (1.0 / 60.0) - fElapsedTime
                while not self.nes.ppu.frame_complete:
                    self.nes.clock()
                self.nes.ppu.frame_complete = False
        else:
            pass
        return True


def main():
    nes = RingNES()


if __name__ == '__main__':
    main()
