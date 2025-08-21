import code
import readline

if __name__ == "__pytool__":
    _l = { **globals() }
    code.interact(
            "pytools interactive shell \n\t"+
            "- python shell in pytool environment", local=_l)
