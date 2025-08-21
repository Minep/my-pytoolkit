import os
import os.path

from importlib.abc import Loader, MetaPathFinder
from importlib.util import spec_from_file_location

class ExtendableImporter(MetaPathFinder):
    def __init__(self, common_global, base_path=None):
        super().__init__()

        self._global = common_global
        self.__path  = os.getcwd() if base_path is None else base_path

    def find_spec(self, fullname, path, target=None):
        if path is None or path == "":
            path = []

        path.append(self.__path)
        for p in self.search_paths():
            path.append(p)
        
        if "." in fullname:
            *parents, name = fullname.split(".")
        else:
            resolved = self.resolve(fullname, path, target)
            if resolved is not None:
                path, name = resolved
            else:
                name = fullname

        for entry in path:
            if os.path.isdir(os.path.join(entry, name)):
                filename = os.path.join(entry, name, "__init__.py")
                submodule_locations = [os.path.join(entry, name)]
            else:
                filename = os.path.join(entry, name + ".py")
                submodule_locations = None

            if not os.path.exists(filename):
                continue

            return spec_from_file_location(
                        fullname, filename,
                        loader=MyLoader(filename, self._global),
                        submodule_search_locations=submodule_locations)

        return None

    def search_paths(self):
        return []

    def resolve(self, fullname, path, target):
        return None


class MyLoader(Loader):
    def __init__(self, filename, common_global):
        self.filename = filename
        self.__g = common_global

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        with open(self.filename) as f:
            data = f.read()

        v = vars(module)
        v.update(self.__g)
        co = compile(data, self.filename, mode='exec')
        exec(co, v)

