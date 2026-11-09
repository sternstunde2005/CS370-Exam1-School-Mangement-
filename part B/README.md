# Part B — Authentication and Password Security

Contributor: Shuyang Qiu. Course: CS 370.

This is a runnable Part B contribution built on the uploaded team's `PartC/website` snapshot. It retains that snapshot's C role checks, D CSRF/input checks and E audit logger. Those retained features are teammates' work. It does not claim that all C/D/E requirements or the entire team project are complete.

## Run on macOS or Linux (Python 3.10+)

Open a terminal in `PartB`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r website/requirements.txt
python website/setup_demo.py
python website/run.py
```

Open http://127.0.0.1:5001. `setup_demo.py` refuses to overwrite an existing database. It creates fictional data only. On Windows, use `py -m venv .venv` and `.venv\Scripts\activate` in place of the first two commands; remaining commands are the same. The team's old bundled Windows Python runtime does not include Argon2; use the new virtual environment.

| Account username (email used as login ID) | Password | Role |
|---|---|---|
| student3@example.test | DemoPass123! | Student |
| faculty2@example.test | DemoPass123! | Faculty |
| admin1@example.test | DemoPass123! | Admin |
| student4@example.test | DemoPass123! | Student |
| faculty5@example.test | DemoPass123! | Faculty |

These public credentials are for the local demonstration only. The app does not seed users automatically. `manage_access.py` remains the trusted local tool for creating faculty/admin accounts.

## Run all tests

From `PartB`, with the virtual environment activated:

```bash
python verify.py
```

**Verified result: 52 automated tests passed, plus 5 real HTTP smoke checks.**

Tests use disposable SQLite databases and leave your demonstration data unchanged. The runner writes `evidence/test-results.txt` and `evidence/test-results.json`, exits nonzero on a failure, and includes the retained C/E suites. See the checked-in evidence for the measured result, environment and timestamp. Existing permission tests were updated for salted-hash verification, explicit HTTP 401 on bad logins, and a registration password meeting the new minimum. No authorization assertions were removed.

## Requirement mapping

| Part B requirement | Implementation | Test evidence |
|---|---|---|
| Student/faculty username and password | Existing unique account email is the username; database role determines destination | `test_student_and_faculty_login` |
| Secure password storage | Argon2id with random salt: 64 MiB, 3 iterations, parallelism 4 | `test_salted_argon2id_storage`, registration test |
| Incorrect credentials rejected | Generic error and HTTP 401; parameterized SQL | `test_incorrect_unknown_and_sql_injection_credentials` |
| Limit repeated failures | SQLite counters: 5/account, 30/source IP, 15-minute windows; HTTP 429 at limit | account/IP/expiry/reset tests |
| Logout/session termination | CSRF-protected POST; delete server session; clear cookie; fixed 30-minute server expiry | logout replay, expiry, CSRF tests |
| Protect private pages/functions | Validate server session before existing server-side RBAC checks | protected-resources and retained permission tests |

## Design details

- `security_b.py`: password hashing/verification, failure counters, session records, session validation and no-store headers.
- `app.py`: login/logout integration, schema initialization and registration validation. `hash_password` stays importable for existing provisioning scripts.
- `auth_sessions` stores a SHA-256 digest of a random 256-bit session token, user ID, password-hash snapshot and absolute expiry. SHA-256 here is for a high-entropy random token, **not for new passwords**. Only the signed, HttpOnly cookie contains the raw token. Password changes invalidate earlier sessions.
- The authentication hook runs before C's identity lookup. The user role is still reread from the database on every request. Forged/stale identity cookies alone are insufficient.
- Login clears and replaces session state and its CSRF token. Logout revokes that browser's session; other independently logged-in browsers remain logged in.
- Counters are database-backed, so a fresh browser or application restart cannot reset them. A SQLite immediate transaction serializes checks/increments. Expired rows are cleaned up at login. A successful login clears account failures but does not clear the source IP failure budget.
- The 15-minute window starts at the first failure, not at the fifth. This is a small local teaching application: SQLite serialization and IP limits can affect shared-address users. No proxy forwarding headers are trusted; deployment behind a proxy requires separately configured trusted proxy handling.
- Existing 64-character SHA-256 password hashes are verified only for migration, then upgraded to Argon2id after a successful login. Incorrect passwords never trigger migration. Accounts that have not logged in retain their old hashes and need login/reset before a complete database migration can be claimed. A fresh demo database contains only Argon2id passwords.
- New web registrations require 12–1024 characters. Existing account passwords are accepted for migration; local staff provisioning retains C's original nonempty-password rule.
- Audit events retain E's LOGIN format, and B adds LOGOUT. No passwords, hashes or authentication tokens are logged. Rate-limited attempts are recorded as failed LOGIN events.
- HTTP local demo: HttpOnly, SameSite=Lax cookies and no-store responses. When deploying through HTTPS, set `COOKIE_SECURE=1` and a strong persistent `SECRET_KEY`. Without SECRET_KEY, the app generates a random process key and a restart signs out users. Multi-worker deployments need one shared secret. TLS deployment is not claimed here.

## Integration into the team repository

Upload the entire `PartB` folder at the repository root as a separate contribution. Run `PartB/website/run.py` to demonstrate B. Simply adding the folder does **not** change the running app in `part a/website` or `PartC/website`.

`changes.patch` describes only B's changes against the uploaded `PartC/website` baseline, plus new B modules/tests. After reviewing with the team, from the repository root:

```bash
git apply --check PartB/changes.patch
git apply PartB/changes.patch
python -m pip install -r PartC/website/requirements.txt
python PartC/website/run.py
```

Stop if the check fails: a teammate has changed those files, so merge the listed changes manually instead of overwriting them. Initialization adds the B tables without deleting existing student records. Back up the existing SQLite file before any team integration. Run B/C/E tests against the actual merged app as well; `PartB/verify.py` tests this packaged copy, not another directory.

Do not replace the root audit logger or teammates' folders wholesale. The root README should eventually point to the single application directory the team chooses. The frozen copies may diverge if teammates continue working.

## Sources and attribution

- Original selected project: https://github.com/zaydkassimi/school-management (provided source commit `cb6035cebfd40da5a244e2671d3a9631018e25a2`).
- Direct baseline: `PartC/website` in the supplied team ZIP, archive commit `31dd3feaf5100277aa25b5d26204b2cded4d6809`.
- Password API: https://argon2-cffi.readthedocs.io/en/stable/api.html
- Argon2 implementation is provided by `argon2-cffi`, not a homemade cryptographic algorithm.
- Preserve the team's source/licensing notes: the selected upstream snapshot did not declare a license; the team's root LICENSE does not relicense upstream code.
- B implementation and documentation were prepared with ChatGPT assistance. Review and understand them before presentation/check-off, and follow the instructor's disclosure requirements.
