from bus import Bus
from cartridge import Cartridge


def main():
    nes = Bus()
    cart = Cartridge("./Rom/mario.nes")
    nes.insertCartridge(cart)
    nes.reset()
    while True:
        nes.ppu.GetScreen()
        nes.clock()

if __name__ == '__main__':
    # main()
    a = [[0] * 10]* 2

    print(a)
