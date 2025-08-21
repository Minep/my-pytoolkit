from pathlib import Path
from sys import argv
import re

file = argv[1]

steps = [
    (re.compile(r"@", re.MULTILINE), r'\\'),
    (re.compile(r"\(`(.*?)`\);", re.MULTILINE), r'{\1}'),
    (re.compile(r"\(", re.MULTILINE), '{'),
    (re.compile(r"\)", re.MULTILINE), '}'),
    (re.compile(r";", re.MULTILINE), ' '),
    (re.compile(r"%", re.MULTILINE), ''),
    (re.compile(r"regst", re.MULTILINE), 'textit'),
    (re.compile(r"emphasis", re.MULTILINE), 'emph'),
    (re.compile(r"\\section", re.MULTILINE), r'\\section{}'),
    (re.compile(r"\\br{}", re.MULTILINE), ''),
    (re.compile(r"^--", re.MULTILINE), '%'),
]

with open(file, 'r') as f:
    words = f.read()
    for regex, target in steps:
        regex: re.Pattern = regex
        words = regex.sub(target, words)
        print(target)
    with open(argv[2], 'w') as f2:
        f2.write(words)
