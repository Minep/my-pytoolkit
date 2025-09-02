from state import global_state
from config import BinConfig

from utils import fixbin, fixhex, get_rawrep
from lib.advprinter import AdvPrinter


class Ptep:
    class State:
        def __init__(self, offset):
            self.level = 0
            self.offset = offset

        def __str__(self):
            return f"L{self.level} @{self.offset:03d}"

    def __init__(self, val):
        self.__param = _get_param()
        self.mis_alignment = False
        self.transition = []

        if isinstance(val, list):
            self.transition = val
            self.__recompute_level()
            self.__deduce_ptrval()
        else:
            self.__calc_transition(val)
            self.__ptrval = val

        self.__last_level = self.transition[-1].level

        last = self.transition[-1]

        (_, _, pgran, level, vpn) = self.__param
        max_ent_idx = ~(-1 << vpn)
        self.terminal = False

        if last.level == 0 and max_ent_idx == last.offset:
            self.terminal = True
        elif last.level == level:
            self.terminal = True

    def __deduce_ptrval(self):
        (config, _, pgran, level, vpn) = self.__param
        pte_size = BinConfig.Bits[config] // 8
        val = 0

        for i, v in enumerate(reversed(self.transition)):
            if i == 0:
                val = v.offset * pte_size
                continue
            val = (v.offset << ((i - 1) * vpn + pgran)) | val

        self.__ptrval = val

    def __recompute_level(self):
        (_, _, pgran, level, vpn) = self.__param
        self.transition = self.transition[:level + 1]
        max_ents_idx = (1 << vpn) - 1

        last_level = 0
        for i in range(level):
            offset = self.transition[i].offset
            self.transition[i].level = last_level
            if offset != max_ents_idx:
                last_level += 1

        self.transition[-1].level = last_level

    def __calc_transition(self, val):
        parts = _unpack(val)[1:]

        (config, vabits, pgran, level, vpn) = _get_param()
        max_ents_idx = (1 << vpn) - 1
        bits = BinConfig.Bits[config]

        for i, (_, v) in enumerate(parts[:-1]):
            self.transition.append(Ptep.State(v))

        pte_size = bits // 8
        self.transition.append(Ptep.State(parts[-1][1] // pte_size))

        self.mis_alignment = (parts[-1][1] % pte_size) != 0

        self.__recompute_level()

    def print(self, printer):
        (_, _, pgran, level, vpn) = self.__param

        if self.__last_level == level:
            _type = "Pointer to generic data"
        else:
            _type = f"Level {self.__last_level} pte pointer"

            if self.transition[-1].offset == ~(-1 << vpn):
                _type = f"{_type}, L{self.__last_level} recursive entry"

        printer.print(fixhex(self.__ptrval))

        pp = printer.next_level()
        pp.print(_type)
        pp.print()
        pp.print("LEVEL TRANSITION")

        ppp = pp.next_level()
        ppp.print(" --> ".join([str(x) for x in self.transition]))

        if self.mis_alignment and self.__last_level != level:
            pp.print()
            pp.print("WARN: ptep does not aligned to pte boundary")

    def derive_inflections(self):
        (_, _, pgran, level, vpn) = self.__param
        last_ent_idx = ~(-1 << vpn)
        _trns_copy = [Ptep.State(x.offset) for x in self.transition]

        trns_copy = _trns_copy.copy()
        last_ptep = self
        while not last_ptep.terminal:
            trns_copy.insert(0, Ptep.State(last_ent_idx))
            last_ptep = Ptep(trns_copy.copy())
            yield last_ptep

        trns_copy = _trns_copy.copy()
        last_ptep = self
        while not last_ptep.terminal:
            trns_copy.pop(0)
            trns_copy.append(Ptep.State(0))
            last_ptep = Ptep(trns_copy.copy())
            yield last_ptep


def __cell(x):
    return f"{x:^15}"


def _get_param():
    config = global_state().config
    vabits = BinConfig.MmuVABits[config]
    pgran  = BinConfig.MmuPgGran[config]
    level  = BinConfig.MmuLevels[config]
    vpn    = (vabits - pgran) // level

    return (config, vabits, pgran, level, vpn)

def _unpack(va):
    (config, vabits, pgran, level, vpn) = _get_param()

    fields = []

    vaddr = get_rawrep(va)
    heading = vaddr >> vabits
    vfn = vaddr >> pgran

    fields.append((f"VA[{BinConfig.Bits[config] - 1}:{vabits}]", heading))

    for i in range(level):
        cur_lvl = level - i - 1
        h_shift = (cur_lvl + 1) * vpn
        l_shift = (cur_lvl) * vpn

        mask = (-1 << h_shift)^ (-1 << l_shift)

        fields.append((f"VPN{i}", (vfn & mask) >> l_shift))

    fields.append(("PG_OFF", vaddr & ~(-1 << pgran)))

    return fields

def __unpack_vaddr_print(va, printer):
    (_, vabits, pgran, level, vpn) = _get_param()

    fields = _unpack(va)
    cols = []
    for col, field in fields:
        disp_line = [__cell(col)]
        for fn in [lambda x: fixbin(x, vpn), hex, str]:
            disp_line.append(__cell(fn(field)))
        cols.append(disp_line)

    displ = [" ", "B", "H", "D"]
    for col in cols:
        for i, line in enumerate(col):
            displ[i] += f" {line} "

    for line in displ:
        printer.print(line)


def unpack_vaddr(va):
    printer = AdvPrinter()
    printer.print()
    __unpack_vaddr_print(va, printer)
    return va


def unpack_ptep(vaddr):
    ptep = Ptep(vaddr)

    printer = AdvPrinter()

    printer.print()
    printer.print("DESCRIPTION")
    printer.print()

    pp = printer.next_level()
    ptep.print(pp)

    printer.print()
    printer.print("VA BREAK DOWN")
    printer.print()
    __unpack_vaddr_print(vaddr, printer.next_level())

    printer.print()
    printer.print("INFLECTIONS")
    printer.print()

    pp = printer.next_level()
    for inflected in ptep.derive_inflections():
        inflected.print(pp)
        pp.print()

        if inflected.terminal:
            pp.print("-------------------")
            pp.print()

    return vaddr
