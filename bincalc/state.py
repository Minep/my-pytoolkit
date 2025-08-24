from shared.context import Context

class GlobalState:
    def __init__(self):
        self.config = {}


def global_state():
    if "__gs" not in Context.GlobalValueTable:
        Context.GlobalValueTable["__gs"] = GlobalState()
    return Context.GlobalValueTable["__gs"]
