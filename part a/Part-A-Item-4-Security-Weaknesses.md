# Part A Item 4 — Security Weaknesses and Missing Controls

## Scope and authorization

This report completes Part A item 4 for the School Management System selected from the assignment's third suggested GitHub project.

- Upstream repository: <https://github.com/zaydkassimi/school-management>
- Upstream commit reviewed: [`cb6035cebfd40da5a244e2671d3a9631018e25a2`](https://github.com/zaydkassimi/school-management/commit/cb6035cebfd40da5a244e2671d3a9631018e25a2)
- Packaged baseline reviewed: [`60125b53daf25e971701c21e78840e7ba2cdc77e`](https://github.com/sternstunde2005/CS370-Exam1-School-Mangement-/commit/60125b53daf25e971701c21e78840e7ba2cdc77e)
- Assessment date: 2026-11-07
- Test boundary: the authorized local course package and fictional test records only.

The assessment identifies weaknesses in the existing application. It does not implement the later assignment parts or claim that the system is production-ready.

## Method

The application routes, authentication helpers, templates, database writes, and packaged launcher were reviewed at the fixed commits above. Bounded checks were also performed with Flask's local test client and a newly created temporary SQLite database. The delivered `website/school.db` retained the same SHA-256 value before and after the checks. No internet-facing system, real account, or real student record was tested.

Severity reflects the likely impact and ease of exploitation in a deployment that exposes the application. The exact risk can change when external controls such as a reverse proxy, web application firewall, or single sign-on service are present; none of those controls are included in this repository.

## Executive summary

| ID | Potential weakness or missing control | Severity | Primary CIA impact |
| --- | --- | --- | --- |
| SEC-01 | Public, static Flask session signing key permits forged privileged sessions | Critical | Confidentiality, integrity |
| SEC-02 | Hard-coded default administrator credentials | High | Confidentiality, integrity, availability |
| SEC-03 | Student passwords use fast, unsalted SHA-256 | High | Confidentiality |
| SEC-04 | State-changing forms lack CSRF protection | High | Integrity |
| SEC-05 | Login has no application-level throttling or temporary lockout | Medium | Confidentiality, availability |
| SEC-06 | Grade and absence limits are enforced only by the browser | Medium | Integrity, availability |

These six findings exceed the requirement to identify at least three weaknesses or missing controls.

## SEC-01 — Public static Flask session signing key

**Severity:** Critical
**Category:** CWE-321, Use of Hard-coded Cryptographic Key

### Evidence

- [`website/app.py:15`](https://github.com/sternstunde2005/CS370-Exam1-School-Mangement-/blob/60125b53daf25e971701c21e78840e7ba2cdc77e/part%20a/website/app.py#L15) assigns a constant `app.secret_key` that is visible to everyone who can read the repository.
- [`website/app.py:120-138`](https://github.com/sternstunde2005/CS370-Exam1-School-Mangement-/blob/60125b53daf25e971701c21e78840e7ba2cdc77e/part%20a/website/app.py#L120-L138) grants access based on `user_id` and `role` in the Flask session.
- The local verification creates an `admin` session cookie with the published key and receives HTTP 200 from `/admin_dashboard` without submitting a password.

Flask's default session is stored in a signed client cookie. The signature prevents undetected editing only while the signing key remains secret. Here, the repository publishes the active key and the packaged launcher does not replace it.

### Impact

An attacker who can reach a deployed instance can construct a cookie that claims the administrator role. This can expose student names, grades, absences, analytics, and exports (confidentiality) and can permit unauthorized grade or absence changes (integrity). Malicious bulk changes could also reduce availability of trustworthy records.

### Required control

Load a long random secret from a deployment secret store or environment variable, fail startup when it is absent, and use a different value per environment. Rotate the exposed key and invalidate all existing sessions. For a higher-assurance deployment, consider server-side sessions and re-check the current user's role from trusted server-side data for sensitive actions. Flask documents that `SECRET_KEY` signs session cookies in its [configuration reference](https://flask.palletsprojects.com/en/stable/config/#SECRET_KEY).

### Preconditions and false-positive notes

Exploitation requires network access to the application and knowledge of the published source, both realistic for a public repository and exposed web service. An undocumented external gateway could add authentication, but it would not remove the vulnerable application behavior. This is not a false positive in the packaged configuration because no secret override is present.

## SEC-02 — Hard-coded administrator credentials

**Severity:** High
**Category:** CWE-798, Use of Hard-coded Credentials

### Evidence

- [`website/app.py:236-247`](https://github.com/sternstunde2005/CS370-Exam1-School-Mangement-/blob/60125b53daf25e971701c21e78840e7ba2cdc77e/part%20a/website/app.py#L236-L247) accepts `admin` / `admin` and creates an administrator session without consulting the database.
- [`website/run.py:18-21`](https://github.com/sternstunde2005/CS370-Exam1-School-Mangement-/blob/60125b53daf25e971701c21e78840e7ba2cdc77e/part%20a/website/run.py#L18-L21) prints the same credentials.
- The bounded test logs in with this public credential and reaches the administrator route.

### Impact

Anyone who knows or guesses the documented default can read all administrator-visible student data and modify grade and attendance records. The same shared password prevents individual accountability, and a malicious user could corrupt or delete the practical value of the records.

### Required control

Remove the source-code credential. Store administrator identities in a trusted identity system or database using a strong adaptive password hash, provision a unique random initial password through a secret channel, require first-login rotation, and support revocation. Add multi-factor authentication for administrators and never print credentials to logs or consoles.

### Preconditions and false-positive notes

The risk applies when the application is reachable and this login path is enabled. The account is intentionally convenient for a local fictional demo, but that context reduces exposure rather than removing the weakness. It must not be retained in a real deployment.

## SEC-03 — Fast, unsalted SHA-256 password storage

**Severity:** High
**Category:** CWE-916, Use of Password Hash With Insufficient Computational Effort

### Evidence

- [`website/app.py:140-142`](https://github.com/sternstunde2005/CS370-Exam1-School-Mangement-/blob/60125b53daf25e971701c21e78840e7ba2cdc77e/part%20a/website/app.py#L140-L142) applies one SHA-256 operation directly to the password.
- Registration stores that value at [`website/app.py:266-286`](https://github.com/sternstunde2005/CS370-Exam1-School-Mangement-/blob/60125b53daf25e971701c21e78840e7ba2cdc77e/part%20a/website/app.py#L266-L286), and login compares it at [`website/app.py:249-260`](https://github.com/sternstunde2005/CS370-Exam1-School-Mangement-/blob/60125b53daf25e971701c21e78840e7ba2cdc77e/part%20a/website/app.py#L249-L260).
- The local check confirms that two uses of the same password produce the same 64-character SHA-256 digest, demonstrating the absence of a per-password salt and work factor.

### Impact

If the SQLite database is copied or exposed, an attacker can test large password dictionaries rapidly and recognize users who share a password. Recovered passwords may also unlock other services where a student reused the same credential, expanding the confidentiality impact beyond this application.

### Required control

Use a password-specific algorithm with an automatically generated salt and configurable work factor. OWASP's [Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html) prefers Argon2id and provides alternatives such as scrypt, bcrypt, or PBKDF2 for constrained environments. Migrate existing hashes after a successful login or force a password reset; do not attempt to “decrypt” old hashes.

### Preconditions and false-positive notes

Offline cracking requires access to password hashes, so this is primarily a defense-after-database-compromise control. SHA-256 remains a sound general cryptographic hash, but its speed and lack of a built-in work factor make this specific password-storage construction unsuitable.

## SEC-04 — Missing CSRF protection on state-changing forms

**Severity:** High
**Category:** CWE-352, Cross-Site Request Forgery

### Evidence

- The authenticated administrator POST handler changes grades and absences at [`website/app.py:299-357`](https://github.com/sternstunde2005/CS370-Exam1-School-Mangement-/blob/60125b53daf25e971701c21e78840e7ba2cdc77e/part%20a/website/app.py#L299-L357).
- The corresponding form contains no CSRF token at [`website/templates/admin_dashboard.html:80-129`](https://github.com/sternstunde2005/CS370-Exam1-School-Mangement-/blob/60125b53daf25e971701c21e78840e7ba2cdc77e/part%20a/website/templates/admin_dashboard.html#L80-L129). The login and registration forms also have no token.
- The local check submits the administrator update without a CSRF field and confirms that the temporary database is changed.

### Impact

If a logged-in administrator visits attacker-controlled content, the browser may be induced to submit an unwanted update while attaching its session cookie. Successful exploitation can silently alter academic and attendance records (integrity). Login CSRF can also place a victim into an attacker-chosen session in some designs.

### Required control

Add framework-backed CSRF tokens to every state-changing form and reject missing or invalid tokens on the server. Keep state changes off GET routes, configure session cookies with `Secure`, `HttpOnly`, and an appropriate `SameSite` policy, and validate `Origin`/`Referer` as defense in depth. The [OWASP CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html) describes token patterns and layered controls.

### Preconditions and false-positive notes

The victim must have a valid session and encounter attacker-controlled content. Browser `SameSite` defaults can block some cross-site requests, but they are not a replacement for an explicit token and may not cover same-site subdomains or every client. The repository has no application-level CSRF check.

## SEC-05 — No application-level login throttling or temporary lockout

**Severity:** Medium
**Category:** CWE-307, Improper Restriction of Excessive Authentication Attempts

### Evidence

- The complete login handler at [`website/app.py:236-264`](https://github.com/sternstunde2005/CS370-Exam1-School-Mangement-/blob/60125b53daf25e971701c21e78840e7ba2cdc77e/part%20a/website/app.py#L236-L264) has no attempt counter, delay, rate limiter, temporary lock, or security-event record.
- The local test sends 20 consecutive invalid attempts without receiving HTTP 429, after which the public administrator password still succeeds.

### Impact

An attacker can automate password guessing and credential stuffing against student accounts, threatening confidentiality. High request volumes can also consume application resources or lock out users if an external control later adds a poorly designed permanent lockout.

### Required control

Apply progressive delays and rate limits by both account and source, add a bounded temporary lock or challenge after repeated failures, record and alert on suspicious attempts, and offer multi-factor authentication. Avoid permanent account denial based only on attacker-controlled failures. The [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html#login-throttling) provides login-throttling guidance.

### Preconditions and false-positive notes

This test proves that the Flask application itself does not throttle requests. A production reverse proxy or identity provider could supply an external limit, but no such deployment control is included or documented in this repository.

## SEC-06 — Missing server-side validation of grades and absences

**Severity:** Medium
**Category:** CWE-20, Improper Input Validation

### Evidence

- Browser inputs specify limits at [`website/templates/admin_dashboard.html:99-104`](https://github.com/sternstunde2005/CS370-Exam1-School-Mangement-/blob/60125b53daf25e971701c21e78840e7ba2cdc77e/part%20a/website/templates/admin_dashboard.html#L99-L104).
- The server reads submitted strings and writes them without checking numeric type or range at [`website/app.py:302-351`](https://github.com/sternstunde2005/CS370-Exam1-School-Mangement-/blob/60125b53daf25e971701c21e78840e7ba2cdc77e/part%20a/website/app.py#L302-L351).
- A direct local POST stores grade `999` and absence count `-7` in the temporary database, values the browser form was intended to reject.

### Impact

Invalid values can corrupt averages, ranks, risk labels, exports, and attendance results (integrity). Extreme or malformed values can also trigger errors in later calculations or reports, reducing availability. A compromised administrator session makes this issue easier to exploit, but accidental or scripted invalid submissions are enough.

### Required control

Parse and validate every field on the server before opening a write transaction. Enforce grade `0–20`, a non-negative integer absence count, valid academic-year and semester formats, an existing student identifier, and reasonable text lengths. Add SQLite `CHECK` constraints as a second layer and return a clear 4xx validation response without partially writing data.

### Preconditions and false-positive notes

The update route requires an administrator session; this is therefore a privileged integrity weakness rather than an unauthenticated write. HTML constraints improve normal user experience but can be bypassed by any direct HTTP client and are not a server-side security boundary.

## Existing controls observed

The review also confirmed controls that should be preserved:

- Most database values are passed through parameterized SQLite queries rather than concatenated into SQL.
- `login_required` and `admin_required` decorators centralize route checks, although SEC-01 shows that their session input is not trustworthy with the exposed key.
- Jinja templates retain default auto-escaping for normal HTML rendering.
- The packaged `tools/serve.py` launcher binds to `127.0.0.1` and disables debug mode, reducing exposure for the local demo.
- The delivered database contains fictional demonstration identities rather than real student records.

These controls reduce particular risks but do not cancel the six findings above.

## Conditional deployment observation

The one-click packaged launcher is local-only and debug-off. However, the alternative [`website/run.py`](https://github.com/sternstunde2005/CS370-Exam1-School-Mangement-/blob/60125b53daf25e971701c21e78840e7ba2cdc77e/part%20a/website/run.py) binds to all interfaces with debug enabled, and the direct `app.py` entry point also enables debug mode. Neither development entry point should be used on an untrusted network. A production deployment should use a supported WSGI server, debug disabled, TLS at the edge, explicit trusted-host/proxy settings, secure cookie flags, security headers, backups, monitoring, and least-privilege file permissions.

## Prioritized remediation

1. **Immediate:** replace and rotate the session secret; invalidate sessions; remove the `admin/admin` path and printed credential.
2. **High priority:** migrate password hashes to an adaptive salted algorithm and add CSRF tokens to every state-changing request.
3. **Short term:** add login throttling, temporary lockout/challenges, authentication logging, and administrator MFA.
4. **Short term:** enforce server-side type/range checks plus database constraints for academic data.
5. **Before any deployment:** use a production WSGI setup, secure cookie settings, TLS, security headers, monitoring, tested backups, and a repeat security review after changes.

## Limitations

- Results apply to the fixed commits identified above; later changes require reassessment.
- Dynamic checks use Flask's local test client and a temporary SQLite database, not an internet deployment.
- No load test, dependency vulnerability scan, infrastructure review, TLS review, or external penetration test was performed.
- External controls that are not in the repository were not assumed. Their presence could reduce exploitability but would not correct the underlying code.
- The assessment reports potential security impact; it does not claim that real student information has been exposed or that any attack occurred.

## Conclusion

The application is suitable as a local fictional course demonstration, but it lacks several controls required for real student information. The static signing key and default administrator credential create immediate authorization risk; password storage, CSRF protection, login abuse controls, and server-side validation also need remediation before the system is exposed or populated with real records.
