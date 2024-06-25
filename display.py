"""
Author: Henry-Sky <https://github.com/Henry-Sky>
Date: 2024-06-24
"""

import tkinter as tk
from bus import Bus
import random
import threading

from cartridge import Cartridge
from sprite import Sprite


class Display:
    def __init__(self, root, width=256, height=240, pixel_size=1, threads = 32):
        root.title('NES-DEV')
        self.root = root
        self.width = width
        self.height = height
        self.pixel_size = pixel_size
        self.bus = None

        # Create a canvas to draw on
        self.canvas = tk.Canvas(root, width=self.width * self.pixel_size, height=self.height * self.pixel_size)
        self.canvas.pack()

        # Create a PhotoImage to hold pixel data
        self.image = tk.PhotoImage(width=self.width, height=self.height)
        self.canvas.create_image((self.width // 2, self.height // 2), image=self.image, state="normal")

        # Initialize pixel data
        self.pixel_data = [["#000000"] * self.width for _ in range(self.height)]

        # Start the thread to generate random pixels
        self.running = True

        self.thread_list = []
        for i in range(threads):
            self.thread = threading.Thread(target=self.update_clock)
            self.thread_list.append(self.thread)
            self.thread.start()
        self.pix_thread = threading.Thread(target=self.generate_pixels)
        self.pix_thread.start()


        # Start updating the canvas
        self.update_canvas()

    def update_clock(self):
        while self.running:
            if self.bus is not None:
                self.bus.clock()

    def generate_pixels(self):
        while self.running:
            new_pixel_data = []
            if self.bus is not None:
                sprScreen : Sprite = self.bus.ppu.GetScreen()
                data = sprScreen.ColData
                for y in range(self.height):
                    row = []
                    for x in range(self.width):
                        index = y * 256 + x
                        color = "#{:02x}{:02x}{:02x}".format(data[index].red, data[index].green, data[index].blue)
                        row.append(color)
                    new_pixel_data.append(row)
            else:
                for y in range(self.height):
                    row = []
                    for x in range(self.width):
                        color = "#{:02x}{:02x}{:02x}".format(random.randint(0, 255), random.randint(0, 255),
                                                             random.randint(0, 255))
                        row.append(color)
                    new_pixel_data.append(row)
            self.pixel_data = new_pixel_data

    def update_canvas(self):
        pixel_data = ""
        for row in self.pixel_data:
            pixel_data += "{" + " ".join(row) + "} "
        self.image.put(pixel_data)

        # Schedule the next update
        if self.running:
            self.root.after(33, self.update_canvas)  # Approximately 30 FPS

    def stop(self):
        self.running = False
        self.pix_thread.join()
        for t in self.thread_list:
            t.join()

    def connectBus(self, bus: Bus):
        self.bus = bus


if __name__ == "__main__":
    root = tk.Tk()
    app = Display(root)
    bus = Bus()
    cart = Cartridge("./Rom/mario.nes")
    bus.insertCartridge(cart)
    bus.reset()
    app.connectBus(bus)

    def on_closing():
        app.stop()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
