import git
import os
import fnmatch

from difflib import ndiff, SequenceMatcher
from pydoc import pager
from argparse import ArgumentParser
from pathlib import Path
from breaker import wrap_lines, wrap_text, pad_right

Pathes = [
    "*.tex"
]


def surround(text, i, j, start, end):
    add_head = False
    r = ""
    while i < j:
        c = text[i]
        i += 1
        if c == '\n':
            if add_head:
                r += end
                add_head = False
            r += c
            continue

        if not add_head:
            r += start
            add_head = True
        r += c
    if add_head:
        r += end

    return r


def wrap_green(text, i, j):
    return surround(text, i, j, "\x1b[32;49;1m", "\x1b[0m")


def wrap_red(text, i, j):
    return surround(text, i, j, "\x1b[31;49;9;1m", "\x1b[0m")


def wrap_yellow(text, i, j):
    return surround(text, i, j, "\x1b[33;49;4;1m", "\x1b[0m")


def wrap_line_marker(text):
    return f"\x1b[34;49;1;3m{text}\x1b[0m"


def wrap_width(w):
    return w + 2


def blobstr(blob):
    if not blob:
        return ""
    return blob.data_stream.read().decode('utf-8')


def get_ndiff(a, b):
    lines = 0
    i = 0
    dl = list(ndiff(a, b))

    l, r = "", ""
    state = " "
    for diff_line in dl:
        if diff_line.startswith("? "):
            continue

        if diff_line.startswith("  "):
            lines += 1
            continue

        line = diff_line[2:]
        if diff_line[0] == '-':
            if state == '-':
                yield (lines, "", r)
                lines += 1
                yield (lines, "", line)
            elif state == '+':
                lines += 1
                yield (lines, l, line)
            else:
                r = line
                state = '-'
                continue
            state = ' '
        else:
            if state == '+':
                yield (lines, l, "")
                lines += 1
                yield (lines, line, "")
            elif state == '-':
                lines += 1
                yield (lines, line, r)
            else:
                l = line
                state = '+'
                continue
            state = ' '


def render_line_diff(a, b):
    s = SequenceMatcher(lambda x: x in '\n\r', a, b)
    a_ = ""
    b_ = ""
    for tag, i1, i2, j1, j2 in s.get_opcodes():
        if tag == "delete":
            a_ += wrap_green(a, i1, i2)
        elif tag == "replace":
            a_ += wrap_yellow(a, i1, i2)
            b_ += wrap_yellow(b, j1, j2)
        elif tag == "insert":
            b_ += wrap_red(b, j1, j2)
        else:
            a_ += a[i1:i2]
            b_ += b[j1:j2]
    return (a_, b_)


def diffblob(blob_a, blob_b, width):
    a = blobstr(blob_a).splitlines()
    b = blobstr(blob_b).splitlines()

    la = []
    lb = []

    for line, l, r in get_ndiff(a, b):
        mark = wrap_line_marker(f"@@ {line}")
        la.append("")
        la.append(mark)

        lb.append("")
        lb.append(mark)

        l_ = wrap_text(l, width)
        r_ = wrap_text(r, width)
        l_, r_ = render_line_diff("\n".join(l_), "\n".join(r_))

        la += l_.splitlines()
        lb += r_.splitlines()

        len_diff = len(la) - len(lb)
        if len_diff < 0:
            la += [""] * abs(len_diff)
        else:
            lb += [""] * abs(len_diff)

    return (la, lb)


class DiffEntry:
    def __init__(self, diff_obj: git.Diff, accessor):
        self.__do = diff_obj
        self.mode = getattr(diff_obj, f"{accessor}_mode", None)
        self.path = getattr(diff_obj, f"{accessor}_path", None)
        self.blob = getattr(diff_obj, f"{accessor}_blob", None)

    def absent(self):
        return self.mode is None

    def comparef(self, other, width=20):
        this, that = diffblob(self.blob, other.blob, width)

        len_diff = len(this) - len(that)
        if len_diff < 0:
            this += [""] * abs(len_diff)

        else:
            that += [""] * abs(len_diff)

        merged = []
        for l_this, l_that in zip(this, that):
            l_this = pad_right(l_this, wrap_width(width))
            merged.append(f"  {l_this}" + "|".ljust(4) + f"{l_that}")

        return merged

    @staticmethod
    def check_path(a, b, path_prefixes):
        if a.path != b.path:
            return False

        for path_prefix in path_prefixes:
            if fnmatch.fnmatch(a.path, path_prefix):
                return True

        return False

    @staticmethod
    def get_attr_union(a, b, accessor):
        _a = getattr(a, accessor, None)
        _b = getattr(b, accessor, None)
        return _b if _b else _a


class DiffAnchor:
    def __init__(self, name, obj):
        self.__obj = obj
        self.__name = name

    def obj(self):
        return self.__obj

    def __str__(self):
        _hash = "n/a"
        if self.__obj and hasattr(self.__obj, "hexsha"):
            _hash = self.__obj.hexsha[:8]
        return f"({self.__name}) {_hash}"

    def diff(self, other):
        if not self.__obj:
            return other.obj().diff(None, R=True)

        return self.__obj.diff(other.obj())

    @staticmethod
    def create(repo, name=None, staged=False, dirty=False):
        if dirty:
            return DiffAnchor("<UNSTAGED>", None)
        if staged:
            return DiffAnchor("<STAGED>", repo.index)

        name = "HEAD" if not name else name
        commit = repo.commit(name)
        return DiffAnchor(name, commit)


class Diff:
    def __init__(self, repo, a, ref):
        self.__commit_A = a
        self.__commit_R = ref
        self.__repo = repo

        self.__diff = self.__commit_R.diff(self.__commit_A)

    def format(self, width):
        lines = []

        columnA = "cmp: " + str(self.__commit_A)
        columnB = "ref: " + str(self.__commit_R)
        colHeader = pad_right(columnB, wrap_width(width)) + columnA

        for obj in self.__diff:
            diffed = DiffEntry(obj, "a")
            reference = DiffEntry(obj, "b")

            if not DiffEntry.check_path(diffed, reference, Pathes):
                continue

            path = DiffEntry.get_attr_union(diffed, reference, "path")

            lines += [
                f"#### {path} ####",
                "  " + colHeader,
                "",
                *reference.comparef(diffed, width),
                "",
                ""
            ]

        return "\n".join(lines)


def main():
    global Pathes
    parser = ArgumentParser(__pytool__,
                            description="diff tool designed for comparing changes across " +
                                        "literary paragraph with improved readability")

    parser.add_argument("compared", nargs='?', default='HEAD',
                        help="Point to compare (default: HEAD)")
    parser.add_argument("-r", "--ref",
                        required=False, default=None,
                        help="Referencing point (default: HEAD)")
    parser.add_argument("--width",
                        type=int, required=False, default=24,
                        help="Max line width when formatted for display (default: 24)")
    parser.add_argument("-s", "--staged",
                        required=False, action='store_true',
                        help="Referencing from current index")
    parser.add_argument("-d", "--dirty",
                        required=False, action='store_true',
                        help="Referencing from unstaged files")
    parser.add_argument("-i", "--include", action='append', required=False)

    args = parser.parse_args()
    repo = git.Repo(os.getcwd(), search_parent_directories=True)

    includes = args.include
    if includes:
        Pathes.clear()
        Pathes += includes
    
    if not args.staged and args.dirty:
        args.staged = True
        print("WARN: using dirty will force comparison with staged.")

    anchorA = DiffAnchor.create(repo, args.compared, dirty=args.dirty)
    anchorR = DiffAnchor.create(repo, args.ref, args.staged)

    diff = Diff(repo, anchorA, ref=anchorR)

    out = []
    out.append(diff.format(args.width))

    pager("\n".join(out))


if __name__ == "__pytool__":
    main()
