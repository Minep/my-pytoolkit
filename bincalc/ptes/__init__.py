from .x86_64 import interpret_pte as interpret_pte_x86

from .config import BinConfig, BinArch
from .utils import BinCalcException
from .function_base import BincalcFunctions
from .cmdbase import cmd


class PteFunctions(BincalcFunctions):
    def __init__(self):
        super().__init__()

    @cmd("pte")
    def interpret_pte(self, pte, level):
        arch = BinConfig.Arch[self.gs.config]
        if arch == BinArch.X86_64:
            return interpret_pte_x86(pte, level)

        raise BinCalcException(f"not supported for '{arch}'")

