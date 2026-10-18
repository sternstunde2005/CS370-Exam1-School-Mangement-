"""Create a consistent SQLite snapshot and portable SQL dump; does not alter live data."""
from pathlib import Path
import sqlite3
import argparse
from contextlib import closing

root = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser()
parser.add_argument('--name', default='studenthub-backup')
args = parser.parse_args()
if not args.name.replace('-', '').replace('_', '').isalnum():
    parser.error('Name may contain letters, numbers, hyphens and underscores only.')
db_path = root / 'website' / 'db.sqlite3'
with closing(sqlite3.connect(db_path.as_uri() + '?mode=ro', uri=True)) as source:
    target_path = root / 'database' / f'{args.name}.sqlite3'
    sql_path = root / 'database' / f'{args.name}.sql'
    if target_path.exists() or sql_path.exists():
        raise SystemExit(f'Refusing to overwrite an existing backup named {args.name}')
    with closing(sqlite3.connect(target_path)) as target:
        source.backup(target)
        sql = '\n'.join(target.iterdump()) + '\n'
    sql_path.write_text(sql, encoding='utf-8')
print(target_path)
