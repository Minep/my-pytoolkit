import gzip
import json

from lib.advprinter import PydocAdvPrinter

from utils import BitFieldValue, BitFieldExractor, arrange

from shared.context import Context
from difflib import get_close_matches


def _load_sysreg_db():
    path = Context.LocalFiles["sysregs/arm-sysregs.json.gz"]

    with gzip.open(path.absolute(), 'r') as f:
        return json.load(f)


def _get_register(db, name):
    if name in db:
        return db[name]

    return get_close_matches(name, list(db.keys()), n=20)


def _get_bitfield_val(field_alt):
    return [(k, v["msb"], v["lsb"]) for k, v in field_alt["fields"].items()]


def _print_field(p, field, val):
    pp = p >> 1
    ppp = p >> 2
    pppp = p >> 3

    p.printb(f"{field['name']}")
    pp.printblk(f"""
        {val},
        {hex(val)},
        {bin(val)}
    """, nowrap=True)

    pp.printb("DESCRIPTION")

    for alt in field['alts']:
        ppp.printb(alt["cond"])
        pppp.printblk(alt["desc"])

    pp.printb("VALUES")

    for alt in field['alts']:
        ppp.printb(alt["cond"])
        ppp.print()
        for val in alt["values"]:
            pppp.printb(val["val"])
            pppp.printblk(val["desc"])


def _print_encoding(p, reg):
    enc = reg["enc"]
    pp = p >> 1

    def parse(key):
        nonlocal enc
        try:
            return int(enc[key], 2)
        except Exception as e:
            return enc[key]

    p.printb("ENCODING")
    p.print()

    op0 = parse("op0")
    op1 = parse("op1")
    crn = parse("CRn")
    crm = parse("CRm")
    op2 = parse("op2")

    pp.print(f"s{op0}_{op1}_c{crn}_c{crm}_{op2}")


def interpret_fields(reg, val):
    with PydocAdvPrinter() as p:
        pp = p >> 1
        ppp = p >> 2

        p.printb(reg["name"])
        pp.print(reg["desc"])

        p.print()
        if reg.get("enc", None):
            _print_encoding(p, reg)
        else:
            p.printb("MEMORY MAPPED")

        sysreg_fields = reg["fields"]
        
        pp.print()
        for field_alt in sysreg_fields:
            cond = field_alt["cond"]
            if cond:
                p.printb(cond)
            else:
                p.printb("TYPICAL")

            fields = _get_bitfield_val(field_alt)
            extractor = BitFieldExractor(fields)

            printable, extracted = extractor.extract_colored(val)
            
            pp.print()
            pp.print(printable)
            pp.print()

            pp.print(arrange(extracted))
            
            pp.print()
            pp.printb("FIELDS")

            for bf in extracted:
                field = field_alt["fields"][bf.name]
                _print_field(ppp, field, bf.value)


class Arm64SysRegInterpreter:
    def __init__(self):
        self.__regfile = _load_sysreg_db()

    def interprete(self, name, val):
        maybereg = _get_register(self.__regfile, name)

        if not isinstance(maybereg, list):
            interpret_fields(maybereg, val)
            return

        with PydocAdvPrinter() as p:
            p.printb(f"Possible match for '{name}'")

            pp = p >> 1
            for k in maybereg:
                pp.print(k)
