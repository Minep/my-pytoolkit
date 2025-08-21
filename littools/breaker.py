import unicodedata
import math

WIDTH_TABLE = {
    "W": 1,
    "F": 1,
    "Na": 0.5,
    "H": 0.5,
    "A": 0.5,
    "N": 0.5
}

SPECIAL_LENGTH = {
    "—": 0.5,
    "…": 0.5,
    "\t": 3
}


def get_width(chr):
    if chr in SPECIAL_LENGTH:
        return SPECIAL_LENGTH[chr]

    w = unicodedata.east_asian_width(chr)
    return WIDTH_TABLE[w]


def sticky(chr):
    return chr in "-,.:;`)]}\"'~?!）】。，：；’”？！、～—》」』❳_*…"


def non_sticky(chr):
    return chr in "([{（【“‘《【「『❲\\"


class MaybeBreak:
    def __init__(self):
        pass

    def permitted(self):
        pass

    def get_char(self):
        return ""

    def get_width(self):
        return 0


class Box(MaybeBreak):
    def __init__(self, char="", prev=None):
        super().__init__()
        self.c = char
        self.__prev = prev
        self.__brk = unicodedata.name(char).startswith("CJK ")

        if not char:
            self.w = 0
            return

        self.w = get_width(char)

    def permitted(self):
        if isinstance(self.__prev, Glue):
            return self.__brk and self.__prev.sticky()
        return self.__brk

    def get_char(self):
        return self.c

    def get_width(self):
        return self.w


class Glue(MaybeBreak):
    def __init__(self, char, width=None, prev=None):
        super().__init__()
        self.__can_break = isinstance(prev, Box)
        self.__stickyness = not non_sticky(char)
        self.w = get_width(char) if char else 0
        self.c = char

        if width is not None:
            self.w = width

    def get_char(self):
        return self.c

    def get_width(self):
        return self.w

    def permitted(self):
        return self.__can_break and not self.__stickyness

    def sticky(self):
        return self.__stickyness


class Penalty(MaybeBreak):
    def __init__(self, val):
        super().__init__()
        self.p = val

    def permitted(self):
        return self.p < 0


def pack(blist, c):
    prev = None if not blist else blist[-1]

    if c.isspace() or non_sticky(c) or sticky(c):
        return Glue(c, prev=prev)

    return Box(c, prev=prev)


def break_oneline(blist, pos, max_width):
    cur_lines = []
    width = 0
    brkpoint = []

    while pos < len(blist):
        b = blist[pos]
        width += b.get_width()
        cur_lines.append(b.get_char())

        pos += 1

        if b.permitted():
            brkpoint.append(len(cur_lines) - 1)

        if isinstance(b, Penalty) and b.p < -1000:
            brkpoint.append(len(cur_lines))
            break

        if width > max_width:
            break

    if not brkpoint:
        brkpoint.append(len(cur_lines))


    best_brk = max(brkpoint)
    trimmed = len(cur_lines) - best_brk

    pos -= trimmed

    line = "".join(cur_lines[:best_brk])
    return (pos, line)


def apply_break(blist, max_width):
    lines = []

    pos = 0

    while pos < len(blist):
        pos, line = break_oneline(blist, pos, max_width)
        lines.append(line)

    return lines


def wrap_text(text, width):
    if not width:
        return [text]

    blist = []
    for c in text:
        blist.append(pack(blist, c))

    blist.append(Penalty(-100000))
    return apply_break(blist, width)


def wrap_lines(lines, width):
    wrapped = []
    for line in lines:
        wrapped += wrap_text(line, width)
    return wrapped


def pad_right(text, width):
    escaped = False
    w_ = 0
    for c in text:
        if escaped:
            escaped = not (c == 'm')
            continue
        elif c == '\x1b':
            escaped = True
            continue

        w_ += get_width(c)

    rest = int((width - w_) * 2)

    return text + (" " * rest)

def update_length_data(new_length_data):
    global SPECIAL_LENGTH

    SPECIAL_LENGTH.update(new_length_data)
