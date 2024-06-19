import sys
import time
from utils import hex2int
from PyQt5 import QtCore, QtGui, QtWidgets
import threading


def DrawWindows():
    app = QtWidgets.QApplication(sys.argv)
    window = QtWidgets.QWidget()
    window.setWindowTitle('RingNes')
    window.resize(500, 500)
    label = QtWidgets.QLabel(parent=window)
    label.setWindowTitle("labeltitle")
    window.show()
    sys.exit(app.exec_())


def main():
    a = 0
    b = a
    a = 2

    print(b)


if __name__ == '__main__':
    main()
