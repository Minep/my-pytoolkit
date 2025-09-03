from parser import parse_expr, BuiltinConversion
from state import global_state
from utils import get_converter, BinCalcException 
from cmds import AllFunctions

from config import preset_x86_64_LA48, preset_arm64_le_va48_4k

from lib.accessor import AccessorException


class BinaryCalculator:
    def __init__(self):
        self.__record_id = 0
        self.__gs = global_state()
        self.__save_records = {}

        # setup defaults
        self.__gs.config.update(preset_arm64_le_va48_4k())

        self.__all_fns = AllFunctions()


    def __get_exec_env(self):
        def invoke_cmd(name, *args):
            ok, retv = self.__all_fns.call(name, *args)
            if ok:
                return retv
            raise BinCalcException(f"undefined function: {name}")

        def get_record(rec_id):
            if rec_id not in self.__save_records:
                raise BinCalcException(
                        f"record of index {rec_id} does not exists or non-numeric")

            return self.__save_records[rec_id]

        return {
            BuiltinConversion.InvokeCommand: invoke_cmd,
            BuiltinConversion.GetRecord: get_record,
            "__builtins__": {}
        }

    def eval(self, line):
        co = parse_expr(line)

        env = self.__get_exec_env()

        try:
            result = eval(co, env)
        except AccessorException as e:
            raise BinCalcException(str(e))
        except Exception as e:
            raise e

        if type(result) in [int, float]:
            self.__save_records[self.__record_id] = result

        self.__record_id += 1
        return self.__convert_printable(result)

    def __convert_printable(self, result):
        if result is None:
            return ""

        if isinstance(result, str):
            return result

        conv = get_converter(self.__gs.config)
        return conv.convert(result)

    def get_id(self):
        return self.__record_id
