from typing import Tuple

import pyglet
from pyglet import image
from pyglet.sprite import Sprite

from Minecraft.libs.command import MinecraftCommand


class Button:
    def __init__(self, x, y, width, height, on, off, text, type_):
        self.w, self.h = width, height
        self.x, self.y = x - self.w // 2, y - self.h // 2
        self.imgs = [image.load(off), image.load(on)]
        self.on = False
        self.sprite = Sprite(self.imgs[0])
        self.sprite.x = x - self.w // 2
        self.sprite.y = y - self.h // 2
        self.sprite.scale_x = self.w / 910
        self.sprite.scale_y = self.h / 290
        self.type = type_
        self.lab = pyglet.text.Label(text,
                                     font_name='Arial',
                                     font_size=15,
                                     x=self.x + self.w // 2 - len(text) * 6, y=self.y + self.h // 2 - 6)

    def draw(self):
        self.sprite.image = self.imgs[int(self.on)]
        self.sprite.draw()
        self.lab.draw()

    # x,y,(1,0,-1),func,arguments
    def isHit(self, x, y, mode, func: MinecraftCommand):
        if mode == 1:
            if self.x < x < self.x + self.w:
                if self.y < y < self.y + self.h:
                    self.on = True
                    self.draw()
                    MinecraftCommand.execute(func.executor, func.args)
        elif mode == -1:
            if self.x < x < self.x + self.w:
                if self.y < y < self.y + self.h:
                    self.on = False
        elif mode == 0:
            z = 1
            if self.x < x < self.x + self.w:
                if self.y < y < self.y + self.h:
                    self.on = True
                    z = 0
            if z == 1:
                self.on = False
