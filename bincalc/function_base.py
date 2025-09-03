from state import global_state
from cmdbase import CmdTable
from config import accessors

from utils import BinCalcException

class BincalcFunctions(CmdTable):
    def __init__(self):
        super().__init__()
        self.gs = global_state()
        self.configs = accessors()

    def call(self, name, *args):
        try:
            return super().call(name, *args)
        except TypeError as e:
            raise BinCalcException(str(e))
