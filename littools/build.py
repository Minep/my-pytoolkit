import sys
import os
import subprocess
import shlex

from pathlib import Path
from argparse import ArgumentParser

from Shared.importer import ExtendableImporter
from Shared.context import Context

def load_buildscript(file, environment):
    importer = ExtendableImporter(environment)

    old_importer = sys.meta_path[0]

    with file.open('r') as f:
        co = compile(f.read(), file.absolute(), 'exec')

    sys.meta_path[0] = importer
    exec(co, environment)
    sys.meta_path[0] = old_importer

class StageFailed(Exception):
    def __init__(self, stage, *args):
        super().__init__(*args)
        self.failed_stage = stage

class StageBase:
    def __init__(self, name, repeat=1):
        self._name = name
        self.__nr_repeat = repeat
        self._index = 0

    def run(self):
        for i in range(self.__nr_repeat):
            self._index = i

            name = f"[{self.get_name()} {i + 1}/{self.__nr_repeat}] {self.get_desc()}"
            print(name)

            self._execute()

    def _execute(self, index):
        pass

    def get_name(self):
        return self._name

    def get_desc(self):
        return ""

class PosixCmdStage(StageBase):
    def __init__(self, name, args, repeat=1):
        super().__init__(name, repeat)

        self.__args = [str(x) for x in args] 

    def _execute(self):
        cwd = Context.WorkingFiles.base()
        ret = subprocess.run(self.__args, cwd=cwd)

        if ret.returncode != 0:
            raise StageFailed(self, f"failed with return code {ret.returncode}")

    def get_name(self):
        return f"CMD"

    def get_desc(self):
        return " ".join(self.__args)

class PosixScriptStage(PosixCmdStage):
    def __init__(self, name, script, args, repeat=1):
        script_exec = [
            Context.WorkingFiles[script].absolute(),
            *args
        ]

        super().__init__(name, script_exec, repeat)

        self.__script = script

    def get_name(self):
        return f"RUN"


class CheckDirStage(StageBase):
    def __init__(self, name, args):
        super().__init__(name, len(args))

        self.__dirs = args

    def _execute(self):
        dir_name = self.__dirs[self._index]
        dir_to_check = Context.WorkingFiles[dir_name]

        if not dir_to_check.exists():
            dir_to_check.mkdir()
            return

        if not dir_to_check.is_dir():
            raise StageFailed(self, f"{dir_name} (at {dir_to_check}) is not directory")

    def get_name(self):
        return f"CHECK DIR"

    def get_desc(self):
        return self.__dirs[self._index]

class ExportEnvStage(StageBase):
    def __init__(self, name, env_key, env_val):
        super().__init__(name)

        self.__k = env_key
        self.__v = env_val

    def _execute(self):
        os.environ[self.__k] = str(self.__v)

    def get_name(self):
        return f"ENV"

    def get_desc(self):
        return f"{self.__k} = '{self.__v}'" 


class Pipeline:
    def __init__(self):
        self.__post_actions = []
        self.__pre_actions = []
        self.__stages = {}

    def add_post_action(self, stage):
        self.__post_actions.append(stage)

    def add_pre_action(self, stage):
        self.__pre_actions.append(stage)

    def add_stages(self, target, stages):
        if target not in self.__stages:
            self.__stages[target] = []

        self.__stages[target] += stages

    def run(self, target):
        print(">>>> Building:", target)
        merged  = self.__pre_actions
        merged += self.__stages[target]
        merged += self.__post_actions
        for stage in merged:
            stage.run()


def get_environment(pipeline):
    def to_list(l):
        if isinstance(l, tuple):
            return [*l]
        if not isinstance(l, list):
            return [l]
        return l

    def unfold(l):
        v = []
        for _e in l:
            if isinstance(_e, list):
                v += _e
            else:
                v.append(_e)
        return v

    def cmd(cmd_args, name="", **kwargs):
        cmd_args = to_list(cmd_args)
        return [PosixCmdStage(name, cmd_args, **kwargs)]

    def run(cmd_line, name="", **kwargs):
        parts = shlex.split(cmd_line)
        return cmd(parts, name=name, **kwargs)

    def mkdir(dirs, name="", **kwargs):
        dirs = to_list(dirs)
        return [CheckDirStage(name, dirs, **kwargs)]

    def env(key, val, name="", **kwargs):
        return [ExportEnvStage(name, key, val, **kwargs)]
    
    def script(script_name, cmd_args = [], name="", **kwargs):
        cmd_args = to_list(cmd_args)
        return [PosixScriptStage(name, script_name, cmd_args, **kwargs)]

    def file(rel_path):
        return Context.WorkingFiles[rel_path].absolute()

    def xelatex(file, bibtex=False, build_dir="", other_args = [], **kwargs):
        nr_repeat = 2   # at least 2 pass, to account for toc and hyperref
        args = ["xelatex"]
        if build_dir:
            args += [ "-output-directory", build_dir ]

        args += other_args
        args.append(file)

        stages = []

        if bibtex:
            bibtex_name = Path(file)
            bibtex_name = Path(build_dir) / bibtex_name.stem

            stages += cmd(args, name="XTEX")
            stages += cmd(["bibtex", bibtex_name], name="BBL")
            stages += cmd(args, name="XTEX")

            nr_repeat = 1

        stages += cmd(args, name="XTEX", repeat=nr_repeat)

        return stages

    def target(name, stages):
        pipeline.add_stages(name, unfold(stages))

    def prologue(stages):
        for stage in unfold(stages):
            pipeline.add_pre_action(stage)

    return {
        "cmd": cmd,
        "mkdir": mkdir,
        "env": env,
        "script": script,
        "file": file,
        "xelatex": xelatex,
        "prologue": prologue,
        "target": target
    }



def main():
    ap = ArgumentParser(__pytool__)
    ap.add_argument("build_script")
    ap.add_argument("targets", nargs="+")

    args, unknown = ap.parse_known_args()

    pipeline = Pipeline()
    env  = get_environment(pipeline)
    
    sys.argv = unknown
    load_buildscript(Context.WorkingFiles[args.build_script], env)

    for target in args.targets:
        pipeline.run(target)

if __name__ == "__pytool__":
    main()
