from itertools import zip_longest
import typing

class SchemaBase:
    def __init__(self):
        pass

    def match(self, val):
        return False

    @staticmethod
    def match_generic(val, ref):
        t = type(ref)
        t_v = type(val)
        
        if ref == typing.Any:
            return True

        if isinstance(ref, type) and isinstance(val, ref):
            return True

        if issubclass(t, SchemaBase):
            return ref.match(val)

        if t != t_v:
            return False

        if t == list or t == tuple:
            for r, v in zip_longest(ref, val):
                if r == None:
                    continue
                if not SchemaBase.match_generic(v, r):
                    return False
            return True

        return val == ref

    @staticmethod
    def get_name(ref):
        if isinstance(ref, type):
            return ref.__name__

        if issubclass(type(ref), SchemaBase):
            return str(ref)

        return str(ref)

    def __eq__(self, value):
        return self.match(value)

    def __ne__(self, value):
        return not self.__eq__(value)


class Optional(SchemaBase):
    def __init__(self, schema):
        super().__init__()
        self.__schema = schema

    def match(self, v):
        if v is None:
            return True
        return SchemaBase.match_generic(v, self.__schema)

    def __str__(self):
        v = SchemaBase.get_name(self.__schema)
        return f"{v}?"


class Schema(SchemaBase):
    def __init__(self, any_ref):
        super().__init__()

        self.__ref = any_ref

    def match(self, val):
        return SchemaBase.match_generic(val, self.__ref)

    def __str__(self):
        v = SchemaBase.get_name(self.__ref)
        return v

class ObjectSchema(SchemaBase):
    def __init__(self, type_, **kwargs):
        super().__init__()

        self.__type = type_
        self.__members = kwargs

    def match(self, val):
        if not isinstance(val, self.__type):
            return False

        for k, ref in self.__members.items():
            v = getattr(val, k, None)
            if v is None:
                return False

            if not SchemaBase.match_generic(v, ref):
                return False

        return True

    def __str__(self):
        v = SchemaBase.get_name(self.__schema)
        members = [f"{k}{SchemaBase.get_name(v)}" for k, v in self.__members.items()]
        return f"{v}::< {', '.join(members)} >"

class UnionSchema(SchemaBase):
    def __init__(self, *args):
        super().__init__()
        self.__choices = args

    def match(self, val):
        for choice in self.__choices:
            if SchemaBase.match_generic(val, choice):
                return True
        return False

    def __str__(self):
        members = [f"{SchemaBase.get_name(c)}" for c in self.__choices]
        return f"({' | '.join(members)})"


class ElementAt(SchemaBase):
    def __init__(self, index, schema):
        super().__init__()
        self.__index = index
        self.__schema = schema

    def match(self, val):
        t = type(val)
        if t not in [list, tuple]:
            return False

        if self.__index >= len(val):
            return False

        pos = val[self.__index]
        return SchemaBase.match_generic(pos, self.__schema)

    def __str__(self):
        v = SchemaBase.get_name(self.__schema)
        return f"[{self.__index}] = {v}"


class PartialList(SchemaBase):
    def __init__(self, *args):
        super().__init__()
        self.__positions = []
        for el in args:
            if not isinstance(el, ElementAt):
                raise ValueError("PartialList expect ElementAt instances")
            self.__positions.append(el)

    def match(self, val):
        for pos in self.__positions:
            if not pos.match(val):
                return False

        return True

    def __str__(self):
        v = [SchemaBase.get_name(x) for x in self.__positions]
        return f"{{ {', '.join(v)} }}"

