from state import global_state
from cmdbase import CmdTable
from config import accessors

class BincalcFunctions(CmdTable):
    def __init__(self):
        super().__init__()
        self.gs = global_state()
        self.configs = accessors()


