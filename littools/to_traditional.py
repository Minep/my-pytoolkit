import gzip
import json

from pathlib import Path
from argparse import ArgumentParser

from Shared.context import Context

suppliment = {
        "着": [ord("著")],
        "窜": [ord("竄")],
        "蹿": [ord("竄")],
        "与": [ord("与")],
        "录": [ord("錄")],
}


def get_stmap():
    global suppliment
    p = Context.LocalFiles["stcharmap.json.gz"]
    with gzip.open(p.absolute(), 'rt') as f:
        d = json.load(f)
        d.update(suppliment)
        return d


def convert(stmap, file):
    f = open(file, 'r')

    content = f.read()
    result = []
    for c in content:
        if c.isascii() or c not in stmap:
            result.append(c)
            continue

        result.append(chr(stmap[c][0]))

    f.close()
    return ''.join(result)


def convert_struct(base, files):
    base_dir = Path(base)
    stmap = get_stmap()

    for file in files:
        org_file = Path(file)
        p = base_dir / org_file
        p.parent.mkdir(parents=True, exist_ok=True)

        print("processing", file)

        with p.open('w') as f:
            f.write(convert(stmap, file))


if __name__ == "__pytool__":
    ap = ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("-n", "--nr-maps",
                    action='store_true',
                    help="Display mapping count")

    args = ap.parse_args()

    if args.nr_maps:
        stmap = get_stmap()
        print("Total character map entries:", len(stmap.keys()))
        exit(0)

    convert_struct(args.out, args.files)
