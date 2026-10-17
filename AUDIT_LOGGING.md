# Security Logging and Audit Trail

**Project:** CS 370 — School Management System  
**Module:** Part E — Security Logging & Integration Testing

## 1. Overview

This module records security-related activities in the School Management System using Python and SQLite.

The logging functionality is implemented in `audit_logger.py`. Audit records are stored in the `audit_logs` table of the local `school.db` database.

Each log entry contains:
- Timestamp (UTC)
- User ID
- Action
- Success or failure status
- Brief event description

Passwords, session tokens, and other sensitive credentials must not be included in audit logs.

## 2. Implemented Logging Events

| Event | Description | Status |
|---|---|---|
| `LOGIN` | Successful administrator and student login | Tested |
| `LOGIN` | Failed login attempts | Tested |
| `UNAUTHORIZED_ACCESS` | Student attempts to access an admin-only resource | Tested |
| `STUDENT_RECORD_UPDATED` | Administrator updates student grades or attendance | Tested |
| `STUDENT_REGISTERED` | New student account is registered | Tested |

The `success` field stores `1` for successful actions and `0` for failed or denied actions.

## 3. How to Use the Logging Module

Import the logger in `app.py`:

```python
from audit_logger import log_event
```

Example of recording a successful operation:

```python
log_event(
    user_id=session.get('user_id'),
    action='STUDENT_RECORD_UPDATED',
    success=True,
    details='Student record updated successfully'
)
```

The logger automatically creates the `audit_logs` table if it does not exist.

## 4. Automated Testing

Three unit tests are provided in `test_audit_logger.py`:

1. `test_table_creation` — verifies that the audit table is created.
2. `test_successful_event` — verifies that successful events are saved.
3. `test_failed_event` — verifies that failed events are saved.

Run the tests from the project directory:

```bash
.venv/bin/python -m unittest -v test_audit_logger
```

**Current test result:** 3 tests passed.

Tests use temporary SQLite databases and do not modify the main `school.db`.

## 5. Integration Notes

The following work requires coordination with other team members:

- Integrate audit events with the final authentication implementation.
- Add audit logging for student personal information changes.
- Add logging for authorized faculty administrative operations.
- Run integration tests after the team's changes are merged.

The database path is resolved relative to `audit_logger.py` to avoid working-directory issues.

## 6. Security Considerations

- Use parameterized SQL queries for log insertion.
- Do not record passwords, password hashes, authentication cookies, or session tokens.
- Ensure only authorized users can access audit records.
- Review audit logging after authentication and authorization code changes.

Audit logging supports security monitoring but does not replace authentication or authorization controls.