"""
Regenerate the committed golden files.

    .venv/Scripts/python.exe -m tests.golden_regen              # all reports
    .venv/Scripts/python.exe -m tests.golden_regen euro_ncap_side_barrier

Regeneration is always a **deliberate** act: the golden tests never rewrite the
files themselves. When a refactor step legitimately changes a number, run this,
inspect ``git diff tests/golden/``, and explain the diff in the progress log.
"""
from __future__ import annotations

import logging
import sys

from tests import golden_utils


def main(argv: list[str]) -> int:
    logging.basicConfig(level=logging.ERROR)

    stems = argv or sorted(golden_utils.BUILDERS)
    unknown = [stem for stem in stems if stem not in golden_utils.BUILDERS]
    if unknown:
        print(f"unknown report(s): {', '.join(unknown)}", file=sys.stderr)
        print(f"available: {', '.join(sorted(golden_utils.BUILDERS))}", file=sys.stderr)
        return 2

    for stem in stems:
        print(f"regenerating {stem} ...", flush=True)
        data = golden_utils.produce_isolated(stem)
        golden_utils.store(stem, data)
        tests = len(data["results"])
        print(f"  -> {golden_utils.golden_path(stem)}"
              f" ({tests} test(s), {len(data['print_results'])} printed lines)")

    print("\nDone. Review `git diff tests/golden/` before committing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
