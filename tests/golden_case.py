"""Child-process entry point used by the result-golden test and regenerator."""

from __future__ import annotations

import json
import logging
import sys

from tests import golden_utils


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    json.dump(golden_utils.produce(sys.argv[1]), sys.stdout, sort_keys=True)
