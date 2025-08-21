from pathlib import Path

class ResourceScope:
    def __init__(self, base, *args):
        if not isinstance(base, Path):
            base = Path(base)

        if base.is_file():
            base = base.parent

        self.__base = base / Path(*args)

    def locate(self, *args):
        return ResourceScope(self.__base, *args)

    def base(self):
        return str(self.__base.absolute())

    def __getitem__(self, index):
        parts = [index]

        if isinstance(index, tuple):
            parts = [*index]

        parts2 = []
        for p in parts:
            if isinstance(p, Path):
                if p.is_absolute():
                    return p

                parts2 += p.parts
            else:
                parts2.append(p)

        return self.__base / Path(*parts2)
