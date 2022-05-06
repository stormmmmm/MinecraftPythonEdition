import math
import os
import pickle
import random
import sys

from types import MappingProxyType
import pyglet.graphics
from pyglet import image
from pyglet.gl import *
from pyglet.sprite import Sprite
from pyglet.window import key, mouse

from Minecraft.libs.command import MinecraftCommand
from libs.Button import Button
from model import cube_vertices, player, music_list, xrange, \
    FLYING_SPEED, WALKING_SPEED, TERMINAL_VELOCITY, GRAVITY, \
    PLAYER_HEIGHT, sectorize, normalize, FACES, soundpl, JUMP_SPEED, TICKS_PER_SEC, Model
from utils import warns


class Window(pyglet.window.Window):

    def __init__(self, *args, **kwargs):
        super(Window, self).__init__(*args, **kwargs)

        # Whether or not the window exclusively captures the mouse.
        self.model = Model()
        self.exclusive = False

        # When flying gravity has no effect and speed is increased.
        self.flying = False

        # Strafing is moving lateral to the direction you are facing,
        # e.g. moving to the left or right while continuing to face forward.
        #
        # First element is -1 when moving forward, 1 when moving back, and 0
        # otherwise. The second element is -1 when moving left, 1 when moving
        # right, and 0 otherwise.
        self.strafe = [0, 0]

        # Current (x, y, z) position in the world, specified with floats. Note
        # that, perhaps unlike in math class, the y-axis is the vertical axis.
        self.position = (0, 50, 0)

        # First element is rotation of the player in the x-z plane (ground
        # plane) measured from the z-axis down. The second is the rotation
        # angle from the ground plane up. Rotation is in degrees.
        #
        # The vertical plane rotation ranges from -90 (looking straight down) to
        # 90 (looking straight up). The horizontal rotation range is unbounded.
        self.rotation = (0, 0)

        # Which sector the player is currently in.
        self.sector = None

        # Inventory gui
        self.bar = Sprite(image.load(f"textures{os.sep}ui{os.sep}inven.png"), x=0, y=0)
        self.toggleInv = False

        # The crosshairs at the center of the screen.
        self.reticle = None

        # Velocity in the y (upward) direction.
        self.dy = 0

        # Convenience list of num keys.
        self.num_keys = (
            key._1, key._2, key._3, key._4, key._5,
            key._6, key._7, key._8, key._9, key._0
        )

        # A list of blocks the player can place. Hit num keys to cycle.
        self.hotBar = ["GRASS", "SAND", "GLASS", "STONE", "OLDR", "WOOD", "BWOOD", "LEAF", "BLEAF"]
        # The player's inventory
        self.inventory = [["" for _ in range(9)] for _ in range(5)]
        for i in range(len(self.model.blocksSprites.keys())):
            if i > 9 * 5:
                break
            else:
                self.inventory[i // 9][i % 9] = list(self.model.blocksSprites.keys())[i]

        # The current block the user can place. Hit num keys to cycle.
        self.block = self.hotBar[0]
        self.moveBlock = [0, 0, ""]

        # Opened menu
        self.openMenu = False
        # Menu button's commands
        # key: command
        self.commands = MappingProxyType({
            "exit": MinecraftCommand(self.exit),
            "saves": MinecraftCommand(self.to_saves),
            "main": MinecraftCommand(self.to_main),
            "save": MinecraftCommand(self.save),
            "load": MinecraftCommand(self.load),
            "game": MinecraftCommand(self.to_game)
        })

        # Menus
        self.main_menu = (Button(self.width // 2, self.height // 2 + 60, 200, 30,
                                 f"textures{os.sep}ui{os.sep}button2.png",
                                 f"textures{os.sep}ui{os.sep}button1.png", "Load", "saves"),
                          Button(self.width // 2, self.height // 2 + 20, 200, 30,
                                 f"textures{os.sep}ui{os.sep}button2.png",
                                 f"textures{os.sep}ui{os.sep}button1.png", "Save", "save"),
                          Button(self.width // 2, self.height // 2 - 20, 200, 30,
                                 f"textures{os.sep}ui{os.sep}button2.png",
                                 f"textures{os.sep}ui{os.sep}button1.png", "Exit", "exit"),
                          Button(self.width // 2, self.height // 2 + 100, 200, 30,
                                 f"textures{os.sep}ui{os.sep}button2.png",
                                 f"textures{os.sep}ui{os.sep}button1.png", "Continue", "game"),
                          )
        self.saves_menu = (Button(self.width // 2, self.height // 2 + 200, 200, 30,
                                  f"textures{os.sep}ui{os.sep}button2.png",
                                  f"textures{os.sep}ui{os.sep}button1.png", "Back", "main"),
                           Button(self.width // 2, self.height // 2 + 60, 200, 50,
                                  f"textures{os.sep}ui{os.sep}button2.png",
                                  f"textures{os.sep}ui{os.sep}button1.png", "Load", "load")
                           )

        # Menu is current show
        self.shown_menu = self.main_menu

        # Menu's background
        self.bg = Sprite(image.load(f"textures{os.sep}ui{os.sep}background.png"), 0, 0)

        # The label that is displayed in the top left of the canvas.
        self.label = pyglet.text.Label('', font_name='MS Serif', font_size=18,
                                       x=10, y=self.height - 10, anchor_x='left', anchor_y='top',
                                       color=(0, 0, 0, 255))
        # Time
        self.time_world = 0
        self.time_music = 0
        self.world_time_map = MappingProxyType({
            9500: lambda: self.set_time_world(0),
            2500: lambda: glClearColor(0.4, 0.50, 0.8, 1) and
                          glFogfv(GL_FOG_COLOR, (GLfloat * 4)(0.4, 0.50, 0.8, 1)),
            1: lambda: glClearColor(0.7, 0.69, 1.0, 1) and
                       glFogfv(GL_FOG_COLOR, (GLfloat * 4)(0.7, 0.69, 1.0, 1)),
            4000: lambda: glClearColor(0.3, 0.35, 0.5, 1) and
                          glFogfv(GL_FOG_COLOR, (GLfloat * 4)(0.3, 0.35, 0.5, 1)),
            5000: lambda: glClearColor(0.2, 0.20, 0.3, 1) and
                          glFogfv(GL_FOG_COLOR, (GLfloat * 4)(0.2, 0.20, 0.3, 1)),
            5500: lambda: glClearColor(0.1, 0.10, 0.2, 1) and
                          glFogfv(GL_FOG_COLOR, (GLfloat * 4)(0.1, 0.10, 0.2, 1)),
            6000: lambda: glClearColor(0, 0, 0, 1) and
                          glFogfv(GL_FOG_COLOR, (GLfloat * 4)(0, 0, 0, 1)),
            7000: lambda: glClearColor(0.1, 0.10, 0.2, 1) and
                          glFogfv(GL_FOG_COLOR, (GLfloat * 4)(0.1, 0.10, 0.2, 1)),
            7500: lambda: glClearColor(0.2, 0.20, 0.3, 1) and
                          glFogfv(GL_FOG_COLOR, (GLfloat * 4)(0.2, 0.20, 0.3, 1)),
            8500: lambda: glClearColor(0.3, 0.35, 0.5, 1) and
                          glFogfv(GL_FOG_COLOR, (GLfloat * 4)(0.3, 0.35, 0.5, 1)),
            9200: lambda: glClearColor(0.4, 0.50, 0.8, 1) and
                          glFogfv(GL_FOG_COLOR, (GLfloat * 4)(0.4, 0.50, 0.8, 1))
        })
        self.run_symbols = MappingProxyType({
            key.W: lambda: self.strafe.__setitem__(0, self.strafe[0] - 1),
            key.S: lambda: self.strafe.__setitem__(0, self.strafe[0] + 1),
            key.A: lambda: self.strafe.__setitem__(1, self.strafe[1] - 1),
            key.D: lambda: self.strafe.__setitem__(1, self.strafe[1] + 1),
        })
        self.stop_symbols = MappingProxyType({
            key.W: lambda: self.strafe.__setitem__(0, self.strafe[0] + 1),
            key.S: lambda: self.strafe.__setitem__(0, self.strafe[0] - 1),
            key.A: lambda: self.strafe.__setitem__(1, self.strafe[1] + 1),
            key.D: lambda: self.strafe.__setitem__(1, self.strafe[1] - 1),
        })
        #
        # self.inven_image = pyglet.image.load('textures/ui/inven.png')
        # This call schedules the `update()` method to be called
        # TICKS_PER_SEC. This is the main game event loop.
        pyglet.clock.schedule_interval(self.update, 1.0 / TICKS_PER_SEC)

    # functions used by the menu buttons
    def to_game(self):
        self.openMenu = False

    def to_saves(self):
        self.shown_menu = self.saves_menu

    def to_main(self):
        self.shown_menu = self.main_menu

    def exit(self):
        try:
            self.close()
            sys.exit(0)
        finally:
            pass

    def save(self):
        if "save1" not in os.listdir("saves"):
            os.mkdir(f"saves{os.sep}save1/")
        q1 = open(f"saves{os.sep}save1{os.sep}world.mcp", "wb")
        q2 = open(f"saves{os.sep}save1{os.sep}shown.mcp", "wb")
        q3 = open(f"saves{os.sep}save1{os.sep}sectors.mcp", "wb")
        data1 = pickle.dumps(self.model.__dict__["world"])
        data2 = pickle.dumps(self.model.__dict__["shown"])
        data3 = pickle.dumps(self.model.__dict__["sectors"])
        q1.write(data1)
        q2.write(data2)
        q3.write(data3)
        q1.close()
        q2.close()
        q3.close()

    def load(self):
        q1 = open(f"saves{os.sep}save1{os.sep}world.mcp", "rb")
        q2 = open(f"saves{os.sep}save1{os.sep}shown.mcp", "rb")
        q3 = open(f"saves{os.sep}save1{os.sep}sectors.mcp", "rb")
        d1 = q1.read()
        d2 = q2.read()
        d3 = q3.read()
        q1.close()
        q2.close()
        q3.close()
        self.model.world = pickle.loads(d1)  # Replace dates
        self.model.shown = pickle.loads(d2)
        self.model.sectors = pickle.loads(d3)
        self.model._shown = {}  # Reset dates
        self.model.batch = pyglet.graphics.Batch()
        for i in self.model.shown:
            x, y, z = i
            vertex_data = cube_vertices(x, y, z, 0.5)
            texture_data = list(self.model.world[i][0])
            self.model._shown[i] = self.model.batch.add(24, GL_QUADS,
                                                        self.model.atlases[self.model.shown[i][1]][0],
                                                        ('v3f/static', vertex_data),
                                                        ('t2f/static', texture_data))

    def set_exclusive_mouse(self, exclusive=True):
        """ If `exclusive` is True, the game will capture the mouse, if False
        the game will ignore the mouse.

        """
        super(Window, self).set_exclusive_mouse(exclusive)
        self.exclusive = exclusive

    def get_sight_vector(self):
        """ Returns the current line of sight vector indicating the direction
        the player is looking.

        """
        x, y = self.rotation
        # y ranges from -90 to 90, or -pi/2 to pi/2, so m ranges from 0 to 1 and
        # is 1 when looking ahead parallel to the ground and 0 when looking
        # straight up or down.
        m_ = math.cos(math.radians(y))
        # dy ranges from -1 to 1 and is -1 when looking straight down and 1 when
        # looking straight up.
        dy = math.sin(math.radians(y))
        dx = math.cos(math.radians(x - 90)) * m_
        dz = math.sin(math.radians(x - 90)) * m_
        return dx, dy, dz

    def get_motion_vector(self):
        """ Returns the current motion vector indicating the velocity of the
        player.

        Returns
        -------
        vector : tuple of len 3
            Tuple containing the velocity in x, y, and z respectively.

        """
        if any(self.strafe):
            x, y = self.rotation
            strafe = math.degrees(math.atan2(*self.strafe))
            y_angle = math.radians(y)
            x_angle = math.radians(x + strafe)
            if self.flying:
                m_ = math.cos(y_angle)
                dy = math.sin(y_angle)
                if self.strafe[1]:
                    # Moving left or right.
                    dy = 0.0
                    m_ = 1
                if self.strafe[0] > 0:
                    # Moving backwards.
                    dy *= -1
                # When you are flying up or down, you have less left and right
                # motion.
                dx = math.cos(x_angle) * m_
                dz = math.sin(x_angle) * m_
            else:
                dy = 0.0
                dx = math.cos(x_angle)
                dz = math.sin(x_angle)
        else:
            dy = dx = dz = 0.0
        return dx, dy, dz

    def set_time_world(self, time_):
        self.time_world = time_

    def update(self, dt):
        # music = pyglet.media.load('music/' + random.choice(music_list) + '.wav')
        # player.play()
        # time
        self.time_world += 1
        self.time_music += 1
        if self.time_music == 21000:
            music_ = pyglet.media.load(f'music{os.sep}{random.choice(music_list)}.wav')
            player.queue(music_)
            player.play()
        if self.time_music == 21001:
            self.time_music = 0
        self.world_time_map.get(self.time_world, lambda: None)()
        if any(self.position) < -3:
            self.position = (0, 100, 0)
        # pass
        """ This method is scheduled to be called repeatedly by the pyglet
        clock.

        Parameters
        ----------
        dt : float
            The change in time since the last call.

        """
        self.model.process_queue()
        sector = sectorize(self.position)
        if sector != self.sector:
            self.model.change_sectors(self.sector, sector)
            if self.sector is None:
                self.model.process_entire_queue()
            self.sector = sector
        m_ = 8
        dt = min(dt, 0.2)
        for _ in xrange(m_):
            self._update(dt / m_)
        if self.moveBlock[2] != "":
            self.moveBlock[0] = self._mouse_x - 16
            self.moveBlock[1] = self._mouse_y - 16

    def _update(self, dt):
        """ Private implementation of the `update()` method. This is where most
        of the motion logic lives, along with gravity and collision detection.

        Parameters
        ----------
        dt : float
            The change in time since the last call.

        """
        # walking
        speed = FLYING_SPEED if self.flying else WALKING_SPEED
        d = dt * speed  # distance covered this tick.
        dx, dy, dz = self.get_motion_vector()
        # New position in space, before accounting for gravity.
        dx, dy, dz = dx * d, dy * d, dz * d
        # gravity
        if not self.flying:
            # Update your vertical speed: if you are falling, speed up until you
            # hit terminal velocity; if you are jumping, slow down until you
            # start falling.
            self.dy -= dt * GRAVITY
            self.dy = max(self.dy, -TERMINAL_VELOCITY)
            dy += self.dy * dt
        # collisions
        x, y, z = self.position
        x, y, z = self.collide((x + dx, y + dy, z + dz), PLAYER_HEIGHT)
        self.position = (x, y, z)

    def collide(self, position, height):
        """ Checks to see if the player at the given `position` and `height`
        is colliding with any blocks in the world.

        Parameters
        ----------
        position : tuple of len 3
            The (x, y, z) position to check for collisions at.
        height : int or float
            The height of the player.

        Returns
        -------
        position : tuple of len 3
            The new position of the player taking into account collisions.

        """
        # How much overlap with a dimension of a surrounding block you need to
        # have to count as a collision. If 0, touching terrain at all counts as
        # a collision. If .49, you sink into the ground, as if walking through
        # tall grass. If >= .5, you'll fall through the ground.
        pad = 0.25
        p = list(position)
        np_ = normalize(position)
        for face in FACES:  # check all surrounding blocks
            for i in xrange(3):  # check each dimension independently
                if not face[i]:
                    continue
                # How much overlap you have with this dimension.
                d = (p[i] - np_[i]) * face[i]
                if d < pad:
                    continue
                for dy in xrange(height):  # check each height
                    op = list(np_)
                    op[1] -= dy
                    op[i] += face[i]
                    if tuple(op) not in self.model.world:
                        continue
                    p[i] -= (d - pad) * face[i]
                    if face == (0, -1, 0) or face == (0, 1, 0):
                        # You are colliding with the ground or ceiling, so stop
                        # falling / rising.
                        self.dy = 0
                    break
        return tuple(p)

    def on_mouse_press(self, x, y, button, modifiers):
        """ Called when a mouse button is pressed. See pyglet docs for button
        amd modifier mappings.

        Parameters
        ----------
        x, y : int
            The coordinates of the mouse click. Always center of the screen if
            the mouse is captured.
        button : int
            Number representing mouse button that was clicked. 1 = left button,
            4 = right button.
        modifiers : int
            Number representing any modifying keys that were pressed when the
            mouse button was clicked.

        """
        if self.openMenu:
            for i in self.shown_menu:
                f = self.commands[i.type]
                i.isHit(x, y, 1, f)
        elif self.exclusive:
            vector = self.get_sight_vector()
            block, previous = self.model.hit_test(self.position, vector)
            if (button == mouse.RIGHT) or \
                    ((button == mouse.LEFT) and (modifiers & key.MOD_CTRL)):
                # ON OSX, control + left click = right click.
                if previous:
                    self.model.add_block(previous, self.model.blocks[self.block])
            elif button == pyglet.window.mouse.LEFT and block:
                texture = self.model.world[block]
                warns.maybe_unused(texture)

                self.model.remove_block(block, by_player=True)
                sound_ = pyglet.media.load(f'sounds{os.sep}break.wav')
                soundpl.queue(sound_)
                soundpl.play()
        elif not self.toggleInv:
            self.set_exclusive_mouse(True)
        elif self.toggleInv:
            if button == mouse.LEFT:
                x = x // 35
                y = abs(self.height - y) // 35
                try:
                    self.moveBlock[2] = self.inventory[y][x]
                finally:
                    pass

    def on_mouse_motion(self, x, y, dx, dy):
        """ Called when the player moves the mouse.

        Parameters
        ----------
        x, y : int
            The coordinates of the mouse click. Always center of the screen if
            the mouse is captured.
        dx, dy : float
            The movement of the mouse.

        """
        if self.openMenu:
            for i in self.shown_menu:
                f = self.commands[i.type]
                i.isHit(x, y, 0, f)
        elif self.exclusive:
            m_ = 0.15
            x, y = self.rotation
            x, y = x + dx * m_, y + dy * m_
            y = max(-90, min(90, int(y)))
            self.rotation = (x, y)

    def on_mouse_release(self, x, y, button, modifiers):
        if self.openMenu:
            for i in self.shown_menu:
                f = self.commands[i.type]
                i.isHit(x, y, -1, f)
        if self.toggleInv:
            if button == mouse.LEFT:
                if self.moveBlock[2] != "":
                    x = abs(6 - x) // 40
                    try:
                        if y <= 41:
                            self.hotBar[x] = self.moveBlock[2]
                    finally:
                        pass
                    self.moveBlock[2] = ""

    def on_key_press(self, symbol, modifiers):
        """ Called when the player presses a key. See pyglet docs for key
        mappings.

        Parameters
        ----------
        symbol : int
            Number representing the key that was pressed.
        modifiers : int
            Number representing any modifying keys that were pressed.

        """
        if symbol == key.SPACE:
            if self.dy == 0:
                self.dy = JUMP_SPEED
        elif symbol == key.ESCAPE:
            self.set_exclusive_mouse(False)
            self.openMenu = not self.openMenu
        elif symbol == key.TAB:
            self.flying = not self.flying
            sound = pyglet.media.load(f'sounds{os.sep}fly.wav')
            soundpl.queue(sound)
            soundpl.play()
        elif symbol in self.num_keys:
            index = (symbol - self.num_keys[0]) % len(self.hotBar)
            self.block = self.hotBar[index]
        elif symbol == key.F11:
            # not working yet
            window = pyglet.window.Window(fullscreen=True)

            warns.maybe_unused(window)
        elif symbol == key.R:
            self.position = (125, 50, 125)
        elif symbol == key.E:
            self.toggleInv = not self.toggleInv
            self.set_exclusive_mouse(not self.toggleInv)
        else:
            self.run_symbols.get(symbol, lambda: None)()

    def on_key_release(self, symbol, modifiers):
        """ Called when the player releases a key. See pyglet docs for key
        mappings.

        Parameters
        ----------
        symbol : int
            Number representing the key that was pressed.
        modifiers : int
            Number representing any modifying keys that were pressed.

        """
        global flying

        if symbol == key.F2:
            file = str(random.randint(1, 99999999999999999999))
            f = open(f'screenshots{os.sep}{file}.png', "a")
            f.close()
            pyglet.image.get_buffer_manager().get_color_buffer().save(
                'screenshots/' + file + '.png')
        elif symbol == key.Y:
            self.time_world += 200
        else:
            self.stop_symbols.get(symbol, lambda: None)()

    def on_resize(self, width, height):
        """ Called when the window is resized to a new `width` and `height`.

        """
        # label
        self.label.y = height - 10
        # reticle
        if self.reticle:
            self.reticle.delete()
        x, y = self.width // 2, self.height // 2
        n = 10
        self.reticle = pyglet.graphics.vertex_list(4,
                                                   ('v2i', (x - n, y, x + n, y, x, y - n, x, y + n))
                                                   )

    def set_2d(self):
        """ Configure OpenGL to draw in 2d.

        """
        width, height = self.get_size()
        glDisable(GL_DEPTH_TEST)
        viewport = self.get_viewport_size()
        glViewport(0, 0, max(1, viewport[0]), max(1, viewport[1]))
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, max(1, width), 0, max(1, height), -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def set_3d(self):
        """ Configure OpenGL to draw in 3d.

        """
        width, height = self.get_size()
        glEnable(GL_DEPTH_TEST)
        viewport = self.get_viewport_size()
        glViewport(0, 0, max(1, viewport[0]), max(1, viewport[1]))
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(65.0, width / float(height), 0.1, 60.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        x, y = self.rotation
        glRotatef(x, 0, 1, 0)
        glRotatef(-y, math.cos(math.radians(x)), 0, math.sin(math.radians(x)))
        x, y, z = self.position
        glTranslatef(-x, -y, -z)

    def on_draw(self):
        """ Called by pyglet to draw the canvas.

        """
        self.clear()
        # sky.blit(0, 0)
        self.set_3d()
        glColor3d(1, 1, 1)
        if not self.openMenu:
            self.model.batch.draw()
            self.draw_focused_block()
        self.set_2d()
        self.draw_label()
        # self.draw_inven()
        self.draw_reticle()
        self.draw_inventory()
        self.draw_menu()
        # self.inven_image(anchor_x='center', anchor_y='center')
        # self.image_sprite.draw()

    def draw_menu(self):
        if self.openMenu:
            self.bg.draw()
            for i in self.shown_menu:
                i.draw()

    def draw_focused_block(self):
        """ Draw block edges around the block that is currently under the
        crosshairs.

        """
        vector = self.get_sight_vector()
        block = self.model.hit_test(self.position, vector)[0]
        if block:
            x, y, z = block
            vertex_data = cube_vertices(x, y, z, 0.50)  # 51
            glColor3d(0, 0, 0)
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            pyglet.graphics.draw(24, GL_QUADS, ('v3f/static', vertex_data))
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    def draw_label(self):
        """ Draw the label in the top left of the screen.

        """
        x, y, z = self.position

        self.label.text = f'Beta 0.0.5 Fps: {pyglet.clock.get_fps()} ({x}, {y}, {z}) ' \
                          f'{len(self.model._shown)} / {len(self.model.world)}'
        # Beta 0.0.4 Fps: %02d (%.2f, %.2f, %.2f) %d / %d
        self.label.draw()

    def draw_reticle(self):
        """ Draw the crosshairs in the center of the screen.

        """
        glColor3d(255, 225, 225)
        self.reticle.draw(GL_LINES)

    def draw_inventory(self):
        glColor3d(255, 225, 225)
        self.bar.draw()
        for i in range(len(self.hotBar)):
            t = self.model.blocksSprites[self.hotBar[i]]
            t.width = 32
            t.height = 32
            t.blit(6 + i * 40, 6)
        if self.toggleInv:
            h = self.height
            for i in range(len(self.inventory)):
                for z in range(len(self.inventory[i])):
                    if self.inventory[i][z] != "":
                        img = self.model.blocksSprites[self.inventory[i][z]]
                        img.width = 32
                        img.height = 32
                        img.blit(z * 35, h - i * 35 - 35)
            if self.moveBlock[2] != "":
                img = self.model.blocksSprites[self.moveBlock[2]]
                img.width = 32
                img.height = 32
                img.blit(self.moveBlock[0], self.moveBlock[1])
