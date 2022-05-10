from Minecraft.utils import warns
from Minecraft.utils.bind import FunctionBind


class Block:
    def __init__(self, position: tuple, texture, shown: dict, _shown: dict):
        self.position = position
        self.texture = texture
        self.shown = shown
        self._shown = _shown
        self.is_shown = False

    def show(self, show_method: FunctionBind):
        warns.maybe_unused(self)
        show_method()
        self.is_shown = True

    #     if self.is_shown:
    #         return
    #     self.shown[self.position] = self.texture
    #     if immediate:
    #         self._show(batch, atlases)
    #     else:
    #         self.queue.put((self._show, batch, atlases))
    #
    # def _show(self, batch, atlases):
    #     x, y, z = self.position
    #     vertex_data = cube_vertices(x, y, z, 0.5)
    #     texture_data = list(self.texture[0])
    #     # create vertex list
    #     # FIXME_ Maybe `add_indexed()` should be used instead
    #     self._shown[self.position] = batch.add(24, GL_QUADS, atlases[self.texture[1]][0],
    #                                            (f'v3f/static', vertex_data),
    #                                            (f't2f/static', texture_data))


    # def show_block(self, position, immediate=True):
    #     """ Show the block at the given `position`. This method assumes the
    #     block has already been added with add_block()
    #
    #     Parameters
    #     ----------
    #     position : tuple of len 3
    #         The (x, y, z) position of the block to show.
    #     immediate : bool
    #         Whether or not to show the block immediately.
    #
    #     """
    #
    #     def _show_block(self, position, texture):
    #         """ Private implementation of the `show_block()` method.
    #
    #         Parameters
    #         ----------
    #         position : tuple of len 3
    #             The (x, y, z) position of the block to show.
    #         texture : list of len 3
    #             The coordinates of the texture squares. Use `tex_coords()` to
    #             generate.
    #
    #         """
