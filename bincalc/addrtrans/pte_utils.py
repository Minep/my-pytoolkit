from utils import BitFieldExractor, get_rawrep, arrange
from state import global_state

from textwrap import indent

class PteFormatBase:
    def __init__(self, val, pte_type, level=3):
        self._config = global_state().config
        self._pteval = val
        self._rawval = get_rawrep(val)
        self._level  = level
        self._type   = pte_type

        self.init()

        fields = self.get_fields()
        extractor = BitFieldExractor(fields)
        reslult = extractor.extract_colored(self._rawval, 64)
        self.__binstr, self.__field_map = reslult
    
    def init(self):
        pass

    def get_fields(self):
        return []

    def get_field_values(self):
        return self.__field_map

    def get_field_comment(self, field):
        return None

    def _get_basic_info(self):
        return [
            "pte (native): " + hex(self._rawval),
            "pte (target): " + hex(self._pteval)
        ]

    def print_explaination(self):
        print("BASIC INFO")

        info = self._get_basic_info()
        info = arrange(info, cols=1, seq_number=False)
        print(indent(info, " " * 4))

        print()
        print("BITS MAP")
        print(indent(self.__binstr, "    "))
        print()
        print("FIELDS MAP")

        for f in self.__field_map:
            f.set_comment(self.get_field_comment(f))

        fields = arrange(self.__field_map)
        print(indent(fields, " " * 4))


