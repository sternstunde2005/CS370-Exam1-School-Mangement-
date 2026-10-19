from datetime import datetime, timezone
from pathlib import Path
import json
import os
import sqlite3
import sys


BUNDLE_ROOT = Path(__file__).resolve().parents[1]
WEBSITE_ROOT = BUNDLE_ROOT / "website"
DATABASE_PATH = WEBSITE_ROOT / "school.db"
EVIDENCE_PATH = BUNDLE_ROOT / "evidence" / "functional-checks.json"
os.chdir(WEBSITE_ROOT)
sys.path.insert(0, str(WEBSITE_ROOT))

from app import app  # noqa: E402


checks = []


def check(name, condition, detail=""):
    passed = bool(condition)
    checks.append({"check": name, "passed": passed, "detail": detail})
    if not passed:
        raise AssertionError(f"{name}: {detail}")


def run_checks() -> None:
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        expected = {"users", "grades", "absences", "classes", "student_class", "risk_thresholds"}
        check("SQLite schema contains six application tables", expected.issubset(tables), str(sorted(tables)))
        student_count = connection.execute("SELECT COUNT(*) FROM users WHERE role='student'").fetchone()[0]
        grade_count = connection.execute("SELECT COUNT(*) FROM grades").fetchone()[0]
        absence_count = connection.execute("SELECT COUNT(*) FROM absences").fetchone()[0]
        check("Fictional demo students are present", student_count == 3, str(student_count))
        check("Demo grades are present", grade_count == 6, str(grade_count))
        check("Demo absences are present", absence_count == 6, str(absence_count))
    finally:
        connection.close()

    app.config.update(TESTING=True)
    client = app.test_client()
    response = client.get("/login")
    check("Login page loads", response.status_code == 200, str(response.status_code))
    response = client.get("/register")
    check("Student registration page loads", response.status_code == 200, str(response.status_code))

    response = client.post("/login", data={"email": "admin", "password": "admin"})
    check("Admin login redirects to dashboard", response.status_code == 302 and "/admin_dashboard" in response.location, response.location or "")
    response = client.get("/admin_dashboard")
    check("Admin dashboard loads", response.status_code == 200 and b"Alex Demo" in response.data, str(response.status_code))
    response = client.get("/analytics")
    check("Analytics dashboard loads", response.status_code == 200, str(response.status_code))
    response = client.get("/api/performance_evolution")
    check("Performance API returns JSON", response.status_code == 200 and response.is_json, str(response.status_code))
    response = client.get("/export_data?format=csv")
    check("CSV export works", response.status_code == 200 and b"Name,Email,Module" in response.data, response.content_type)
    response = client.get("/export_data?format=excel")
    check("Excel export works", response.status_code == 200 and response.data.startswith(b"PK"), response.content_type)
    response = client.get("/export_data?format=pdf")
    check("PDF export works", response.status_code == 200 and response.data.startswith(b"%PDF"), response.content_type)
    client.get("/logout")

    response = client.post(
        "/login",
        data={"email": "alex.demo@example.test", "password": "Student123!"},
    )
    check("Student login redirects to dashboard", response.status_code == 302 and "/student_dashboard" in response.location, response.location or "")
    response = client.get("/student_dashboard")
    check("Student dashboard loads personal grades", response.status_code == 200 and b"Mathematics" in response.data, str(response.status_code))
    response = client.get("/logout")
    check("Logout redirects to login", response.status_code == 302 and "/login" in response.location, response.location or "")

    evidence = {
        "status": "passed",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "passed": sum(item["passed"] for item in checks),
        "total": len(checks),
        "checks": checks,
    }
    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"passed: {evidence['passed']}/{evidence['total']} checks")


if __name__ == "__main__":
    run_checks()
