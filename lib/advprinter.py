
class AdvPrinter:
    def __init__(self, lvl = 0, indent_w = 4):
        self.__level  = lvl
        self.__indetw = indent_w
        self.__indent = " " * (lvl * indent_w)

    def print(self, *args):
        s = " ".join([str(x) for x in args])
        print(self.__indent + s)

    def next_level(self):
        return AdvPrinter(self.__level + 1, self.__indetw)
