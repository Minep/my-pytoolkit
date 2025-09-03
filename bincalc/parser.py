from ast import (
    NodeTransformer, Tuple,
    Call, Name, Constant,
    parse, dump
)

from utils import BinCalcException

import ast

from lib.schmea import (
    ObjectSchema, UnionSchema,
    PartialList, ElementAt
)
import re

class AstTypes:
    Function = ObjectSchema(Tuple, 
                    elts=PartialList(
                        ElementAt(0, Name)))

    DirectCall = ObjectSchema(Call, func=Name)
    
    NameRef = ObjectSchema(Name, id=str)

    result_ref = re.compile(r"^(?:A|Ans)([0-9]+)$")

class BuiltinConversion:
    InvokeCommand = "__invoke_cmd"
    GetRecord = "__get_record"

class ExpressionTransformer(NodeTransformer):
    def __init__(self):
        super().__init__()
    
    def __to_invoke(self, name, arg_list):
        args = [Constant(name)]

        for e in arg_list:
            e_ = self.visit(e)
            if e_ is None:
                continue
            args.append(e_)
    
        n = Name(BuiltinConversion.InvokeCommand, ctx=ast.Load())
        return Call(n,  args, [], lineno=0)

    def visit_Tuple(self, node: Tuple):
        if not AstTypes.Function.match(node):
            return node

        func_name = node.elts[0].id

        return self.__to_invoke(func_name, node.elts[1:])

    def visit_Name(self, node: Name):
        if AstTypes.NameRef != node:
            return Constant(node.id)

        id_ = node.id
        g = AstTypes.result_ref.match(id_)
        if not g:
            return Constant(node.id)

        num = int(g.group(1))
        
        n = Name(BuiltinConversion.GetRecord, ctx=ast.Load())
        return Call(n, [Constant(num)], [])

    def visit_Call(self, node : Call):
        if not AstTypes.DirectCall.match(node):
            return None

        return self.__to_invoke(node.func.id, node.args)

    def visit_Import(self, node):
        return None

    def visit_ImportFrom(self, node):
        return None


def parse_expr(expr):
    transform = ExpressionTransformer()
    
    try:
        T = parse(expr, mode='eval', filename=f"expr:'{expr}'")
        T = transform.visit(T)
        T = ast.fix_missing_locations(T)
    except SyntaxError as e:
        raise BinCalcException(f"syntax error: {e.filename} (1:{e.offset})")

    #print(dump(T, indent=4))
    #print(ast.unparse(T))
    return compile(T, "<expr>", mode='eval')

