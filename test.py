from cartridge import Cartridge
from cpu import Cpu6502
from bus import Bus


def main():
    cartridge = Cartridge("./Rom/mario.nes")


if __name__ == '__main__':
    main()
