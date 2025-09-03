from .arm64_sysreg import Arm64SysRegInterpreter
from .arm64_sysfeat import Arm64Features


from config import BinConfig, BinArch
from utils import BinCalcException
from function_base import BincalcFunctions
from cmdbase import cmd


class SysRegFunctions(BincalcFunctions):
    def __init__(self):
        super().__init__()

        self.__arm64i = Arm64SysRegInterpreter()
        self.__arm64f = Arm64Features()

    @cmd("sysreg")
    def system_register(self, name: str, val: int = 0):
        """
            Interpret the system register according to correspond ISA specification
        """
        
        arch = BinConfig.Arch[self.gs.config]
        if arch == BinArch.Arm64:
            return self.__arm64i.interprete(name, val)

        raise BinCalcException(f"not supported for '{arch}'")
    
    @cmd("sysfeat")
    def system_feature(self, name: str):
        """
            Query a architectural feature defined by ISA specification
        """

        arch = BinConfig.Arch[self.gs.config]
        if arch == BinArch.Arm64:
            return self.__arm64f.query(name)

        raise BinCalcException(f"not supported for '{arch}'")
