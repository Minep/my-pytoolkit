from state import global_state
from config import BinConfig, BinEndian, GeneralConfig, DisplyType
import struct


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
