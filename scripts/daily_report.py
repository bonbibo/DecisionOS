#!/usr/bin/env python3
"""Write yesterday's operations summary to reports/YYYY-MM-DD.md.

Also emails it to OPS_EMAIL if that's set (file is always written either way):

    python scripts/daily_report.py [--day YYYY-MM-DD]
"""

import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.channels.email import send_email  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.reports import compute_daily_report, render_daily_report  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--day", default=None, help="YYYY-MM-DD, defaults to yesterday (UTC)")
    args = parser.parse_args()
    day = date.fromisoformat(args.day) if args.day else None

    db = SessionLocal()
    try:
        report = compute_daily_report(db, day)
    finally:
        db.close()

    text = render_daily_report(report)
    output_dir = Path("reports")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / f"{report.day.isoformat()}.md"
    output_path.write_text(text, encoding="utf-8")
    print(f"Wrote {output_path}")

    settings = get_settings()
    if settings.ops_email:
        send_email(settings.ops_email, f"Günlük Rapor — {report.day.isoformat()}", text)
        print(f"Emailed to {settings.ops_email}")


if __name__ == "__main__":
    main()
