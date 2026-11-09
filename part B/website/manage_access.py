"""Trusted local CLI for staff provisioning; never exposed as a public web route."""
import argparse
from getpass import getpass
from pathlib import Path

from app import app, hash_password, init_db
from security_c import connect_db


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', default=app.config['DATABASE'])
    commands = parser.add_subparsers(dest='command', required=True)
    create = commands.add_parser('create-user')
    create.add_argument('--name', required=True)
    create.add_argument('--email', required=True)
    create.add_argument('--role', choices=['student', 'faculty', 'admin'], required=True)
    role = commands.add_parser('set-role')
    role.add_argument('--user-id', required=True, type=int)
    role.add_argument('--role', choices=['student', 'faculty', 'admin'], required=True)
    for command in ('assign', 'revoke'):
        sub = commands.add_parser(command)
        sub.add_argument('--faculty-id', type=int, required=True)
        sub.add_argument('--student-id', type=int, required=True)
        sub.add_argument('--module', required=True)
        sub.add_argument('--year', required=True)
        sub.add_argument('--semester', choices=['1', '2'], required=True)
    args = parser.parse_args(argv)
    path = Path(args.database).resolve()
    if args.command != 'create-user' and not path.is_file():
        parser.error('Database does not exist.')
    app.config['DATABASE'] = str(path)
    password = None
    if args.command == 'create-user':
        password = getpass('New password: ')
        if not password or password != getpass('Confirm password: '):
            parser.error('Passwords must be nonempty and match.')
    init_db()
    with app.app_context(), connect_db() as conn:
        if args.command == 'create-user':
            conn.execute('INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)',
                         (args.name, args.email, hash_password(password), args.role))
        elif args.command == 'set-role':
            if conn.execute('UPDATE users SET role = ? WHERE id = ?',
                            (args.role, args.user_id)).rowcount != 1:
                parser.error('User does not exist.')
            # Invalidate old assignments when moving into or out of an academic role.
            conn.execute('DELETE FROM faculty_assignments WHERE faculty_id = ? OR student_id = ?',
                         (args.user_id, args.user_id))
        else:
            from security_d import validate_academic_record
            try:
                values = validate_academic_record(dict(student_id=str(args.student_id),
                    module_name=args.module, academic_year=args.year, semester=args.semester,
                    grade='0', absences='0'))
            except ValueError as error:
                parser.error(str(error))
            key = (args.faculty_id, args.student_id, values[1], args.year, args.semester)
            if args.command == 'assign':
                for uid, expected in [(args.faculty_id, 'faculty'), (args.student_id, 'student')]:
                    if not conn.execute('SELECT 1 FROM users WHERE id = ? AND role = ?', (uid, expected)).fetchone():
                        parser.error(f'Account {uid} must have role {expected}.')
                conn.execute('INSERT OR IGNORE INTO faculty_assignments VALUES (?, ?, ?, ?, ?)', key)
            else:
                conn.execute('''DELETE FROM faculty_assignments WHERE faculty_id = ? AND student_id = ?
                    AND module_name = ? AND academic_year = ? AND semester = ?''', key)
    print(f'{args.command} completed.')


if __name__ == '__main__':
    main()
