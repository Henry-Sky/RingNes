import sys
from PyQt5.QtGui import QPalette
from bus import Bus
from PyQt5.QtWidgets import*
from PyQt5.QtCore import*

from cartridge import Cartridge


class Screen(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('NES-DEBUG')
        self.setGeometry(100, 100, 1280, 720)
        # 主要部件, 可在其上添加其他额外部件
        self.centralwidget = QWidget()
        self.centralwidget.resize(1280, 720)
        self.setCentralWidget(self.centralwidget)
        self.palette = QPalette()
        # Set Layout
        self.main_layout = QHBoxLayout()
        self.left_layout = QVBoxLayout()
        self.right_layout = QVBoxLayout()
        # Add widget on left layout
        self.left_layout.addWidget(self.GameWidget())
        # Add widget on right layout
        self.right_layout.addWidget(self.DebugWidget())

        self.main_layout.addLayout(self.left_layout)
        self.main_layout.addLayout(self.right_layout)
        self.centralwidget.setLayout(self.main_layout)

        # device
        self.bus = None
        self.bconnectedBus = False

        # ui
        self.clock_info = "Wait for clock to start"

    def connectedBus(self, n: Bus):
        self.bus = n
        self.bconnectedBus = True

    def GameWidget(self) -> QWidget:
        gamelabel = QWidget()
        gamelabel.resize(640, 480)
        return gamelabel

    def DebugWidget(self) -> QWidget:
        debuglabel = QWidget()
        debuglabel.resize(640, 720)
        debuglayout = QVBoxLayout()
        debuglayout.addWidget(self.DebugButton())
        debuglabel.setLayout(debuglayout)
        return debuglabel

    def DebugButton(self) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout()
        widget.resize(640, 200)

        info_lab = QLabel()
        info_lab.setText("INFO")
        info_lab.resize(320, 200)
        layout.addWidget(info_lab)

        debug_btn = QPushButton('Debug-Clock')
        debug_btn.resize(320, 200)
        debug_btn.clicked.connect(self.DebugClock)
        layout.addWidget(debug_btn)

        widget.setLayout(layout)
        return widget

    def DebugClock(self):
        if self.bconnectedBus:
            self.bus.clock()
        else:
            pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Screen()
    bus = Bus()
    cart = Cartridge("./Rom/nestest.nes")
    bus.insertCartridge(cart)
    bus.reset()
    w.connectedBus(bus)
    w.show()
    sys.exit(app.exec_())