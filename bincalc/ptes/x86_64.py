from .utils import PteFieldExractor, get_rawrep, BinCalcException
from .state import global_state
from .config import BinConfig

x86_64_pte_common_fields = [
    ("Valid", 0, 0),
    ("R/W", 1, 1),
    ("U/S", 2, 2),
    ("PWT", 3, 3),
    ("PCD", 4, 4),
    ("A",   5, 5),
    ("XD", 63, 63)
]

x86_64_pte_page_fields = [
    *x86_64_pte_common_fields,
    ("Dirty", 6, 6),
    ("Global", 8, 8),
]

def get_l4_pte_fields(cfg):
    pa_bits = BinConfig.MmuPABits[cfg]
    bits = BinConfig.Bits[cfg]

    return [
        *x86_64_pte_page_fields,
        ("PA", pa_bits, 12),
    ]

def get_uppers_pte_field(cfg, level, huge=False):
    pa_bits = BinConfig.MmuPABits[cfg]

    if not huge or level == 0:
        fields = [*x86_64_pte_common_fields]
    else:
        fields = [
            *x86_64_pte_page_fields, 
            ("PAT", 12, 12),
            ("PA", pa_bits, 12),
        ]
    
    if 3 < level <= 2 and huge:
        fields.append(("Prot.Key", 62, 59))

    return fields

def get_fields_for(pte_val, level):
    cfg = global_state().config
    
    raw_bin = get_rawrep(pte_val)
    maybe_huge = (raw_bin & (1 << 7)) != 0

    if level == 3:
        return get_l4_pte_fields(cfg)

    return get_uppers_pte_field(cfg, level, maybe_huge)

def interpret_pte(pte_val, level):
    if not 0 <= level < 4:
        raise BinCalcException(f"invalid pte level: {level}, expect 0~3")

    fields = get_fields_for(pte_val, level)

    extractor = PteFieldExractor(fields)

    extractor.print_intepreted(pte_val)
