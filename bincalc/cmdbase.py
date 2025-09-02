from typing import Callable, Any
from lib.schmea import Schema, Optional, SchemaBase

import inspect
import textwrap


def cmd(name, *alias):
    def __cmd(fn: Callable):
        fn.__annotations__["__CMD__"] = True
        fn.__annotations__["__NAME__"] = name
        fn.__annotations__["__ALIAS__"] = [*alias]
        return fn
    return __cmd


def imply_schema(fn: Callable):
    arg_list = []

    signature = inspect.signature(fn)
    param = signature.parameters

    for k, v in param.items():
        if k == "self":
            continue

        t = v.annotation
        t = t if t != inspect.Parameter.empty else Any

        default = v.default
        if default == inspect.Parameter.empty:
            arg_list.append((k, t))
            continue

        arg_list.append((k, Optional(Schema(t))))

    return Schema([x[1] for x in arg_list]), arg_list


class Executor:
    def __init__(self, body: Callable):
        self.name = body.__annotations__["__NAME__"]
        self.alias = body.__annotations__["__ALIAS__"]
        self.help = inspect.getdoc(body)
        self.help = textwrap.dedent(self.help if self.help else "")

        schema, args = imply_schema(body)
        self.argstr  = ', '.join(
            [f'<{n.upper()}: {SchemaBase.get_name(t)}>' for n, t in args])

        self.__fn = body
        self.__argtype = schema

    def match_name(self, name):
        return self.name == name or name in self.alias

    def try_invoke(self, *args):
        t_args = [self.__type_mapper(x) for x in args]
        if self.__argtype != t_args:
            raise TypeError(
                f"invalid parameter ({t_args}), expect: ({self.argstr})")

        return self.__fn(*t_args)

    def __type_mapper(self, strtype):
        if strtype in ['True', 'False']:
            return bool(strtype)
        if strtype in ['y', 'n']:
            return bool(strtype == 'y')

        return strtype

    def __str__(self):
        return '\n'.join([
            *[f"{name}, {self.argstr}" for name in self.alias + [self.name]],
            textwrap.indent(self.help, '\t'),
            ""
        ])


class CmdTable:
    def __init__(self):
        self._cmd_map = []

        fns = inspect.getmembers(self, 
                                 lambda p: isinstance(p, Callable))
        for _, fn in fns:
            if not hasattr(fn, "__annotations__"):
                continue
            if "__CMD__" not in fn.__annotations__:
                continue

            self._cmd_map.append(Executor(fn))

    def call(self, name, *args):
        for exe in self._cmd_map:
            if exe.match_name(name):
                retv = exe.try_invoke(*args)
                return True, retv

        return False, None

    def help_text(self):
        ls = []
        for exe in self._cmd_map:
            ls.append(str(exe))

        return '\n'.join(ls)

