
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

    @staticmethod
    def execute(executor, args: tuple):
        executor(*args)
