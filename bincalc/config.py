from lib.accessor import DictAccessor, AccessorManager
from lib.accessor import expect_str, expect_int, expect_bool, expect_oneof
from shared.context import Context

_ammgr = AccessorManager()

def accessors():
    if "__ammgr" in Context.GlobalValueTable:
        return Context.GlobalValueTable["__ammgr"]

    _ammgr = AccessorManager()
    Context.GlobalValueTable["__ammgr"] = _ammgr
    return _ammgr

class DisplyType:
    Dec = "dec"
    Hex = "hex"
    Bin = "bin"

class GeneralConfig:
    Debug = accessors().dict_access("debug", expect_bool(), default_val=False)

    DisplyType = accessors().dict_access("disp",
                        expect_oneof(DisplyType.Dec, DisplyType.Bin, DisplyType.Hex),
                        default_val="hex")


#### Arch dependent binary config

class BinConfig:
    Arch = accessors().dict_access("arch:arch", expect_str())
    Bits = accessors().dict_access("arch:bits", expect_int())

    Endian = accessors().dict_access("arch:endian", expect_str())

    MmuVABits = accessors().dict_access("arch:mmu:va_bits", expect_int())
    MmuPABits = accessors().dict_access("arch:mmu:pa_bits", expect_int())
    MmuPgGran = accessors().dict_access("arch:mmu:page_granule", expect_int())
    MmuLevels = accessors().dict_access("arch:mmu:ptw_level", expect_int())


class BinArch:
    X86_64 = "x86_64"
    X86_32 = "x86_32"
    Arm64  = "arm64"

class BinEndian:
    Big = "be"
    Little = "le"

def mmu_config(c, va, pa, gran_order, levels):
    BinConfig.MmuVABits[c] = va
    BinConfig.MmuPABits[c] = pa
    BinConfig.MmuPgGran[c] = gran_order
    BinConfig.MmuLevels[c] = levels

def preset_x86_64_base():
    c = {}
    BinConfig.Arch[c] = BinArch.X86_64
    BinConfig.Bits[c] = 64
    BinConfig.Endian[c] = BinEndian.Little
    
    return c

def preset_x86_64_LA48():
    c = preset_x86_64_base()

    mmu_config(c, 48, 48, 12, 4)
    return c

def preset_x86_64_LA57():
    c = preset_x86_64_base()

    mmu_config(c, 57, 52, 12, 4)
    return c


def preset_arm64_base(endian):
    c = {}
    BinConfig.Arch[c] = BinArch.Arm64
    BinConfig.Bits[c] = 64
    BinConfig.Endian[c] = endian

    return c

def preset_arm64_le_va48_4k():
    c = preset_arm64_base(BinEndian.Little)
    
    mmu_config(c, 48, 48, 12, 4)
    return c

def preset_arm64_le_va48_16k():
    c = preset_arm64_base(BinEndian.Little)
    
    mmu_config(c, 48, 48, 14, 4)
    return c

def preset_arm64_le_va48_64k():
    c = preset_arm64_base(BinEndian.Little)
    
    mmu_config(c, 48, 48, 16, 4)
    return c

def preset_arm64_le_va48_pa52_4k():
    c = preset_arm64_base(BinEndian.Little)
    
    mmu_config(c, 48, 52, 12, 4)
    return c

def preset_arm64_le_va48_pa52_16k():
    c = preset_arm64_base(BinEndian.Little)
    
    mmu_config(c, 48, 52, 14, 4)
    return c

def preset_arm64_le_va48_pa52_64k():
    c = preset_arm64_base(BinEndian.Little)
    
    mmu_config(c, 48, 52, 16, 4)
    return c

def arch_preset():
    return {
            "arm64_base": preset_x86_64_base,
            "x86_64_base": preset_x86_64_base,
            "x86_64_LA48": preset_x86_64_LA48,
            "x86_64_LA57": preset_x86_64_LA57,
            "arm64_le_va48_4k": preset_arm64_le_va48_4k,
            "arm64_le_va48_16k": preset_arm64_le_va48_16k,
            "arm64_le_va48_64k": preset_arm64_le_va48_64k,
            "arm64_le_va48_pa52_4k": preset_arm64_le_va48_pa52_4k,
            "arm64_le_va48_pa52_16k": preset_arm64_le_va48_pa52_16k,
            "arm64_le_va48_pa52_64k": preset_arm64_le_va48_pa52_64k,

            "mmu": mmu_config
    }

