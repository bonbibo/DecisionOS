#!/usr/bin/env python3
"""Refresh vault/09-Piyasa-Verisi/<dikey>.md for every active vertical.

Run daily via cron (Railway cron job — see docs/MASTER-SPEC-v3.md Package F
for the "İNSAN GEREKLİ" cron setup note):

    python scripts/run_intel.py [--vault vault]
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.intel.aggregate import run_intel  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault", default="vault", help="Path to the vault directory")
    args = parser.parse_args()

    written = run_intel(args.vault)
    if not written:
        print("No intel written (no listings from any adapter this run).")
        return
    for path in written:
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
