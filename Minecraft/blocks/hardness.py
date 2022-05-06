from types import SimpleNamespace

from Minecraft.utils import warns


def _seconds_to_ticks(seconds: float):
    return seconds * 20


class Hardness:
    def __init__(self, hardness: float):
        self.hardness = _seconds_to_ticks(hardness)

    def get_hardness(self, item_in_hand=None):
        warns.maybe_unused(item_in_hand)
        return self.hardness


blocks_hardness = SimpleNamespace(hardness={
    "GRASS": Hardness(1),
    "SAND": Hardness(1),
    "STONE": Hardness(5),
    ...: ...
})
