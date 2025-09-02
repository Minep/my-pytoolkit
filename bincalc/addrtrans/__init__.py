from .x86_64 import interpret_pte as interpret_pte_x86
from .arm64 import interpret_pte as interpret_pte_arm64

from .va_unpacker import unpack_ptep, unpack_vaddr

from config import BinConfig, BinArch
from utils import BinCalcException
from function_base import BincalcFunctions
from cmdbase import cmd


class PteFunctions(BincalcFunctions):
    def __init__(self):
        super().__init__()

    @cmd("pte")
    def interpret_pte(self, pte, level):
        """
            Interpret the PTE bit fields according to current ISA setting
        """
        arch = BinConfig.Arch[self.gs.config]
        if arch == BinArch.X86_64:
            return interpret_pte_x86(pte, level)

        if arch == BinArch.Arm64:
            return interpret_pte_arm64(pte, level)

        raise BinCalcException(f"not supported for '{arch}'")

    @cmd("va")
    def unpack_va(self, vaddr: int):
        """
            Unpack the virtual address according to translation scheme
        """
        return unpack_vaddr(vaddr)

    @cmd("ptep")
    def unpack_ptep(self, vaddr: int):
        """
            Unfold the structural information encoded in ptep (recursive page table scheme only)
        """
        return unpack_ptep(vaddr)
