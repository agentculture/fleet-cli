"""Entry point for ``python -m fleet``."""

from __future__ import annotations

import sys

from fleet.cli import main

if __name__ == "__main__":
    sys.exit(main())
