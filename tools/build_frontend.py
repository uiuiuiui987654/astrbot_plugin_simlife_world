"""Build the panel's large frontend files from their source fragments.

The panel still loads single files (app.js, style.css, assets/destination-3d.js,
assets/room-3d-models.js); their sources now live in views/life/src/<bundle>/ as
ordered fragments. Each output is the fragments concatenated in file-name order,
preceded by a one-line "generated" banner. No minification or rewriting happens,
so every fragment can be read and diffed on its own.

    python tools/build_frontend.py          # rebuild every bundle
    python tools/build_frontend.py --check  # exit 1 if an output is out of date

Edit the fragments, not the generated files. Remember to bump the matching ?v=
version in views/life/index.html after changing a bundle.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIFE = ROOT / "views" / "life"

# output file -> fragment directory (relative to views/life)
BUNDLES = {
    "app.js": "src/app",
    "style.css": "src/style",
    "assets/destination-3d.js": "src/destination-3d",
    "assets/room-3d-models.js": "src/room-3d-models",
}


def banner(output: str, source: str) -> bytes:
    text = "由 views/life/%s/ 下的片段生成，请勿直接修改；改完片段后运行 python tools/build_frontend.py" % source
    return ("/* %s */\n" % text).encode("utf-8")


def build(output: str, source: str) -> bytes:
    folder = LIFE / source
    suffix = Path(output).suffix
    parts = sorted(p for p in folder.iterdir() if p.is_file() and p.suffix == suffix)
    if not parts:
        raise SystemExit("no fragments in %s" % folder)
    return banner(output, source) + b"".join(p.read_bytes() for p in parts)


def main(argv: list[str]) -> int:
    check = "--check" in argv
    stale = []
    for output, source in BUNDLES.items():
        data = build(output, source)
        target = LIFE / output
        current = target.read_bytes() if target.exists() else b""
        if current == data:
            print("up to date  %s" % output)
            continue
        if check:
            stale.append(output)
            print("OUT OF DATE %s" % output)
        else:
            target.write_bytes(data)
            print("built       %s (%d bytes)" % (output, len(data)))
    if stale:
        print("run: python tools/build_frontend.py")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
