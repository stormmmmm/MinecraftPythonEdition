
class MinecraftCommand:
    def __init__(self, executor, *args):
        """
        executor: function, which execute command
        *args: arguments of command
        """
        if not callable(executor):
            raise TypeError("'executor' field is not callable object")
        self.executor = executor
        self.args: tuple = args

    def execute(self):
        f = self.executor
        f(*self.args)
