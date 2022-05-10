import math
import os
import random
import sys
from collections import deque
from copy import deepcopy
import time

import pyglet
from PIL import Image
from pyglet import image
from pyglet.gl import GL_QUADS
from pyglet.graphics import TextureGroup

from libs.noise_gen import NoiseGen, generate
from utils import warns


# music
music_list = ['world', 'world2', 'world3', 'world4']
player = pyglet.media.Player()
music = pyglet.media.load(f'music{os.sep}{random.choice(music_list)}.wav')
player.queue(music)
player.play()
debug_mode = 1
time_world = 0
time_music = 0

TICKS_PER_SEC = 120

# Size of sectors used to ease block loading.
SECTOR_SIZE = 16

WALKING_SPEED = 5
FLYING_SPEED = 15

CAVESW = 3
CAVESL = [20, 100]
CAVESNUM = 10

# sounds
soundpl = pyglet.media.Player()
sound = pyglet.media.load(f'sounds{os.sep}break.wav')
soundpl.queue(sound)

# finish
GRAVITY = 20.0
MAX_JUMP_HEIGHT = 1.5  # About the height of a block.
# To derive the formula for calculating jump speed, first solve
#    v_t = v_0 + a * t
# for the time at which you achieve maximum height, where a is the acceleration
# due to gravity and v_t = 0. This gives:
#    t = - v_0 / a
# Use t and the desired MAX_JUMP_HEIGHT to solve for v_0 (jump speed) in
#    s = s_0 + v_0 * t + (a * t^2) / 2
JUMP_SPEED = math.sqrt(2 * GRAVITY * MAX_JUMP_HEIGHT)
TERMINAL_VELOCITY = 90

PLAYER_HEIGHT = 2

if sys.version_info[0] >= 3:
    xrange = range


def cube_vertices(x, y, z, n):
    """ Return the vertices of the cube at position x, y, z with size 2*n.

    """
    return [
        x - n, y + n, z - n, x - n, y + n, z + n, x + n, y + n, z + n, x + n, y + n, z - n,  # top
        x - n, y - n, z - n, x + n, y - n, z - n, x + n, y - n, z + n, x - n, y - n, z + n,  # bottom
        x - n, y - n, z - n, x - n, y - n, z + n, x - n, y + n, z + n, x - n, y + n, z - n,  # left
        x + n, y - n, z + n, x + n, y - n, z - n, x + n, y + n, z - n, x + n, y + n, z + n,  # right
        x - n, y - n, z + n, x + n, y - n, z + n, x + n, y + n, z + n, x - n, y + n, z + n,  # front
        x + n, y - n, z - n, x - n, y - n, z - n, x - n, y + n, z - n, x + n, y + n, z - n,  # back
    ]


def tex_coordinate(x, y, n=8):
    """ Return the bounding vertices of the texture square.

    """
    m_ = 1.0 / n
    dx = x * m_
    dy = y * m_
    return dx, dy, dx + m_, dy, dx + m_, dy + m_, dx, dy + m_


def tex_coordinates(top, bottom, side):
    """ Return a list of the texture squares for the top, bottom and side. """
    top = tex_coordinate(*top)
    bottom = tex_coordinate(*bottom)
    side = tex_coordinate(*side)
    return [*top, *bottom, *side * 4]


def parseTexAtlas(path, mas):
    file = open(path, "r")
    data = file.readlines()
    stage = 0
    name = ""
    path = ""
    for i in data:
        for c in i:
            if c != "\n":
                if stage == 0:
                    if c != " ":
                        name += c
                    else:
                        stage += 1
                elif stage == 1:
                    if c == "$":
                        stage = 0
                        mas[name] = [TextureGroup(image.load(path).get_texture()), path]
                        name = ""
                        path = ""
                    elif c == "&":
                        stage = -1
                        mas[name] = [TextureGroup(image.load(path).get_texture()), path]
                    else:
                        path += c
    return mas


def parseBlocks(path, mas):
    name = ""
    n1 = ""
    n2 = ""
    tempN = ""
    texCords = []
    tags = []
    atlas = ""
    file = open(path, "r")
    data = file.readlines()
    stage = 0
    for i in data:
        for c in i:
            if c != "\n":
                if stage == 0:
                    if c != " ":
                        name += c
                    else:
                        stage += 1
                elif stage == 1:
                    if c == "#":
                        stage += 1
                    elif c == " ":
                        if n1 != "" and n2 != "":
                            texCords.append(tuple([int(n1), int(n2)]))
                            n1 = ""
                            n2 = ""
                    elif n1 == "":
                        n1 += c
                    elif n2 == "":
                        n2 += c
                elif stage == 2:
                    if c == "#":
                        stage += 1
                    else:
                        atlas += c
                elif stage == 3:
                    if c == "$":
                        mas[name] = [tex_coordinates(tuple(texCords[0]), tuple(texCords[1]),
                                                     tuple(texCords[2])), atlas, texCords, tags]
                        name = ""
                        n1 = ""
                        n2 = ""
                        atlas = ""
                        texCords = []
                        tags = []
                        stage = 0
                    elif c == "&":
                        mas[name] = [tex_coordinates(tuple(texCords[0]), tuple(texCords[1]),
                                                     tuple(texCords[2])), atlas, texCords, tags]
                        name = ""
                        n1 = ""
                        n2 = ""
                        atlas = ""
                        texCords = []
                        tags = []
                        stage = -1
                    elif c == " ":
                        tags.append(tempN)
                        tempN = ""
                    else:
                        tempN += c
    return mas


FACES = (
    (0, 1, 0),
    (0, -1, 0),
    (-1, 0, 0),
    (1, 0, 0),
    (0, 0, 1),
    (0, 0, -1),
)


def normalize(position):
    """ Accepts `position` of arbitrary precision and returns the block
    containing that position.

    Parameters
    ----------
    position : tuple of len 3

    Returns
    -------
    block_position : tuple of ints of len 3

    """
    x, y, z = position
    x, y, z = (int(round(x)), int(round(y)), int(round(z)))
    return x, y, z


def sectorize(position):
    """ Returns a tuple representing the sector for the given `position`.

    Parameters
    ----------
    position : tuple of len 3

    Returns
    -------
    sector : tuple of len 3

    """
    x, y, z = normalize(position)
    x, y, z = x // SECTOR_SIZE, y // SECTOR_SIZE, z // SECTOR_SIZE
    return x, 0, z


def _bound(mn, mx, v):
    if v <= mn:
        v = mx
    elif v >= mx:
        v = mn
    return v


class Model:

    def __init__(self):
        self.delta = 0

        # A Batch is a collection of vertex lists for batched rendering.
        self.batch = pyglet.graphics.Batch()

        # A TextureGroup manages an OpenGL texture.
        self.atlases = dict()
        self.blocks = dict()
        self.blocksAtlases = dict()
        self.blocksSpritesAtlases = dict()
        self.atlases = parseTexAtlas("atlas.atl", self.atlases)
        self.blocks = parseBlocks("blocks.bls", self.blocks)
        files = os.listdir(f"mods{os.sep}")
        for i in files:
            if i[-1] == "l":
                self.atlases = parseTexAtlas(f"mods{os.sep}" + i, self.atlases)
            elif i[-1] == "s":
                self.blocks = parseBlocks(f"mods{os.sep}" + i, self.blocks)
        for i in self.atlases.keys():
            pa = self.atlases[i][1]
            img = Image.open(pa)
            img = img.resize((img.size[0] // 2, img.size[1] // 2))
            p = f"tempFiles{os.sep}" + pa
            z = 0
            while True:
                if p[z] == os.sep:
                    p = p[:z]
                    break
                z += 1
            tempPath = ""
            for c in p:
                if c != os.sep:
                    tempPath += c
                else:
                    os.makedirs(tempPath)
            img.save(f"tempFiles{os.sep}" + pa)
            self.blocksSpritesAtlases[i] = image.load(f"tempFiles{os.sep}" + pa)

        # Block's sprite group
        self.blocksSprites = dict()
        for i in self.blocks.keys():
            self.blocksSprites[i] = self.blocksSpritesAtlases[self.blocks[i][1]].get_region(
                self.blocks[i][2][0][0] * 32, self.blocks[i][2][0][1] * 32, 32, 32
            )

        # A mapping from position to the texture of the block at that position.
        # This defines all the blocks that are currently in the world.
        self.world = {}

        # Same mapping as `world` but only contains blocks that are shown.
        self.shown = {}

        # Mapping from position to a pyglet `VertextList` for all shown blocks.
        self._shown = {}

        # Mapping from sector to a list of positions inside that sector.
        self.sectors = {}

        # Simple function queue implementation. The queue is populated with
        # _show_block() and _hide_block() calls
        self.queue = deque()

        self._initialize()

    def __getstate__(self):
        attributes = self.__dict__.copy()
        return attributes

    def __setstate__(self, state):
        self.__dict__ = state

    def get_vertex_list(self):
        return self._shown

    def _initialize(self):
        """ Initialize the world by placing all the blocks.

        """
        world_size = 30  # size of the world
        step_size = 1  # step size
        y = 0  # initial y height
        warns.maybe_unused(y)
        maxHeight = 30
        gen = NoiseGen(generate(world_size, maxHeight))
        world_size = world_size * 4
        start = 0

        # too lazy to do this properly lol
        heightMap = {}
        for x in xrange(start, world_size, step_size):
            for z in xrange(start, world_size, step_size):
                heightMap[z + x * world_size] = int(gen.getHeight(x, z))

        # Generate the world
        for x in xrange(0, world_size, step_size):
            for z in xrange(0, world_size, step_size):
                height = heightMap[z + x * world_size]
                if height < 17:
                    self.add_block((x, height, z), self.blocks["SAND"], immediate=True)
                    for y in range(height, 16):
                        self.add_block((x, y, z), self.blocks["WATER"], immediate=True)
                    for y in xrange(height - 1, 0, -1):
                        self.add_block((x, y, z), self.blocks["STONE"], immediate=True)
                    continue
                elif height < 18:
                    self.add_block((x, height, z), self.blocks["SAND"], immediate=True)
                else:
                    self.add_block((x, height, z), self.blocks["GRASS"], immediate=True)
                for y in xrange(height - 1, 0, -1):
                    self.add_block((x, y, z), self.blocks["STONE"], immediate=True)
                # Maybe add tree at this (x, z)
                if height > 10:
                    if random.randrange(0, 1000000) > 999900:
                        cobblestone = 2
                        for y in xrange(height + 0, height + cobblestone):
                            self.add_block((x, y, z), self.blocks["OLDR"], immediate=False)
                if height > 20:
                    if random.randrange(0, 1000) > 990:
                        treeHeight = random.randrange(3, 5)
                        # Tree trunk
                        GENERATABLETREES = [[self.blocks["WOOD"], self.blocks["BWOOD"]],
                                            [self.blocks["LEAF"], self.blocks["BLEAF"]]]
                        wind = random.randrange(0, len(GENERATABLETREES[0]))
                        for y in xrange(height + 1, height + treeHeight):
                            self.add_block((x, y, z), GENERATABLETREES[0][wind], immediate=False)
                        # Tree leaves
                        leafh = height + treeHeight
                        for lz in xrange(z + -1, z + 2):
                            for lx in xrange(x + -1, x + 2):
                                for ly in xrange(2):
                                    self.add_block((lx, leafh + ly, lz),
                                                   GENERATABLETREES[1][wind], immediate=False)
                        # for y in xrange(1):
                        # for x in xrange(1):
                        # self.add_block((x, y, z), OLDR, immediate=False)
        for i in range(CAVESNUM):
            looping = True
            x = random.randint(0, world_size)
            y = random.randint(0, world_size)
            z = random.randint(0, world_size)
            tx = x + random.randint(-10, 11)
            ty = y + random.randint(-10, 11)
            tz = z + random.randint(-10, 11)
            curlen = 0
            maxlen = random.randint(CAVESL[0], CAVESL[1])
            while looping:
                curlen += 1
                if curlen >= maxlen:
                    looping = False
                if tx == x:
                    tx = x + random.randint(-10, 11)
                    tx = _bound(0, world_size, tx)
                if ty == y:
                    ty = y + random.randint(-10, 11)
                    ty = _bound(0, 48, ty)
                if tz == z:
                    tz = z + random.randint(-10, 11)
                    tz = _bound(0, world_size, tz)
                if x < tx:
                    x += 1
                elif x > tx:
                    x -= 1
                if y < ty:
                    y += 1
                elif y > ty:
                    y -= 1
                if z < tz:
                    z += 1
                elif z > tz:
                    z -= 1

                w = random.randint(CAVESW - 1, CAVESW)
                for xx in range(-w, w):
                    for yy in range(-w, w):
                        for zz in range(-w, w):
                            if math.sqrt(xx * xx + yy * yy) <= w and math.sqrt(xx * xx + zz * zz) <= w:
                                if x + xx > 0 and y + yy > 0 and z + zz > 0:
                                    try:

                                        self.remove_block((x + xx, y + yy, z + zz), True)
                                    finally:
                                        pass
                x = _bound(0, world_size, x)
                z = _bound(0, world_size, z)
                y = _bound(0, 50, y)

    def hit_test(self, position, vector, max_distance=6):
        """ Line of sight search from current position. If a block is
        intersected it is returned, along with the block previously in the line
        of sight. If no block is found, return None, None.

        Parameters
        ----------
        position : tuple of len 3
            The (x, y, z) position to check visibility from.
        vector : tuple of len 3
            The line of sight vector.
        max_distance : int
            How many blocks away to search for a hit.

        """
        m_ = 8
        x, y, z = position
        dx, dy, dz = vector
        previous = None
        for _ in xrange(max_distance * m_):
            key_ = normalize((x, y, z))
            if key_ != previous and key_ in self.world:
                return key_, previous
            previous = key_
            x, y, z = x + dx / m_, y + dy / m_, z + dz / m_
        return None, None

    def exposed(self, position):
        """ Returns False is given `position` is surrounded on all 6 sides by
        blocks, True otherwise.

        """
        x, y, z = position
        for dx, dy, dz in FACES:
            if (x + dx, y + dy, z + dz) not in self.world:
                return True
        return False

    def add_block(self, position, texture, immediate=True):
        """ Add a block with the given `texture` and `position` to the world.

        Parameters
        ----------
        position : tuple of len 3
            The (x, y, z) position of the block to add.
        texture : list of len 3
            The coordinates of the texture squares. Use `tex_coords()` to
            generate.
        immediate : bool
            Whether or not to draw the block immediately.

        """
        if position in self.world:
            self.remove_block(position, immediate)
        self.world[position] = texture
        self.sectors.setdefault(sectorize(position), []).append(position)
        if immediate:
            if self.exposed(position):
                self.show_block(position)
            self.check_neighbors(position)

    def remove_block(self, position, immediate=True, by_player=False):
        """ Remove the block at the given `position`.

        Parameters
        ----------
        position : tuple of len 3
            The (x, y, z) position of the block to remove.
        immediate : bool
            Whether or not to immediately remove block from canvas.
        by_player : bool

        """
        try:
            del self.world[position]
            self.sectors[sectorize(position)].remove(position)
            if immediate:
                if position in self.shown:
                    self.hide_block(position)
                self.check_neighbors(position)
        except KeyError:
            pass
        finally:
            if by_player:
                pass

    def check_neighbors(self, position):
        """ Check all blocks surrounding `position` and ensure their visual
        state is current. This means hiding blocks that are not exposed and
        ensuring that all exposed blocks are shown. Usually used after a block
        is added or removed.

        """
        x, y, z = position
        for dx, dy, dz in FACES:
            key_ = (x + dx, y + dy, z + dz)
            if key_ not in self.world:
                continue
            if self.exposed(key_):
                if key_ not in self.shown:
                    self.show_block(key_)
            else:
                if key_ in self.shown:
                    self.hide_block(key_)

    def show_block(self, position, immediate=True):
        """ Show the block at the given `position`. This method assumes the
        block has already been added with add_block()

        Parameters
        ----------
        position : tuple of len 3
            The (x, y, z) position of the block to show.
        immediate : bool
            Whether or not to show the block immediately.

        """
        texture = self.world[position]
        self.shown[position] = texture
        if immediate:
            self._show_block(position, texture)
        else:
            self._enqueue(self._show_block, position, texture)

    def _show_block(self, position, texture):
        """ Private implementation of the `show_block()` method.

        Parameters
        ----------
        position : tuple of len 3
            The (x, y, z) position of the block to show.
        texture : list of len 3
            The coordinates of the texture squares. Use `tex_coords()` to
            generate.

        """
        x, y, z = position
        vertex_data = cube_vertices(x, y, z, 0.5)
        texture_data = list(texture[0])
        # create vertex list
        # FIXME_ Maybe `add_indexed()` should be used instead
        self._shown[position] = self.batch.add(24, GL_QUADS, self.atlases[texture[1]][0],
                                               (f'v3f/static', vertex_data),
                                               (f't2f/static', texture_data))
        """ Private implementation of the `show_block()` method.

        Parameters
        ----------
        position : tuple of len 3
            The (x, y, z) position of the block to show.
        texture : list of len 3
            The coordinates of the texture squares. Use `tex_coords()` to
            generate.

        """
        x, y, z = position
        vertex_data = cube_vertices(x, y, z, 0.5)
        texture_data = list(texture[0])
        # create vertex list
        # FIXME_ Maybe `add_indexed()` should be used instead
        self._shown[position] = self.batch.add(24, GL_QUADS, self.atlases[texture[1]][0],
                                               (f'v3f/static', vertex_data),
                                               (f't2f/static', texture_data))

    def hide_block(self, position, immediate=True):
        """ Hide the block at the given `position`. Hiding does not remove the
        block from the world.

        Parameters
        ----------
        position : tuple of len 3
            The (x, y, z) position of the block to hide.
        immediate : bool
            Whether or not to immediately remove the block from the canvas.

        """
        self.shown.pop(position)
        if immediate:
            self._hide_block(position)
        else:
            self._enqueue(self._hide_block, position)

    def _hide_block(self, position):
        """ Private implementation of the 'hide_block()` method.

        """
        self._shown.pop(position).delete()

    def show_sector(self, sector):
        """ Ensure all blocks in the given sector that should be shown are
        drawn to the canvas.

        """
        for position in self.sectors.get(sector, []):
            if position not in self.shown and self.exposed(position):
                self.show_block(position, False)

    def hide_sector(self, sector):
        """ Ensure all blocks in the given sector that should be hidden are
        removed from the canvas.

        """
        for position in self.sectors.get(sector, []):
            if position in self.shown:
                self.hide_block(position, False)

    def change_sectors(self, before, after):
        """ Move from sector `before` to sector `after`. A sector is a
        contiguous x, y sub-region of world. Sectors are used to speed up
        world rendering.

        """
        before_set = set()
        after_set = set()
        pad = 4
        for dx in xrange(-pad, pad + 1):
            for dy in [0]:  # xrange(-pad, pad + 1):
                for dz in xrange(-pad, pad + 1):
                    if dx ** 2 + dy ** 2 + dz ** 2 > (pad + 1) ** 2:
                        continue
                    if before:
                        x, y, z = before
                        before_set.add((x + dx, y + dy, z + dz))
                    if after:
                        x, y, z = after
                        after_set.add((x + dx, y + dy, z + dz))
        show = after_set - before_set
        hide = before_set - after_set
        for sector in show:
            self.show_sector(sector)
        for sector in hide:
            self.hide_sector(sector)

    def _enqueue(self, func, *args):
        """ Add `func` to the internal queue.

        """
        self.queue.append((func, args))

    def _dequeue(self):
        """ Pop the top function from the internal queue and call it.

        """
        func, args = self.queue.popleft()
        func(*args)

    def process_queue(self):
        """ Process the entire queue while taking periodic breaks. This allows
        the game loop to run smoothly. The queue contains calls to
        _show_block() and _hide_block() so this method should be called if
        add_block() or remove_block() was called with immediate=False

        """
        td = time.time()
        while self.queue and td - self.delta < 1.0 / TICKS_PER_SEC:
            self.delta = deepcopy(td)
            self._dequeue()

    def process_entire_queue(self):
        """ Process the entire queue with no breaks.

        """
        while self.queue:
            self._dequeue()
