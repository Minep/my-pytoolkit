import textwrap
import pydoc


def _fmt_bold(x):
    return f"\x1b[39;49;1m{x}\x1b[0m"


def _fmt_it(x):
    return f"\x1b[39;49;3m{x}\x1b[0m"


def _fmt_underline(x):
    return f"\x1b[39;49;4m{x}\x1b[0m"


def _fmt_strike(x):
    return f"\x1b[39;49;9m{x}\x1b[0m"


class AdvPrinter:
    class Buffer:
        def __init__(self):
            self.__buffer = []

        def append(self, v):
            self.__buffer.append(v)

        def __str__(self):
            return "\n".join(self.__buffer)

    def __init__(self, lvl=0, indent_w=4, buffer=None):
        self.__level  = lvl
        self.__indetw = indent_w
        self.__indent = " " * (lvl * indent_w)
        self.__buffer = buffer

        if buffer:
            self.__do_print = lambda x: buffer.append(x)
        else:
            self.__do_print = lambda x: print(x)

    def __joinstr(self, *args):
        return " ".join([str(x) for x in args])

    def __print(self, *args, fmt_fn=None):
        s = self.__joinstr(*args)
        s = fmt_fn(s) if fmt_fn else s
        s = textwrap.indent(s, self.__indent)
        self.__do_print(s)

    def print(self, *args):
        self.__print(*args)

    def printb(self, *args):
        self.__print(*args, fmt_fn=_fmt_bold)

    def printblk(self, str_blk, nowrap=False):
        str_blk = textwrap.dedent(str_blk).strip()

        if not nowrap:
            strs = []
            for para in str_blk.split('\n\n'):
                para = para.replace('\n', ' ')
                strs += textwrap.wrap(para.strip(), width=70)
                strs.append("")

            str_blk = '\n'.join(strs)
        else:
            str_blk += "\n"

        str_blk = textwrap.indent(str_blk, self.__indent)
        self.__do_print(str_blk)

    def __get_derived(self, l):
        return AdvPrinter(l, self.__indetw, buffer=self.__buffer)
    
    def __lshift__(self, n):
        l = max(self.__level - n, 0)
        return self.__get_derived(l)

    def __rshift__(self, n):
        return self.__get_derived(self.__level + n)

class PydocAdvPrinter:
    def __init__(self, indent_w=4):
        self.__iw = indent_w
        self.__buf = AdvPrinter.Buffer()

    def __enter__(self):
        self.__instance = AdvPrinter(indent_w=self.__iw, buffer=self.__buf)
        return self.__instance

    def __exit__(self, *args):
        pydoc.pager(str(self.__buf))


