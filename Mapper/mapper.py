"""
Author: Henry-Sky <https://github.com/Henry-Sky>
Date: 2024-06-18
"""

class Mapper(object):
    def __init__(self, prgBanks: int, chrBanks: int):
        self._nPRGBanks = prgBanks
        self._nCHRBanks = chrBanks

    def cpuMapRead(self, addr: int) -> (bool, int, int):
        """Check Mapper Read

        The addr between $8000 ~ $FFFF is PRG-ROM which stored in cartridge.
        If cpu want to read above addr then return true and mappered address
        else return false and origan address

        :param addr: address cpu request
        :return: true, mapped address, data
        """
        pass


    def cpuMapWrite(self, addr: int, data: int) -> (bool, int):
        """Check Mapper Write

        The addr between $8000 ~ $FFFF is PRG-ROM which stored in cartridge.
        If cpu want to write above addr then return true and mappered address
        else return false and origan address

        :param addr: address cpu request, data
        :return: true, mapped address
        """
        pass


    def ppuMapRead(self, addr: int, mapped_addr: int) -> bool:
        pass


    def ppuMapWrite(self, addr: int, mapped_addr: int) -> bool:
        pass
