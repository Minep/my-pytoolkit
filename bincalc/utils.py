from itertools import zip_longest
from state import global_state
from config import BinConfig, BinEndian, GeneralConfig, DisplyType
import struct


class BinCalcException(Exception):
    def __init__(self, msg):
        super().__init__()

        self.__msg = msg

    def __str__(self):
        return self.__msg


def get_rawrep(val):
    assert type(val) in [int, float]

    config = global_state().config
    endian = BinConfig.Endian[config]
    bits = BinConfig.Bits[config]

    if isinstance(val, int):
        val = val & ((1 << bits) - 1)

    if isinstance(val, float):
        dtype = 'd' if bits == 64 else 'f'
    else:
        dtype = 'Q' if bits == 64 else 'L'

    if endian == BinEndian.Little:
        ed = '<'
    else:
        ed = '>'

    unpack_type = 'Q' if bits == 64 else 'L'
    s = struct.pack(f"{ed}{dtype}", val)
    return struct.unpack(f"={unpack_type}", s)[0]


def pretty_binary(val, bits, bits_per_group=32, transform_cb=None):
    assert bits % bits_per_group == 0

    rawv = get_rawrep(val)
    binstr = bin(rawv)[2:]

    padlen = bits - len(binstr)
    binstr = "0" * padlen + binstr

    i = 0
    groups_per_row = bits_per_group // 8
    result = []
    line = []

    while i < bits:
        group = binstr[i:i+8]
        msb4, lsb4 = group[:4], group[4:]
        bitpos_hint = bits - i

        if transform_cb:
            msb4 = transform_cb(msb4, bitpos_hint - 4)
            lsb4 = transform_cb(lsb4, bitpos_hint - 8)

        valstr = f"{msb4} {lsb4}"
        if i % bits_per_group == 0:
            # msb
            valstr = f"{bitpos_hint - 1:>2} | {valstr}"
        elif len(line) == groups_per_row - 1:
            # lsb
            valstr = f"{valstr} | {bitpos_hint - 8:<2}"
            line.append(valstr)
            result.append(" ".join(line))

            line.clear()
            i += 8
            continue

        i += 8
        line.append(valstr)

    if len(line) != 0:
        result.append(" ".join(line))

    return "\n".join(result)


class IntConverterBase:
    def __init__(self):
        pass

    def _do_int(self, val):
        pass

    def _do_float(self, val):
        pass

    def convert(self, val):
        if isinstance(val, int):
            return self._do_int(val)
        if isinstance(val, float):
            return self._do_float(val)
        return str(val)


class HexConvert(IntConverterBase):
    def __init__(self):
        super().__init__()

    def _do_int(self, val):
        v = get_rawrep(val)
        return hex(v)

    def _do_float(self, val):
        v = get_rawrep(val)
        return hex(v)


class DecConvert(IntConverterBase):
    def __init__(self):
        super().__init__()

    def _do_int(self, val):
        v = get_rawrep(val)
        return str(v)

    def _do_float(self, val):
        v = get_rawrep(val)
        return str(v)


class BinConvert(IntConverterBase):
    def __init__(self):
        super().__init__()
        config = global_state().config

        self.__bits = BinConfig.Bits[config]

    def _do_int(self, val):
        return pretty_binary(val, self.__bits)

    def _do_float(self, val):
        return pretty_binary(val, self.__bits)


def get_converter(config):
    disp_mode = GeneralConfig.DisplyType[config]

    if disp_mode == DisplyType.Dec:
        return DecConvert()

    if disp_mode == DisplyType.Hex:
        return HexConvert()

    if disp_mode == DisplyType.Bin:
        return BinConvert()


class BitFieldColor:
    Red = 31
    Green = 32
    Yellow = 33
    Blue = 34
    Magenta = 35
    Cyan = 36


class PteFieldExractor:
    def __init__(self, fields, color_palette=None):
        # sort in descending order, based on MSB position
        self.__fields = sorted(fields, key=lambda x: x[1], reverse=True)
        self.__palette = list(range(31,37)) if not color_palette else color_palette

        # (assigned_color, field)
        self.__current_fields = None
        self.__current_pos = None

        self.__color_acc = 0

    def __get_color(self):
        i = self.__color_acc % len(self.__palette)

        self.__color_acc += 1
        return self.__palette[i]

    def __check_in_range(self, field, pos):
        _, h, l = field

        return l <= pos <= h

    def __get_field(self, pos):
        if self.__current_fields is not None:
            if self.__check_in_range(self.__current_fields[1], pos):
                return (self.__current_fields, self.__current_fields)

        old_field = self.__current_fields
        for field in self.__fields:
            if not self.__check_in_range(field, pos):
                continue

            color = self.__get_color()
            self.__current_fields = (color, field)
            return (self.__current_fields, old_field)

        self.__current_fields = None
        return None, old_field

    def __extract_and_color(self, collected, bitgroup, lsb_pos):
        pos = lsb_pos + len(bitgroup) - 1
        colored = []

        if self.__current_fields is not None:
            color, _ = self.__current_fields
            colored.append(f"\x1b[{color};49m")

        for i in range(len(bitgroup)):
            bit = bitgroup[i]
            field, old_field = self.__get_field(pos)

            pos -= 1
            if field != old_field:
                colored.append("\x1b[0m")
                if field is not None:
                    color, field_ = field
                    colored.append(f"\x1b[{color};49m")
                if old_field:
                    collected.append(old_field)
            
            colored.append(bit)

        colored.append("\x1b[0m")
        if lsb_pos == 0 and self.__current_fields:
            collected.append(self.__current_fields)

        return "".join(colored)

    def __extract_internal(self, val, bit):
        extracted = []

        def on_transform(val, lsb_pos):
            nonlocal extracted
            return self.__extract_and_color(extracted, val, lsb_pos)

        if bit is None:
            cfg = global_state().config
            bit = BinConfig.Bits[cfg]

        raw_rep = get_rawrep(val)
        printed_field = pretty_binary(raw_rep, bit, transform_cb=on_transform)

        extracted_val = []
        for color, (name, h, l) in extracted:
            mask = (-1 << (h + 1)) ^ (-1 << l)
            field_val = (raw_rep & mask) >> l
            extracted_val.append((color, name, h, l, field_val))

        return printed_field, extracted_val

    def extract_colored(self, val, bit=None):
        return self.__extract_internal(val, bit)

    def print_intepreted(self, val, bit=None):
        printable_bits, extracted = self.__extract_internal(val, bit)

        field_str = []
        for color, name, h, l, val in extracted:
            field_str.append([
                f"\x1b[{color};49m",
                f"{name}[{h:02d}:{l:02d}]",
                f"{hex(val)}"
            ])

        mid = len(field_str) // 2 + 1
        col1, col2 = field_str[:mid], field_str[mid:]

        print(printable_bits)
        print()

        for c1, c2 in zip_longest(col1, col2):
            [c1clr, c1name, c1str] = ["", "", ""] if c1 is None else c1
            [c2clr, c2name, c2str] = ["", "", ""] if c2 is None else c2

            print(f"{c1clr}{c1name:>15} {c1str:<30}\x1b[0m",
                  f"{c2clr}{c2name:>15} {c2str:<30}\x1b[0m")
