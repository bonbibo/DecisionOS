#!/usr/bin/env python3
"""Regenerate vault/05-Metrikler/dashboard.md from tactic and retro frontmatter.

Run this after filing a retro (or updating a tactic's score frontmatter) so
the dashboard never drifts from the underlying vault notes:

    python scripts/update_metrics.py [--vault vault]
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.metrics import write_dashboard  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault", default="vault", help="Path to the vault directory")
    args = parser.parse_args()

    output_path = write_dashboard(args.vault)
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
