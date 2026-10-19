from pathlib import Path
import os
import sqlite3
import sys


BUNDLE_ROOT = Path(__file__).resolve().parents[1]
WEBSITE_ROOT = BUNDLE_ROOT / "website"
DATABASE_PATH = WEBSITE_ROOT / "school.db"
os.chdir(WEBSITE_ROOT)
sys.path.insert(0, str(WEBSITE_ROOT))

from app import hash_password, init_db  # noqa: E402


STUDENTS = [
    ("Alex Demo", "alex.demo@example.test", "Student123!"),
    ("Morgan Example", "morgan.example@example.test", "Student123!"),
    ("Jamie Sample", "jamie.sample@example.test", "Student123!"),
]

GRADES = {
    "alex.demo@example.test": [("Mathematics", 15.5, "Dr. Taylor"), ("Databases", 13.0, "Dr. Rivera")],
    "morgan.example@example.test": [("Mathematics", 9.0, "Dr. Taylor"), ("Databases", 11.5, "Dr. Rivera")],
    "jamie.sample@example.test": [("Mathematics", 17.0, "Dr. Taylor"), ("Databases", 16.0, "Dr. Rivera")],
}

ABSENCES = {
    "alex.demo@example.test": [("Mathematics", 2, 4), ("Databases", 1, 2)],
    "morgan.example@example.test": [("Mathematics", 12, 24), ("Databases", 8, 16)],
    "jamie.sample@example.test": [("Mathematics", 0, 0), ("Databases", 1, 2)],
}


def seed() -> None:
    init_db()
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        cursor = connection.cursor()
        for name, email, password in STUDENTS:
            cursor.execute(
                "INSERT OR IGNORE INTO users (name, email, password, role) VALUES (?, ?, ?, 'student')",
                (name, email, hash_password(password)),
            )

        cursor.execute(
            "SELECT id FROM classes WHERE name = ? AND academic_year = ? AND teacher_name = ?",
            ("Computer Science 101", "2024-2025", "Dr. Taylor"),
        )
        class_row = cursor.fetchone()
        if class_row is None:
            cursor.execute(
                "INSERT INTO classes (name, academic_year, teacher_name) VALUES (?, ?, ?)",
                ("Computer Science 101", "2024-2025", "Dr. Taylor"),
            )
            class_id = cursor.lastrowid
        else:
            class_id = class_row[0]

        for _, email, _ in STUDENTS:
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            student_id = cursor.fetchone()[0]
            cursor.execute(
                "SELECT 1 FROM student_class WHERE student_id = ? AND class_id = ?",
                (student_id, class_id),
            )
            if cursor.fetchone() is None:
                cursor.execute(
                    "INSERT INTO student_class (student_id, class_id) VALUES (?, ?)",
                    (student_id, class_id),
                )

            for module, grade, teacher in GRADES[email]:
                cursor.execute(
                    "SELECT 1 FROM grades WHERE student_id = ? AND module_name = ? AND academic_year = ? AND semester = ?",
                    (student_id, module, "2024-2025", "1"),
                )
                if cursor.fetchone() is None:
                    cursor.execute(
                        "INSERT INTO grades (student_id, module_name, grade, teacher_name, academic_year, semester) VALUES (?, ?, ?, ?, ?, ?)",
                        (student_id, module, grade, teacher, "2024-2025", "1"),
                    )

            for module, count, hours in ABSENCES[email]:
                cursor.execute(
                    "SELECT 1 FROM absences WHERE student_id = ? AND module_name = ? AND academic_year = ? AND semester = ?",
                    (student_id, module, "2024-2025", "1"),
                )
                if cursor.fetchone() is None:
                    cursor.execute(
                        "INSERT INTO absences (student_id, module_name, count, total_hours, academic_year, semester) VALUES (?, ?, ?, ?, ?, ?)",
                        (student_id, module, count, hours, "2024-2025", "1"),
                    )

        connection.commit()
        counts = {}
        for table in ("users", "grades", "absences", "classes", "student_class", "risk_thresholds"):
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            counts[table] = cursor.fetchone()[0]
        print("Demo database ready:", ", ".join(f"{name}={count}" for name, count in counts.items()))
    finally:
        connection.close()


if __name__ == "__main__":
    seed()
