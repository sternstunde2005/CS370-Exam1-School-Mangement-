"""Local demonstration evidence: algorithm labels and audit summaries only."""
from contextlib import closing
from pathlib import Path
import sqlite3

path = Path(__file__).resolve().parent / 'school.db'
if not path.is_file():
    raise SystemExit('Run setup_demo.py first.')
with closing(sqlite3.connect(f'{path.as_uri()}?mode=ro', uri=True)) as conn:
    print('Password storage (full hashes and session tokens are not printed):')
    for email, stored in conn.execute('SELECT email, password FROM users ORDER BY id'):
        print(email, '->', '$argon2id$' if stored.startswith('$argon2id$') else 'legacy/other')
    print('\nRecent security events:')
    if conn.execute("SELECT 1 FROM sqlite_master WHERE name='audit_logs'").fetchone():
        for row in conn.execute('SELECT timestamp, user_id, action, success FROM audit_logs ORDER BY id DESC LIMIT 12'):
            print(*row, sep=' | ')
