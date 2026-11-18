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

Open the local URL printed in the server terminal (normally http://127.0.0.1:5000). Use that same port throughout the demonstration; if the server uses port 5001, use 5001 in all browser URLs. `setup_demo.py` refuses to overwrite an existing database. It creates fictional data only. On Windows, use `py -m venv .venv` and `.venv\Scripts\activate` in place of the first two commands; remaining commands are the same. The team's old bundled Windows Python runtime does not include Argon2; use the new virtual environment.

| Account username (email used as login ID) | Password | Role |
|---|---|---|
| student3@example.test | DemoPass123! | Student |
| faculty2@example.test | DemoPass123! | Faculty |
| admin1@example.test | DemoPass123! | Admin |
| student4@example.test | DemoPass123! | Student |
| faculty5@example.test | DemoPass123! | Faculty |

These public credentials are for the local demonstration only. The app does not seed users automatically. `manage_access.py` remains the trusted local tool for creating faculty/admin accounts.

## Restart the application

Keep the server terminal open while using the website. Press **Control+C** in that terminal to stop it.

For later sessions, open a terminal in `PartB` and run:

```bash
source .venv/bin/activate
python website/run.py
```

If the folder is on your Mac desktop, first run `cd ~/Desktop/PartB`. Otherwise, type `cd ` (with a trailing space), drag the `PartB` folder into Terminal, and press Return. Windows users should use `.venv\Scripts\activate` to activate the environment.

You do not need to recreate the virtual environment or rerun `setup_demo.py` each time. Dependency installation requires an internet connection. Do not delete useful demonstration data to reset a login limit.

## Run all tests

From `PartB`, with the virtual environment activated:

```bash
python verify.py
```

**Previously reported result: 52 automated tests passed, plus 5 real HTTP smoke checks.** This result is recorded in the original project documentation. The tests were not rerun when these two guides were consolidated; run the command above to check your current copy.

Tests use disposable SQLite databases and leave your demonstration data unchanged. The runner writes `evidence/test-results.txt` and `evidence/test-results.json`, exits nonzero on a failure, and includes the retained C/E suites. See the checked-in evidence for the measured result, environment and timestamp. Existing permission tests were updated for salted-hash verification, explicit HTTP 401 on bad logins, and a registration password meeting the new minimum. No authorization assertions were removed.

## Classroom demonstration

Start the server using the setup instructions above. Keep it running in the first terminal. Commands below for a second terminal assume macOS or Linux and start from the `PartB` folder.

1. **Show access protection.** In a private/incognito browser window, open `/student_dashboard` using the server's local URL, for example `http://127.0.0.1:5000/student_dashboard`. Expect HTTP 401 because no user is logged in.
2. **Show successful logins.** Sign in as `student3@example.test` with `DemoPass123!` and show the student page. Log out, then sign in as `faculty2@example.test` with the same password and show the faculty page.
3. **Show incorrect-password rejection.** Log out and submit an incorrect password. Expect `Invalid username or password` and HTTP 401.
4. **Show repeated-failure protection.** Accumulate five failed attempts for the same account within the failure window. Expect the rate-limit message and HTTP 429. A correct password is also blocked while the limit remains active. The 15-minute window starts with the first failure, not the fifth.
5. **Show recovery through an automated test.** You do not need to wait 15 minutes in class. In a second terminal, run the command below. The test simulates expiration and verifies that login works again; it does not unlock the account in your running demonstration database.

```bash
source .venv/bin/activate
cd website
python -m unittest -v test_authentication.AuthenticationTests.test_expired_lock_allows_login
```

An `OK` result means the test passed. The website can remain running in the first terminal.

6. **Show the password algorithm.** In a terminal at `PartB`, with the virtual environment activated, run:

```bash
python website/inspect_auth.py
```

This script prints the algorithm prefix and a log summary, without displaying full password hashes or session tokens. If your terminal is still in `PartB/website` after the previous test, run `cd ..` first.

7. **Show logout protection.** Once login is available, sign in and copy the complete URL of the protected page. Click **Logout**. In the same browser window, paste the copied URL into the address bar and press Return without signing in again. Expect **401 Unauthorized**. Do not rely only on the browser's Back button.

To demonstrate rejection of a copied pre-logout cookie, open a second terminal at `PartB` and run:

```bash
source .venv/bin/activate
cd website
python -m unittest -v test_authentication.AuthenticationTests.test_logout_revokes_copied_cookie
```

An `OK` result confirms that the test saved a cookie before logout and could not use it to access a protected resource afterward. This is a separate automated check from revisiting a protected URL in the browser.

## Questions to explain during the presentation

| Question | Explanation |
|---|---|
| Why replace SHA-256 for passwords? | Plain SHA-256 is fast, and the original password code did not use random salts. Argon2id is designed for password storage and adds memory and computation costs to password guessing. |
| What is a salt? | A random value generated for each password hash. The same password produces different hashes. Verification uses the parameters and salt stored in the hash record. |
| Why store failure counters in the database? | Refreshing the page, changing browsers, or restarting the app should not reset the limits. |
| Why revoke the server session at logout? | Clearing only the browser cookie may leave a previously copied cookie usable. Server-side revocation rejects that old cookie. |
| How are Parts B and C different? | B checks whether a user has proved their identity. C checks whether that user's role may perform an operation. |
| What happens to old password hashes? | A successful login upgrades a legacy SHA-256 hash to Argon2id. Accounts that have not logged in still need migration or a password reset. Fresh demo accounts already use Argon2id. |

`PRESENTATION_NOTES.md` contains simple English speaking notes and report material. It is not the complete group report or final slide deck. The group still needs to coordinate integration, the report, presentation, and check-off.

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

## Upload the contribution to GitHub

1. Extract the project ZIP to obtain the `PartB` folder.
2. Open the team repository and create a personal branch, such as `part-b-authentication`.
3. At the repository root, choose **Add file → Upload files**, then drag in the entire `PartB` folder, preserving its directory structure.
4. Use a commit message such as `Add Part B authentication and password security`.
5. Commit the files and open a pull request for the team to review and merge.

Upload the extracted files rather than only the ZIP archive. Keep the files inside `website` in their existing folder. Exclude `.venv`, local databases, caches, and personal passwords or secrets.

This consolidated guide is named `REMADE.md` as requested. If the team wants it to serve as the standard GitHub folder landing page, rename it to `README.md` when replacing the previous guide.

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
