
class FunctionBind:

    def __init__(self, func, *args):
        if not callable(func):
            raise TypeError("'func' parameter is not callable object")
        self.func = func
        self.args = args

    def __call__(self):
        return self.func(*self.args)
