# Part B — speaking notes and report material

## Short presentation (about 1–2 minutes)

My part is authentication and password security. I started with our group's existing application. Students and faculty use their account email as their username.

The old version used SHA-256 for passwords. I changed new password storage to Argon2id. It uses a random salt, so two users with the same password have different stored hashes. The library verifies the password without storing the original password. Old accounts are upgraded after a successful login.

I also added a limit on failed login attempts. If an account has five failed attempts in a fifteen-minute window, the application temporarily blocks more attempts. These counters are stored in SQLite, so opening a new browser does not reset them. There is also a limit for each source IP address.

For sessions, the server checks a random session token before allowing access. A session expires after thirty minutes. Logout removes the server's session record and clears the browser session. Even a copied old cookie cannot be reused after logout.

My tests cover successful student and faculty logins, incorrect passwords, lockout, protected pages, password storage, and logout. I also reran our existing permission and audit tests to check compatibility.

## Suggested report paragraph (edit into the team's two-page report)

Part B replaces new SHA-256 password storage with salted Argon2id hashes and upgrades legacy hashes after successful authentication. Students and faculty log in using their unique account email. Parameterized account queries and generic errors reject invalid credentials. Persistent SQLite counters limit failures to five per account and thirty per source IP in a fifteen-minute window. Random server-tracked sessions expire after thirty minutes; CSRF-protected POST logout revokes the current session, and copied cookies fail after revocation. Existing role checks reject unauthenticated access to protected pages and APIs. Integration tests cover these controls along with the retained authorization and audit suites; the result is recorded in PartB/evidence.

## Limits to explain accurately

This is a local development demonstration, not an Internet deployment. HTTPS and secure-cookie deployment configuration remain necessary before deployment. Legacy hashes are migrated when the user successfully logs in, not all at startup. The account email is the username; there is no second username field. The package retains teammates' existing features and does not independently complete every Part C/D/E requirement.
