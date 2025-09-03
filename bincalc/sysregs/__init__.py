from .arm64_sysreg import Arm64SysRegInterpreter


from config import BinConfig, BinArch
from utils import BinCalcException
from function_base import BincalcFunctions
from cmdbase import cmd


class SysRegFunctions(BincalcFunctions):
    def __init__(self):
        super().__init__()

        self.__arm64i = Arm64SysRegInterpreter()

    @cmd("sysreg")
    def interpret_pte(self, name: str, val: int):
        """
            Interpret the system register according to correspond ISA specification
        """
        arch = BinConfig.Arch[self.gs.config]
        if arch == BinArch.Arm64:
            return self.__arm64i.interprete(name, val)

        raise BinCalcException(f"not supported for '{arch}'")
