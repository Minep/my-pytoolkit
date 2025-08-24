from utils import HexConvert, DecConvert, BinConvert
from function_base import BincalcFunctions
from cmdbase import cmd, Executor
from config import arch_preset, GeneralConfig

import textwrap

from ptes import PteFunctions


class GeneralFunctions(BincalcFunctions):
    def __init__(self):
        super().__init__()

        self.__arch_preset = arch_preset()

    @cmd("set")
    def _set(self, key: str, value):
        self.configs[key][self.gs.config] = value

    @cmd("get")
    def _get(self, key: str):
        return str(self.configs[key][self.gs.config])

    @cmd("disp")
    def _disp(self, choice: str):
        GeneralConfig.DisplyType[self.gs.config] = choice
    
    @cmd("hex", "h")
    def _hex(self, val):
        return HexConvert().convert(val)

    @cmd("bin", "b")
    def _bin(self, val):
        return BinConvert().convert(val)

    @cmd("dec", "d")
    def _dec(self, val):
        return DecConvert().convert(val)

    @cmd("arch")
    def _arch(self, name: str = None):
        if name is not None:
            if name not in self.__arch_preset:
                raise NameError("unable to find arch config '{name}'")
            preset = self.__arch_preset[name]

            self.gs.config.update(preset())
            print(self.gs.config)
            return

        for k, acc in self.configs.items():
            if not k.startswith("arch:"):
                continue

            val = acc[self.gs.config]
            print(f"{k:^20}{val}")


class AllFunctions(BincalcFunctions):
    def __init__(self):
        super().__init__()

        self.__scoped_fns = {
            "general": GeneralFunctions(),
            "address transaltion": PteFunctions()
            # More...
        }

    def call(self, name, *args):
        for fn_scope in self.__scoped_fns.values():
            ok, retv = fn_scope.call(name, *args)
            if ok:
                return True, retv

        return super().call(name, *args)

    def register_fn(self, fn_cmd):
        self._cmd_map.append(Executor(fn_cmd))

    def __indent(self, text, level):
        return textwrap.indent(text, "    " * level)

    def __help_str(self, scope, level):
        return self.__indent(scope.help_text(), level)


    @cmd("help", "h")
    def _help(self):
        help_txt = []

        help_txt.append("COMMANDS")

        help_txt.append(self.__indent("SYNOPSIS", 1))
        help_txt.append(self.__indent("command, [ARG],...",2))
        help_txt.append("")

        help_txt.append(self.__indent(
                            "'command' and the arguments are separated by comma (,)",2))
        help_txt.append(self.__indent(
                            "the following list all commands recognised, grouped into categories.",2))
        help_txt.append("")

        for k, v in self.__scoped_fns.items():
            scope_name = k.upper()
            help_txt.append(self.__indent(scope_name, 1))
            help_txt.append(self.__help_str(v, 2))

        help_txt.append("ARCH CONFIG")
        help_txt.append(self.__indent("\n".join(arch_preset().keys()), 1))

        print("\n".join(help_txt))
