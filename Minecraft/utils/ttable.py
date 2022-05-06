import math
from array import array


class SinTable:
    def __init__(self):
        self.sin_table = array('f')
        i = 0
        while i <= 360:
            self.sin_table.append(math.sin(i))
            i += 0.1

    def get(self, num: float):
        try:
            return self.sin_table[int(num * 10)]
        except IndexError:
            return math.sin(num)


class CosTable:
    def __init__(self):
        self.cos_table = array('f')
        i = 0
        while i <= 360:
            self.cos_table.append(math.sin(i))
            i += 0.1

    def get(self, num: float):
        try:
            return self.cos_table[int(num * 10)]
        except IndexError:
            return math.sin(num)


class SinCosTable(SinTable, CosTable):
    def __init__(self):
        super(SinTable, self).__init__()
        super(CosTable, self).__init__()

    def get_sin(self, num: float):
        return super(SinTable).get(num)

    def get_cos(self, num: float):
        return super(CosTable).get(num)

