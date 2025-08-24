import sys
import os.path
import os
import json
import textwrap

from importlib.abc import Loader, MetaPathFinder
from importlib.util import spec_from_file_location

from shared.resource import ResourceScope
from shared.importer import ExtendableImporter

from pathlib import Path
from argparse import ArgumentParser

resource = ResourceScope(os.environ.get("PYTOOL_DIR", __file__))


class PyToolImporter(ExtendableImporter):
    def __init__(self, rel_path, common_global):
        super().__init__(common_global, rel_path)
        self.__base = resource.base()

        with resource["import_defs.json"].open('r') as f:
            self.__map = json.load(f)

    def search_paths(self):
        return [self.__base]

    def resolve(self, fullname, path, target):
        if fullname in self.__map:
            path = [os.path.join(self.__base, self.__map[fullname])]
            return (path, "")

        return super().resolve(fullname, path, target)


class ToolMap:
    def __init__(self):
        map_file = resource["tool_map.json"]

        with map_file.open('r') as f:
            self.__maps = json.load(f)

    def get(self, scope, name):
        if not scope:
            print("execute in current working directory")
            return (Path(os.getcwd()) / name).absolute()

        _scope = self.__maps.get(scope)
        if _scope is None:
            print(f"undefined scope '{scope}'")
            return None

        tool = _scope["map"].get(name)
        if tool is None:
            return None

        return tool["path"]

    def get_help(self):
        strs = []
        for scope_name, scope in self.__maps.items():
            desc = scope.get("desc", "")
            maps = scope.get("map", {})

            strs.append(f" {scope_name}")
            strs.append(f"    {desc}")
            strs.append("")

            for tool_name, tool in maps.items():
                desc = tool.get("desc", "")
                strs.append(f" {scope_name}::{tool_name}")
                strs.append(f"    {desc}")
                strs.append("")

            strs.append("-----")
            strs.append("")

        s = "\n".join(strs)
        print(textwrap.indent(s, "    "))


class ScriptName:
    def __init__(self, toolmap, name, scope="", cwdRelative=False):
        self.__name = name
        self.__scope = scope
        self.__map = toolmap
        self.__cwd_rel = cwdRelative

        self.__path = name
        if cwdRelative or len(scope) > 0:
            self.__path = toolmap.get(scope, name)

    def path(self):
        return resource[self.__path]

    def __str__(self):
        if self.__scope:
            return f"{self.__scope}::{self.__name}"

        if self.__cwd_rel:
            return f"::{self.__name}"

        return self.__name

    def from_name(script_name, toolmap):
        parts = script_name.split("::")[:2]
        if len(parts) == 2:
            return ScriptName(toolmap, parts[1], parts[0], True)

        return ScriptName(toolmap, parts[0])


def install_import_hook(rel_path, common_global):
    sys.meta_path.insert(0, PyToolImporter(rel_path, common_global))


def execute(name, *args):
    script_path = name.path()

    if not script_path.exists():
        print(f"unable to locate '{script}' ({script_path})")
        exit(1)

    with script_path.open('r') as f:
        co = compile(f.read(), script_path.absolute(), 'exec')

    _extras = {
        "_localRes_": ResourceScope(script_path.parent),
        "_cwdRes_": ResourceScope(os.getcwd()),
        "_gvt_": dict()
    }

    _tool_global = {
        "__name__": "__pytool__",
        "__pytool__": str(name)
    }

    sys.argv = [script_path.absolute(), *args]

    install_import_hook(script_path.parent, _extras)
    exec(co, _tool_global)


def main():
    ap = ArgumentParser()
    ap.add_argument("script_str", nargs='?', default='')
    ap.add_argument("--list",
                    required=False,
                    action="store_true",
                    help="list all scopes and tools")

    argv = sys.argv
    additional_start = len(argv)
    for i, v in enumerate(argv):
        if v == "--":
            additional_start = i
            break

    sys.argv = argv[:additional_start]
    args = ap.parse_args()
    maps = ToolMap()

    if args.list:
        maps.get_help()
        exit(0)

    if not args.script_str:
        print("must provide a target to run")
        exit(1)

    name = ScriptName.from_name(args.script_str, maps)
    execute(name, *argv[additional_start + 1:])


if __name__ == "__main__":
    main()
