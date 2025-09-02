from utils import BinCalcException, get_rawrep
from .pte_utils import PteFormatBase
from config import BinConfig
from utils import sprint


class PteType:
    Page = 0
    Table = 1
    Block = 2

    @staticmethod
    def getstr(pte_type):
        if pte_type == PteType.Page:
            return "Page Descriptor"
        if pte_type == PteType.Table:
            return "Table Descriptor"
        return "Block Descriptor"

class Granule:
    G4K = 12
    G16K = 14
    G64K = 16


class Arm64PteFormatBase(PteFormatBase):
    def __init__(self, val, pte_type, level=3):
        super().__init__(val, pte_type, level)

    def init(self):
        self._gran = BinConfig.MmuPgGran[self._config]
        self._oabits = BinConfig.MmuPABits[self._config]

    def get_fields(self):
        return [
            ("Type", 1, 0)
        ]

    def _get_basic_info(self):
        infos = super()._get_basic_info()
        infos += [
            sprint("level:", self._level),
            sprint("type:", PteType.getstr(self._type))
        ]

        infos.append(sprint("OA width:", self._oabits))

        if self._gran == Granule.G64K:
            infos.append(sprint("granule:", "64K", f"({self._gran})"))
        elif self._gran == Granule.G16K:
            infos.append(sprint("granule:", "16K", f"({self._gran})"))
        elif self._gran == Granule.G4K:
            infos.append(sprint("granule:", "4K", f"({self._gran})"))

        return infos

    def print_explaination(self):
        super().print_explaination()

        print()
        print("ADDTIONAL")

        extracted = self.get_field_values()
        oa1, oa2 = None, None
        for e in extracted:
            if e.name == "OA1" or e.name == "OA":
                oa1 = e
            elif e.name == "OA2":
                oa2 = e

        oa = oa1.value << oa1.l
        if oa2:
            oa |= oa2.value << (oa1.h + 1)

        print("    Encoded Output Address (OA2 + OA1):", hex(oa))
        print()


class TableDescriptor(Arm64PteFormatBase):
    def __init__(self, val, level):
        super().__init__(val, PteType.Table, level)

    def get_fields(self):
        fields = [
            ("NSTable", 63, 63),
            ("APTable", 62, 61),
            ("UXN/XN", 60, 60),
            ("PXN", 59, 59)
        ]

        fields.append(("OA", 48, self._gran))

        if self._oabits == 52:
            if self._gran == Granule.G64K:
                fields.append(("TA", 15, 12))
            else:
                fields.append(("TA", 9, 8))

        fields += super().get_fields()

        return fields

low_attributes = [
    ("NSE/nG", 11, 11),
    ("AF", 10, 10),
    ("SH", 9, 8),
    ("AP", 7, 6),
    ("NS", 5, 5),
    ("AttrIdx", 4, 2)
]

high_attributes = [
    ("PBHA", 62, 59),
    ("UXN/XN", 54, 54),
    ("PXN", 53, 53),
    ("Contig", 52, 52),
    ("DBM", 51, 51),
    ("GP", 50, 50),
]

class BlockDescriptor(Arm64PteFormatBase):
    def __init__(self, val, level):
        super().__init__(val, PteType.Block, level)

    def get_fields(self):
        fields = [
            *high_attributes,
            *low_attributes,
            ("nT", 16, 16),
        ]

        n = 9 * (3 - self._level) + self._gran

        if self._oabits == 48:
            fields.append(("OA", 47, n))

        if self._oabits == 52:
            if self._gran == Granule.G64K:
                fields.append(("OA1", 47, n))
                fields.append(("OA2", 15, 12))
            else:
                fields.append(("OA1", 49, n))
                fields.append(("OA2", 9, 8))

                for i in range(fields):
                    n = fields[i][0]
                    if n == "SH":
                        fields.pop(i)

        fields += super().get_fields()

        return fields


class PageDescriptor(Arm64PteFormatBase):
    def __init__(self, val):
        super().__init__(val, PteType.Page, 3)

    def get_fields(self):
        fields = [
            *high_attributes,
            *low_attributes
        ]

        if self._oabits == 48:
            fields.append(("OA", 47, self._gran))

        if self._oabits == 52:
            if self._gran == Granule.G64K:
                fields.append(("OA1", 47, self._gran))
                fields.append(("OA2", 15, 12))
            else:
                fields.append(("OA1", 49, self._gran))
                fields.append(("OA2", 9, 8))

                for i in range(fields):
                    n = fields[i][0]
                    if n == "SH":
                        fields.pop(i)

        fields += super().get_fields()

        return fields

def get_format(val, level):
    pte_type = get_rawrep(val) & 0b11

    if pte_type == 0b01 and level == 3:
        return PageDescriptor(val)
    
    if pte_type == 0b01:
        return BlockDescriptor(val, level)
    
    if pte_type == 0b11 and level < 3:
        return TableDescriptor(val, level)

    raise BinCalcException(f"invalid pte with type: {bin(pte_type)} with level: {level}")


def interpret_pte(pte_val, level):
    if not 0 <= level < 4:
        raise BinCalcException(f"invalid pte level: {level}, expect 0~3")

    get_format(pte_val, level).print_explaination()
