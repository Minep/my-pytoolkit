from utils import HexConvert, DecConvert, BinConvert
from function_base import BincalcFunctions
from cmdbase import cmd, Executor
from config import arch_preset, GeneralConfig, accessors

from lib.advprinter import AdvPrinter, _fmt_bold

import pydoc
import json

from addrtrans import PteFunctions
from sysregs import SysRegFunctions


class GeneralFunctions(BincalcFunctions):
    def __init__(self):
        super().__init__()

        self.__arch_preset = arch_preset()

    @cmd("set")
    def _set(self, key: str, value):
        """
            Set a config term
        """
        self.configs[key][self.gs.config] = value

    @cmd("dump_config")
    def _dump_config(self):
        """
            Dump config object in json
        """
        print(json.dumps(self.gs.config, indent=4))

    @cmd("get")
    def _get(self, key: str):
        """
            Get a config term
        """
        return str(self.configs[key][self.gs.config])

    @cmd("disp", )
    def _disp(self, choice: str):
        """
            Set the displace format. Accept: hex | bin | dec
        """
        GeneralConfig.DisplyType[self.gs.config] = choice
    
    @cmd("hex", "h")
    def _hex(self, val: int):
        """
            Print the value in hexadecimal
        """
        return HexConvert().convert(val)

    @cmd("bin", "b")
    def _bin(self, val: int):
        """
            Print the value in binary
        """
        return BinConvert().convert(val)

    @cmd("dec", "d")
    def _dec(self, val: int):
        """
            Print the value in decimal
        """
        return DecConvert().convert(val)

    @cmd("arch")
    def _arch(self, name: str = None):
        """
            Set or get (if NAME is not given) the Arch (ISA) config.
        """
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

    @cmd("all_cfgs")
    def _configs(self):
        """
            List all configuration keys avaliable
        """

        ammgr = accessors()
        for k, v in ammgr.items():
            print(_fmt_bold(k), f"(default: {v.default()})")


class AllFunctions(BincalcFunctions):
    def __init__(self):
        super().__init__()

        self.__scoped_fns = {
            "general": GeneralFunctions(),
            "address transaltion": PteFunctions(),
            "system register": SysRegFunctions()
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

    @cmd("help", "h")
    def _help(self):
        buf = AdvPrinter.Buffer()

        p = AdvPrinter(buffer=buf)
        pp   = p >> 1
        ppp  = p >> 2
        pppp = p >> 3

        p.printb("SYNOPSIS")

        pp.printblk("""
            CMD_NAME, [EXPR, ...]
            EXPR
        """, nowrap=True)

        p.printb("DESCRIPTION")
        pp.printblk("""
            Execute a command (following by a comma and optionally arbitary expression EXPR separated by comma),
            or a single expression EXPR.

            The expression EXPR can be a regular python arithmatic expression or the command invocation itself.
            In the latter case, the nested command will be evaluated and the return value will be subsituted.
            If command has no return value, 'None' will be used.

            The result of the expression or return value of the command is avaliable in the subsequent interaction,
            and can be accessed as variable `A#` where `#` is the expression ID shown in the prompt when the command
            was executed.

            See GRAMMAR section for complete BNF description of the syntax.

            See LIST OF COMMANDS section gives all command avaliable to invoke.
        """)

        p.printb("GRAMMAR")
        pp.printblk("""
            command    := <expr>;

            expr       := <python-arithmatic-expr>
                        | <cmd_invoke>;

            cmd_invoke := <cmd_name> , <args>
                        | <cmd_name> ,
                        | ;

            args       := <args> , <args>
                        | <ans-ref>
                        | <python-literals>
                        | <python-arithmatic-expr>
                        | ( <cmd_invoke> ) ;

            cmd_name   := <python-identifiers>
                        | <python-string>;

            ans-ref    := A <python-numerial>;
        """, nowrap=True)

        p.printb("LIST OF COMMANDS")
        for k, fns in self.__scoped_fns.items():
            scope_name = k.upper()
            pp.printb(scope_name)

            for v in fns._cmd_map:
                ppp.printb(v.synopsis())
                pppp.printblk(v.description())

        p.printb("ARCH CONFIG")
        pp.print("\n".join(arch_preset().keys()))

        pydoc.pager(str(buf))

