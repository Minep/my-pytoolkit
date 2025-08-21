from .schmea import Schema, UnionSchema


class AccessorManager:
    def __init__(self):
        self.__maps = {}

    def register(self, key, accessor):
        if key in self.__maps:
            raise NameError(f"key '{key}' already exists")

        self.__maps[key] = accessor

    def new(self, accessor, key, *args, **kwargs):
        acc = accessor(key, *args, **kwargs)
        self.register(key, acc)
        return acc

    def get(self, key):
        if key not in self.__maps:
            raise NameError(f"key '{key}' not exists")

        return self.__maps[key]

    def items(self):
        return self.__maps.items()

    def __getitem__(self, index):
        return self.__maps[index]


class AccessorBase:
    def __init__(self, checker=None, default_val=None):
        self.__checker = checker
        self.__default = default_val

    def __getitem__(self, obj):
        v = self.get_value(obj)
        v = self.__default if v is None else v
        return v

    def __setitem__(self, obj, value):
        if self.__checker is not None:
            self.__checker(value)

        self.set_value(obj, value)

    def get_value(self, obj):
        return

    def set_value(self, obj, val):
        pass


class DictAccessor(AccessorBase):
    def __init__(self, key, checker=None, **kwargs):
        super().__init__(checker, **kwargs)
        self.__key = key

    def get_value(self, obj):
        return obj.get(self.__key, None)

    def set_value(self, obj, val):
        obj[self.__key] = val


class ObjectAccessor(AccessorBase):
    def __init__(self, key, checker=None, **kwargs):
        super().__init__(checker, **kwargs)
        self.__key = key

    def get_value(self, obj):
        return getattr(obj, self.__key, None)

    def set_value(self, obj, val):
        setattr(obj, self.__key, val)


def schema_checker(schema):
    def __check(val):
        if schema.match(val):
            return
        raise Exception("expect type: " + str(schema) + ", got " + val)

    return __check


def expect_str():
    return schema_checker(Schema(str))


def expect_int():
    return schema_checker(Schema(int))


def expect_bool():
    return schema_checker(Schema(bool))


def expect_float():
    return schema_checker(Schema(float))


def expect_oneof(*options):
    return schema_checker(UnionSchema(*options))
