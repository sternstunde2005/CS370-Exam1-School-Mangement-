# Part D — Security Vulnerability Testing and Prevention

## Cross-Site Request Forgery (CSRF)

The original application accepted grade updates from an authenticated session without checking a CSRF token. A form on another origin could submit a request using the browser's existing login cookie, affecting the integrity of student records. I tested the original `/admin_dashboard` route using an administrator session and a request without a token. The server returned 302 and saved the change. The fix generates a random token tied to the signed session and checks it before processing unsafe HTTP methods. Login, registration, grade updates, and logout forms include this token. Logout now uses POST. The publicly known session signing key was also replaced with an environment-provided or randomly generated key. Retesting missing, incorrect, and other-session tokens returned 400 with no changes to grades or absences. Valid form submissions still worked.

## Improper Input Validation

The original grade form had browser restrictions, but the server wrote submitted values directly to SQLite. Sending a grade of 99, negative absences, or a nonexistent student ID succeeded. Invalid records could distort academic results and reports. I added server-side checks before database writes. Grades must be finite numbers between 0 and 20, absences must be nonnegative integers within the chosen nine-digit limit, and the student must exist. Module and teacher lengths, academic years, and semesters are also checked. In retesting, all 13 invalid input cases returned 400 and left both academic tables unchanged. Grades of 0, 20, and 15.5 were accepted and stored correctly. Login, registration, dashboards, the performance API, and CSV, Excel, and PDF exports passed the included regression checks.

The tests use Flask's test client and disposable copies of the supplied fictional database. There are 30 checks against the fixed application. Full observations are in `part_d/test-results.json`; repeat them with `python part_d/verify.py`. Browser demonstrations are provided as instructions and have not been executed in this environment. The CSRF demonstration uses two localhost ports to test different origins with same-site cookies. This is not evidence that every browser sends cookies in every cross-site scenario. Before-validation rows record the original behavior rather than assert security. Baseline code was preserved from the uploaded project, without introducing artificial vulnerabilities.

## Short presentation script

“My contribution was Part D. I tested CSRF and improper input validation in our existing application. First, the original server accepted a grade update without a CSRF token. After my fix, the same request is rejected, while a normal form still works. Second, the original server accepted grades outside the 0-to-20 range and negative absences. I added checks on the server before any records are written. The invalid requests now return 400. My tests also compare database contents so I can show that rejected requests do not change the records.”

## Sources and attribution

Original application by zaydkassimi, revision cb6035cebfd40da5a244e2671d3a9631018e25a2, with the group's supplied Part A and audit logging changes. The upstream archive does not declare a license according to the supplied repository notes. Preserve those notes when integrating this work.

- https://github.com/zaydkassimi/school-management
- https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html
- https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html
