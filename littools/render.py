from xml.dom.minidom import Node, Text, parse
from pathlib import Path
from argparse import ArgumentParser
import textwrap
import unicodedata

from breaker import wrap_text, get_width, update_length_data, sticky, non_sticky


def center_justify(text, width):
    w_ = sum([get_width(c) for c in text])

    rest = width - w_
    rhalf = int((rest) / 2) * 2
    lhalf = int(rest - rhalf) * 2

    return (" " * rhalf) + text + (" " * lhalf)


class TagBinding:
    def __init__(self, name, subs, expand_all=False):
        self.__subs = [*subs]
        self.__name = name
        self.__expand_all = expand_all

    def bindable(self, node):
        return node.tagName == self.__name

    def emit(self, writer, text):
        pass

    def process(self, writer, node):
        q = list(reversed([*node.childNodes]))

        while len(q) > 0:
            child = q.pop()

            if isinstance(child, Text):
                self.emit(writer, child.nodeValue)
                continue

            processed = False
            for sub in self.__subs:
                if not sub.bindable(child):
                    continue

                sub.process(writer, child)
                processed = True
                break

            if processed or not self.__expand_all:
                continue

            q += reversed(child.childNodes)


class CounterTable:
    def __init__(self):
        self._counters = {}

    def add_counter(self, name, val=0):
        self._counters[name] = val

    def step_counter(self, name, dt=1):
        self._counters[name] += dt

    def get_counter(self, name):
        return self._counters[name]

    def has_counter(self, name):
        return name in self._counters

    def rm_counter(self, name):
        del self._counters[name]


class IntermediateWriter:
    class Token:
        def __init__(self, level, content="", **attrs):
            self.level = level
            self.content = content
            self.attrs = {**attrs}

        def set_attrs(self, **args):
            self.attrs.update(args)

        def expand_content(self, content):
            self.content += content

    def __init__(self):
        self.__cur_level = 0
        self.tokens = []
        self.cntab = CounterTable()

    def put_text(self, text, **attr):
        tok = IntermediateWriter.Token(self.__cur_level, text)
        tok.set_attrs(**attr)
        tok.set_attrs(type="text")

        self.tokens.append(tok)

    def put_title(self, title):
        cnt = [self.cntab.get_counter(x)
               for x in range(1, self.__cur_level + 1)]
        tok = IntermediateWriter.Token(
            self.__cur_level, title, type="title", counter=cnt)
        self.tokens.append(tok)

    def put_break(self):
        tok = IntermediateWriter.Token(self.__cur_level, type="brk")
        self.tokens.append(tok)

    def push_level(self):
        self.__cur_level += 1
        level_tok = IntermediateWriter.Token(self.__cur_level, type="level")
        self.tokens.append(level_tok)

        level = self.__cur_level
        if not self.cntab.has_counter(level):
            self.cntab.add_counter(level)
        self.cntab.step_counter(level)

    def pop_level(self):
        for k in list(self.cntab._counters.keys()):
            if not isinstance(k, int):
                continue

            if self.__cur_level < k:
                self.cntab.rm_counter(k)

        level_tok = IntermediateWriter.Token(
            self.__cur_level, type="level-end")

        self.__cur_level -= 1
        self.tokens.append(level_tok)

class WordCounter:
    def __init__(self):
        self.__counter = {}

    def add_counter(self, name, fn):
        self.__counter[name] = fn
    
    def next_chunk(self, imw, idx, level):
        i = idx
        found = False
        start = -1
        end = -1
        title = ""

        while i < len(imw.tokens):
            tok = imw.tokens[i]
            i += 1

            l = tok.level
            t = tok.attrs.get("type", "")

            if t.startswith("level") and l != level:
                continue

            if not found and t == "level":
                start = i
                found = True
            elif found and t == "level-end":
                end = i
                break

            if found and t == "title" and l == level:
                title = tok.content

        if start == -1:
            return (False, 0, 0, "")

        return (True, start, end, title)

    def count(self, imw, level = 1):
        cnts = {}
        idx = 0

        for k in self.__counter.keys():
            cnts[k] = 0

        while True:
            n, start, end, name = self.next_chunk(imw, idx, level)

            if not n:
                break

            print(name)
            for k, v in self.__counter.items():
                n_ = 0
                for tok in imw.tokens[start:end]:
                    cnt = tok.content.strip()
                    n_ += v(cnt)
                cnts[k] += n_
                print(f" * {k}: {n_}")
            print()

            idx = end - 1

        print("total")
        for k, v in cnts.items():
            print(f" * {k}: {v}")


class GenericBlockBinding(TagBinding):
    def __init__(self, name, subs=[]):
        super().__init__(name, subs)

    @staticmethod
    def of(name, subs=[]):
        return GenericBlockBinding(name, subs)

    def process(self, writer, node):
        print("Processed: ", node.tagName, f"({node.getAttribute('xml:id')})")
        writer.push_level()
        super().process(writer, node)
        writer.pop_level()


class ParaBinding(TagBinding):
    def __init__(self, subs=[]):
        super().__init__("para", subs, expand_all=True)

    def emit(self, writer, text):
        writer.put_text(text)

    def process(self, writer, node):

        for p in node.getElementsByTagName("p"):
            super().process(writer, p)
            writer.put_break()

        writer.put_break()


class TitleBinding(TagBinding):
    def __init__(self, subs=[]):
        super().__init__("title", subs)
        self.__has_valid_title = False

    def emit(self, writer, text):
        writer.put_title(text)
        self.__has_valid_title = True

    def process(self, writer, node):
        self.__has_valid_title = False
        super().process(writer, node)

        if not self.__has_valid_title:
            writer.put_title("")


class RefBinding(TagBinding):
    def __init__(self, subs=[]):
        super().__init__("ref", subs)

    def emit(self, writer, text):
        writer.put_text(text)


class ErrorBinding(TagBinding):
    def __init__(self, subs=[]):
        super().__init__("ERROR", subs)

    def emit(self, writer, text):
        pass


class TextBinding(TagBinding):
    def __init__(self, subs=[]):
        super().__init__("text", subs)

    def emit(self, writer, text):
        writer.put_text(text, font=self.__node.getAttribute("font"))

    def bindable(self, node):
        return node.tagName == "text"

    def process(self, writer, node):
        self.__node = node
        super().process(writer, node)


class TransformerBase:
    def __init__(self):
        self._counters = {}
        self.lines = []
        self.w = 0
        pass

    def render(self, itokens):
        pass

    def flush_and_export(self, file):
        with file.open('w') as f:
            processed = []
            for l in self.lines:
                str_ = wrap_text(l, self.w)
                processed += str_

            f.write("\n".join(processed))
        self.lines = [""]


class TxtTransformer(TransformerBase):
    def __init__(self, width):
        super().__init__()

        self.w = width

    def render(self, iwriter):
        self.lines = [""]
        line = ""
        for token in iwriter.tokens:
            type_ = token.attrs.get("type", "text")

            if type_ == "text":
                line += token.content.strip()
                continue

            if type_ == "brk":
                self.lines.append(line)
                line = ""
                continue

            if type_ == "title":
                counter = token.attrs["counter"]

                if len(counter) > 1:
                    num = ".".join([str(x) for x in counter[1:]])
                    title = ' '.join([f"({num})", f"{token.content}"])
                else:
                    title = token.content

                self.lines.append("")
                self.lines.append(center_justify(title, self.w))
                continue


class MarkdownTransformer(TransformerBase):
    def __init__(self, w):
        super().__init__()

        self.w = w

    def render(self, iwriter):
        self.lines = [""]
        line = ""
        for token in iwriter.tokens:
            type_ = token.attrs.get("type", "text")

            if type_ == "text":
                font_style = token.attrs.get("font", "")
                l = token.content.strip()

                if len(l) == 0:
                    continue

                if font_style == "italic":
                    l = f" *{l}* "
                elif font_style == "bold":
                    l = f" **{l}** "

                line += l
                continue

            if type_ == "brk":
                self.lines.append(line)
                line = ""
                continue

            if type_ == "title":
                counter = token.attrs["counter"]

                if len(counter) > 1:
                    num = ".".join([str(x) for x in counter[1:]])
                    title = ' '.join([f"({num})", f"{token.content}"])
                else:
                    title = token.content

                title = f"{('#' * len(counter))} {title}"

                self.lines.append(title)
                self.lines.append("")
                continue


def get_transformer(name, args):
    if name == "md":
        return MarkdownTransformer(args.width)

    if name == "txt":
        return TxtTransformer(args.width)


def get_binder():
    title = TitleBinding()
    ref = RefBinding()
    err = ErrorBinding()
    ita = TextBinding()

    para = ParaBinding([
        ref,
        err,
        ita
    ])
    
    subsect = GenericBlockBinding.of("subsection", [
        title,
        para
    ])
    
    sect = GenericBlockBinding.of("section", [
        title,
        para,
        subsect
    ])

    chapt = GenericBlockBinding.of("chapter", [
        sect,
        para,
        title
    ])

    part = GenericBlockBinding.of("part", [
        title,
        chapt
    ])

    doc = GenericBlockBinding.of("document", [
        title,
        chapt,
        part
    ])

    return doc


def count_characters(v):
    return len(v)

def count_char_no_punct(v):
    i = 0
    for c in v:
        if sticky(c) or non_sticky(c):
            continue
        i += 1

    return i

def render(docobj, args):
    counter = WordCounter()
    counter.add_counter("字数（含标点）", count_characters)
    counter.add_counter("字数", count_char_no_punct)

    binder = get_binder()
    wr = IntermediateWriter()
    trn = get_transformer(args.fmt, args)
    out_path = args.out

    # if not args.split:
    #    out_path = args.out.parent

    binder.process(wr, docobj)
    trn.render(wr)
    trn.flush_and_export(out_path)

    counter.count(wr, 2)


def main():
    parser = ArgumentParser(prog=__pytool__)
    parser.add_argument("xml_file")
    parser.add_argument("--fmt", default='txt')
    parser.add_argument("--out")
    parser.add_argument("--width", default=24)
    parser.add_argument("--split", action='store_true')

    opt = parser.parse_args()

    opt.out = Path(opt.out)

    update_length_data({
        "—": 1,
        "…": 1
    })
    do = parse(opt.xml_file).documentElement
    render(do, opt)


if __name__ == "__pytool__":
    main()
