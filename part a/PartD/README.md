# Part D — Testing and Demonstration Guide

The two selected vulnerabilities are CSRF and Improper Input Validation. Both were reproduced in the original application's grade submission endpoint.

## Run the automated checks

Place this folder inside the original project's `part a` folder and name it `Part-D`. Open PowerShell in `Part-D` and run

```powershell
..\runtime\python.exe .\part_d\verify.py
```

Results are written to `part_d/test-results.json`. Tests use temporary database copies. A BEFORE PASS means the original behavior was reproduced or observed. An AFTER PASS means a protection or normal operation met its assertion. All 30 checks against the fixed application passed under Linux with Python 3.12 and Flask 2.3.3. The Windows portable runtime and live browser demonstration have not been tested in this environment.

To run this package with a separately installed Python, use

```powershell
python -m pip install -r .\website\requirements.txt
python .\part_d\verify.py
```

## Live demonstration

Use the fictional data included in this package. Each demonstration server uses a temporary copy that is removed when the server stops.

1. From Part-D, run `..\runtime\python.exe .\part_d\demo.py before`. Open http://127.0.0.1:5001 and sign in with username `admin` and password `admin`.
2. Open another PowerShell window in the same folder. Run `..\runtime\python.exe -m http.server 8001 --bind 127.0.0.1 --directory part_d`.
3. Open http://127.0.0.1:8001/csrf_demo.html and click the submit button. On the administrator page, select academic year 2024-2025 and find the CSRF Demo module with a grade of 19. The submitted form comes from another origin and contains no CSRF token.
4. In the administrator's grade form, choose a student and enter a new module with otherwise valid values. Press F12, find the grade input in Elements, and change its max attribute from 20 to 100. Submit a grade of 99. The original application accepts it. You can also change the absence input's min attribute to -10 and submit -5.
5. Press Ctrl+C in the first terminal. Run `..\runtime\python.exe .\part_d\demo.py after`, refresh the login page, and sign in again.
6. Repeat step 3. The request returns HTTP 400 and creates no academic record. Repeat step 4, which also returns HTTP 400. Reopen the administrator page and submit valid values, such as a grade of 15.5 and 2 absences. This submission succeeds.
7. Show `part_d/test-results.json`. Explain that the tests compare database records to verify that rejected requests do not cause partial writes.

The CSRF demonstration uses the same host with different ports. These are different origins within the same site, allowing the browser to send the login cookie. Cross-site cookie behavior also depends on the browser's SameSite policy. The automated tests verify server-side handling of requests with a session; they do not simulate browser cookie policies.

## Merge into the team project

The `website` folder contains the application modified from the uploaded project ZIP. Test it separately, then merge the changes into `part a/website`.

The modified application files are `app.py`, the new `security_d.py`, and four templates — `login.html`, `register.html`, `admin_dashboard.html`, and `base.html`. The relevant code changes are recorded in `part_d/changes.patch`. The `part_d/baseline` folder is for temporary local demonstrations only.

If Parts B, C, or E have newer changes, merge the patch carefully to preserve your teammates' work. Every POST form needs a hidden csrf_token field. Test scripts must first GET a form and then submit its session token with the POST request. Existing tests in verify_app.py/test_app.py that submit directly also need this update. Logout now uses POST; GET /logout returns 405.

The original fixed SECRET_KEY has been replaced with the SECRET_KEY environment variable, with a randomly generated key for each process startup when the variable is absent. Single-process local demonstrations can use the default. Restarting the server requires signing in again. Multi-process deployments should configure one shared random secret. If Part B later clears the session during login, generate a fresh token when rendering the next form.

Validation follows the original application's 0–20 grading scale and semesters 1 and 2. Added rules require consecutive academic years, a maximum of 100 characters each for module and teacher names, and nonnegative integer absence counts of up to nine digits. Confirm these business limits with the team during integration. Existing records have not been bulk-modified. New submissions must reference an existing student, and validation happens before any grade or absence writes.

Part D's input checks focus on grade and absence submissions. SHA-256 password hashing, the hardcoded administrator login, and Faculty permissions still require work from Parts B and C. The existing audit_logger.py and its calls are retained. The overall project report has a two-page limit; condense the two main sections of REPORT_EN.md into the team report.
