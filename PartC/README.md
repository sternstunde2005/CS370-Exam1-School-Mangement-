# Part C: Roles and Access Control

This module is based on upstream `zaydkassimi/school-management` at commit `cb6035cebfd40da5a244e2671d3a9631018e25a2`. Its direct code baseline is `part a/PartD/website` from `sternstunde2005/CS370-Exam1-School-Mangement-` at commit `c615cab1dd7513f36f84084bb0f7759e8212666e`. It preserves Part D's CSRF protection, input validation, and existing audit logging. This directory contains a standalone Part C application that can also be merged into the team project.

## Access Rules

| Resource or operation | Student | Faculty | Admin |
|---|---|---|---|
| Student dashboard | Own dashboard only | Denied | Denied; use the Admin dashboard |
| `/api/student_records/<id>` | All courses belonging to the signed-in student | Assigned students and course records only | All students |
| `/api/student_risk/<id>` | Own assessment only | Denied to prevent disclosure of summaries across unassigned courses | All students |
| Faculty dashboard and grade/absence updates | Denied | Assigned record combinations only | Use the Admin dashboard |
| Admin dashboard and updates | Denied | Denied | Allowed |
| School-wide analytics, trend API, and CSV/Excel/PDF exports | Denied | Denied | Allowed |
| Public registration | Always creates a student account | Cannot self-register as Faculty | Cannot self-register as Admin |
| Role changes and teaching assignments | No web endpoint | No web endpoint | Managed through the local CLI by an operator with server access |

Each Faculty assignment is identified by `(faculty_id, student_id, module_name, academic_year, semester)`. Every request loads the account identity and role from `users`; a role declared in the session, form, or URL is not trusted. Unauthenticated requests return **401**, and authenticated requests without permission return **403**. API errors use JSON.

Requests by students for another student's records are rejected before querying those records. Faculty writes validate the complete assignment key inside the database transaction. Rejected writes are rolled back, then logged as `UNAUTHORIZED_ACCESS`. The teacher name comes from the signed-in account, so a submitted form cannot impersonate another teacher.

## Installation, Testing, and Startup

Open PowerShell in the `PartC` directory and use Python 3.12:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\website\requirements.txt
.\.venv\Scripts\python.exe .\verify.py
.\.venv\Scripts\python.exe .\website\setup_demo.py
.\.venv\Scripts\python.exe .\website\run.py
```

Open <http://127.0.0.1:5000>. The default database is `website/school.db`, regardless of the working directory. `setup_demo.py` creates a new database only; it exits if the file already exists to avoid overwriting existing accounts. For an existing database, start the application directly to add the assignment table. This migration can run repeatedly while preserving existing records.

All demo accounts use the password `DemoPass123!`:

| Account | Role and scope |
|---|---|
| `admin1@example.test` | Admin |
| `faculty2@example.test` | Faculty One; Student One's Mathematics / 2024-2025 / S1 |
| `student3@example.test` | Student One; can view Mathematics and Private History |
| `student4@example.test` | Student Two; can view their own Physics record |
| `faculty5@example.test` | Faculty Two; Student Two's Physics / 2024-2025 / S1 |

When signed in as Faculty One, neither the dashboard nor the records API exposes Student One's Private History or Student Two's Physics. When Student One requests `/admin_dashboard`, `/faculty_dashboard`, or `/api/student_records/4`, the application returns 403.

The original hardcoded `admin/admin` login has been removed. All accounts authenticate against the database, using their stored roles. Public registration cannot create Faculty or Admin accounts. A successful login clears the old session; the next rendered form issues a new CSRF token. Automated clients must GET the destination page after login before submitting a POST request.

## Managing Accounts and Teaching Assignments

Run the local CLI from the same directory. Passwords are entered through a hidden prompt rather than passed as command arguments:

```powershell
.\.venv\Scripts\python.exe .\website\manage_access.py create-user --name "New Faculty" --email "faculty@example.test" --role faculty
.\.venv\Scripts\python.exe .\website\manage_access.py assign --faculty-id 2 --student-id 3 --module Mathematics --year 2024-2025 --semester 1
.\.venv\Scripts\python.exe .\website\manage_access.py revoke --faculty-id 2 --student-id 3 --module Mathematics --year 2024-2025 --semester 1
.\.venv\Scripts\python.exe .\website\manage_access.py set-role --user-id 2 --role student
```

To create an administrator, use `create-user --role admin`. Use the account IDs from the actual database; the IDs above refer to the demo data. `set-role` clears the user's existing teaching assignments so that a later promotion does not unexpectedly restore old access. The CLI is a trusted server administration tool. Do not expose it as a public web endpoint or give ordinary students access to it.

## Tests and Evidence

`verify.py` runs **34 test methods: 31 Part C integration tests and 3 existing audit logging tests**. All passed in the recorded Windows/Python 3.12 run. Tests obtain sessions through actual login requests, keep CSRF protection enabled, and use temporary databases without modifying demo or existing databases.

Coverage includes normal role-based login and page access, unauthenticated requests, vertical privilege escalation, horizontal student IDOR, isolation between Faculty accounts, every dimension of the assignment key, teacher name impersonation, forged roles in cookies/forms/URLs, registration privilege escalation, unknown roles, database role demotion, account deletion, assignment revocation, transaction rollback, denial auditing, valid inserts and updates, CSRF, input validation, all three Admin export formats, CLI assignment and demotion, idempotent migration, and logout.

Rejected writes compare `users`, `grades`, `absences`, and `faculty_assignments` before and after the request. The audit table may gain a denial record.

- `evidence/test-results.txt`: individual test results.
- `evidence/test-results.json`: environment, test count, failures, errors, and subtest results.
- `evidence/dependencies.txt`: dependency versions installed for the recorded run.

These are integration tests using Flask's test client and real SQLite databases, not browser end-to-end tests.

## Merging into the Team Repository

To run Part C independently, place this directory at `part a/PartC` while keeping the original `part a/website` and Part D work. To merge it into the main team application, review `changes.patch` against the **Part D website baseline**:

```powershell
# Run from the team repository root. Do not apply directly to the original Part A version.
git apply --check --directory="part a" "part a/PartC/changes.patch"
git apply --directory="part a" "part a/PartC/changes.patch"
```

Patch paths use `website/...`. If the team's `part a/website` does not yet contain Part D, merge Part D first or merge the Part C changes file by file. Run the team application's `init_db()` to create the assignment table. Existing student accounts remain usable; create Faculty and Admin accounts through the CLI.

Run this package's `verify.py` to check the standalone version. To verify the merged application, copy `test_permissions.py` and `test_audit_logger.py` into the team's website directory, then run the following command from that directory:

```powershell
python -m unittest test_permissions test_audit_logger -v
```

The standalone package's test results do not replace verification of the merged team application.

New files include `security_c.py`, `manage_access.py`, `setup_demo.py`, `test_permissions.py`, and the Faculty template. Modified files include `app.py`, `audit_logger.py`, the navigation template, the startup script, and the audit tests' Windows file handle cleanup. `security_d.py` and its CSRF template fields retain the baseline behavior.

Password storage still uses the original SHA-256 implementation. Password hashing upgrades belong to Part B; when merging that implementation, update password creation in the CLI, demo script, and tests accordingly.

See `SOURCE.json` for source repositories and pinned commits. Licensing statements for new coursework code do not relicense upstream code.
