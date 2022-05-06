from libs.Button import Button

class Menu:
    def __init__(self):
        self.widgets = []
        self.funtions = dict()

    def handle(self):
        for i in self.widgets:


    def draw(self):
        for i in self.widgets:
            i.draw([])