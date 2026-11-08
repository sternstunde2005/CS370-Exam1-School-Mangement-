"""Explicit local-only provisioning. Refuses to seed an existing database."""
import argparse
from pathlib import Path
import sqlite3

from app import app, hash_password, init_db


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', default=str(Path(__file__).parent / 'school.db'))
    args = parser.parse_args()
    path = Path(args.database).resolve()
    if path.exists():
        parser.error('Database already exists; use a new path to avoid changing existing accounts.')
    app.config['DATABASE'] = str(path)
    init_db()
    with sqlite3.connect(path) as conn:
        for uid, name, role in [(1, 'Demo Admin', 'admin'), (2, 'Faculty One', 'faculty'),
                                (3, 'Student One', 'student'), (4, 'Student Two', 'student'),
                                (5, 'Faculty Two', 'faculty')]:
            conn.execute('INSERT INTO users (id, name, email, password, role) VALUES (?, ?, ?, ?, ?)',
                         (uid, name, f'{role}{uid}@example.test', hash_password('DemoPass123!'), role))
        conn.executemany('INSERT INTO faculty_assignments VALUES (?, ?, ?, ?, ?)',
                         [(2, 3, 'Mathematics', '2024-2025', '1'), (5, 4, 'Physics', '2024-2025', '1')])
        conn.executemany('''INSERT INTO grades (student_id, module_name, grade, teacher_name,
            academic_year, semester) VALUES (?, ?, ?, ?, ?, ?)''',
            [(3, 'Mathematics', 15, 'Faculty One', '2024-2025', '1'),
             (3, 'Private History', 11, 'Other Teacher', '2024-2025', '1'),
             (4, 'Physics', 17, 'Faculty Two', '2024-2025', '1')])
    print(f'Demo database: {path}')
    print('Password for demo accounts: DemoPass123!')
    print('admin1@example.test / faculty2@example.test / student3@example.test')
    print('student4@example.test / faculty5@example.test')


if __name__ == '__main__':
    main()
