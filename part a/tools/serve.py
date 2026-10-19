from pathlib import Path
import os
import sys


BUNDLE_ROOT = Path(__file__).resolve().parents[1]
WEBSITE_ROOT = BUNDLE_ROOT / "website"
os.chdir(WEBSITE_ROOT)
sys.path.insert(0, str(WEBSITE_ROOT))

from app import app, init_db  # noqa: E402


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
