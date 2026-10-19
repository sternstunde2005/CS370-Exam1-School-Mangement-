from pathlib import Path
import shutil
import sqlite3


BUNDLE_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = BUNDLE_ROOT / "website" / "school.db"
OUTPUT_DIR = BUNDLE_ROOT / "database"


def export_database() -> None:
    if not DATABASE_PATH.exists():
        raise SystemExit("website/school.db does not exist. Run seed_demo.py first.")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    snapshot = OUTPUT_DIR / "school-demo.sqlite3"
    dump = OUTPUT_DIR / "school-demo.sql"
    shutil.copy2(DATABASE_PATH, snapshot)
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        dump.write_text("\n".join(connection.iterdump()) + "\n", encoding="utf-8", newline="\n")
    finally:
        connection.close()
    print(f"Database snapshot: {snapshot}")
    print(f"SQL dump: {dump}")


if __name__ == "__main__":
    export_database()
