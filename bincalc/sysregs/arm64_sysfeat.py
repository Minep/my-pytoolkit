
import gzip
import json

from lib.advprinter import PydocAdvPrinter

from shared.context import Context
from difflib import get_close_matches


def _load_sysfeat_db():
    path = Context.LocalFiles["sysregs/arm64-features.json.gz"]

    with gzip.open(path.absolute(), 'r') as f:
        return json.load(f)


def _get_feature(db, name):
    if name in db:
        return db[name]

    return get_close_matches(name, list(db.keys()), n=20)


def print_desc(p, desc):
    if not isinstance(desc, list):
        p.printblk(desc)
        p.print()
        return

    for e in desc:
        print_desc(p >> 1, e)


def print_feature(name, feat):
    with PydocAdvPrinter() as p:
        pp = p >> 1
        ppp = p >> 2

        p.printb("ARM64 FEATURE")

        pp.print()
        pp.print(name)
        pp.print()

        pp.printb("DEFINITION")
        pp.print()

        ppp.printblk(feat["def"])
        ppp.print()

        pp.printb("DESCRIPTION")
        pp.print()

        print_desc(ppp, feat["desc"])
        ppp.print()


class Arm64Features:
    def __init__(self):
        self.__regfile = _load_sysfeat_db()

    def query(self, name):
        maybereg = _get_feature(self.__regfile, name)

        if not isinstance(maybereg, list):
            print_feature(name, maybereg)
            return

        with PydocAdvPrinter() as p:
            p.printb(f"Possible match for '{name}'")

            pp = p >> 1
            for k in maybereg:
                pp.print(k)

