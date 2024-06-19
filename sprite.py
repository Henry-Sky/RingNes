from screen import Pixel
from utils import hex2int

class Sprite(object):
    def __init__(self, w: int, h: int):
        self.width = w
        self.height = h

        self.nDefaultAlpha = hex2int("0xff")
        self.nDefaultPixel = (hex2int("0xff") << 24)
        self.pColData = [self.nDefaultPixel for i in range(self.width * self.height)]

    def SetPixel(self, x: int, y: int, p: Pixel) -> bool:
        if 0 <= x < self.width and 0 <= y < self.height:
            self.pColData[y * self.width + x] = p
            return True
        else:
            return False

    def GetPixel(self, x: int, y: int) -> Pixel:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.pColData[y * self.width + x]
        else:
            return Pixel(0, 0, 0, 0)

    def Clear(self, p: Pixel):
        for a in self.pColData:
            a = p