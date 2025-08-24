from utils import BinCalcException, get_rawrep
from state import global_state
from config import BinConfig

from .pte_utils import PteFormatBase

from textwrap import indent


x86_64_pte_common_fields = [
    ("Valid", 0, 0),
    ("R/W", 1, 1),
    ("U/S", 2, 2),
    ("PWT", 3, 3),
    ("PCD", 4, 4),
    ("A",   5, 5),
    ("XD", 63, 63)
]


class PteType:
    Page = 0
    Table = 1
    Huge = 2

    @staticmethod
    def getstr(pte_type):
        if pte_type == PteType.Page:
            return "Base Page"
        if pte_type == PteType.Table:
            return "Table Page"
        return "Huge Page"

class x86PteFormatBase(PteFormatBase):
    def __init__(self, val, pte_type, level=3):
        super().__init__(val, pte_type, level)

    def get_fields(self):
        return x86_64_pte_common_fields

    @staticmethod
    def get_pte_type(val, level):
        if level == 3:
            return PteType.Page

        maybe_huge = (get_rawrep(val) & (1 << 7)) != 0
        if not maybe_huge or level == 0:
            return PteType.Table

        return PteType.Huge

    def get_field_comment(self, field):
        name = field.name
        val  = field.value

        if name == "R/W":
            return "R" if val == 0 else "W"
        if name == "U/S":
            return "User" if val == 1 else "Kernel"
        if name == "XD":
            return "X" if val == 0 else "nX"
        if name == "PWT":
            return "write-through" if val == 1 else None
        if name == "PCD":
            return "dcache-bypass" if val == 1 else None
        return None
    
    def _get_basic_info(self):
        infos = super()._get_basic_info()

        infos += [
            f"translation level: {self._level} (0~3)",
            "type: " + PteType.getstr(self._type)
        ]

        return infos


class PagePte(x86PteFormatBase):
    def __init__(self, val):
        super().__init__(val, PteType.Page, 3)

    def get_fields(self):
        f = super().get_fields()
        bits = BinConfig.MmuPABits[self._config]

        return [
            *f,
            ("Dirty", 6, 6),
            ("Global", 8, 8),
            ("PAT", 7, 7),
            ("PA", bits, 12)
        ]

class HugePte(x86PteFormatBase):
    def __init__(self, val, level):
        super().__init__(val, PteType.Huge, level)

    def get_fields(self):
        f = super().get_fields()
        bits = BinConfig.MmuPABits[self._config]

        return [
            *f,
            ("PAT", 12, 12),
            ("Prot.Key", 62, 59),
            ("PA", bits, 13)
        ]

    def get_field_comment(self, f):
        if f.name == "PA":
            l = 3 - self._level
            mask = (1 << (8 * l)) - 1
            val = f.value & mask
            return "UNALIGN"

        return super().get_field_comment(f)


class TablePage(x86PteFormatBase):
    def __init__(self, val, level):
        super().__init__(val, PteType.Table, level)

    def get_fields(self):
        f = super().get_fields()
        bits = BinConfig.MmuPABits[self._config]

        return [
            *f,
            ("PA", bits, 12)
        ]


def get_format(val, level):
    ptype = x86PteFormatBase.get_pte_type(val, level)

    if ptype == PteType.Page:
        return PagePte(val)
    if ptype == PteType.Huge:
        return HugePte(val, level)

    return TablePage(val, level)


def interpret_pte(pte_val, level):
    if not 0 <= level < 4:
        raise BinCalcException(f"invalid pte level: {level}, expect 0~3")

    get_format(pte_val, level).print_explaination()
