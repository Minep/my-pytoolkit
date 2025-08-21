class GlobalState:
    def __init__(self):
        self.config = {}


_global_state_ = GlobalState()

def global_state():
    global _global_state_
    return _global_state_
