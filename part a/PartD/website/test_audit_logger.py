
import unittest
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

import audit_logger


class TestAuditLogger(unittest.TestCase):

    def setUp(self):
        """Create a temporary database for each test."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(
            Path(self.temp_dir.name) / "test_audit.db"
        )

        self.db_patch = patch.object(
            audit_logger, "DB_PATH", self.db_path
        )
        self.db_patch.start()

    def tearDown(self):
        """Clean up after each test."""
        self.db_patch.stop()
        self.temp_dir.cleanup()

    def test_table_creation(self):
        """The audit_logs table should be created."""
        audit_logger.init_audit_table()

        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute("""
                SELECT name FROM sqlite_master
                WHERE type = 'table' AND name = 'audit_logs'
            """).fetchone()

        self.assertIsNotNone(result)

    def test_successful_event(self):
        """A successful security event should be saved."""
        audit_logger.log_event(
            "admin",
            "LOGIN",
            True,
            "Administrator login successful"
        )

        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute("""
                SELECT user_id, action, success, details
                FROM audit_logs
            """).fetchone()

        self.assertEqual(
            result,
            (
                "admin",
                "LOGIN",
                1,
                "Administrator login successful"
            )
        )

    def test_failed_event(self):
        """A failed event should have success = 0."""
        audit_logger.log_event(
            "student01",
            "UNAUTHORIZED_ACCESS",
            False,
            "Admin page access denied"
        )

        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute("""
                SELECT user_id, action, success
                FROM audit_logs
            """).fetchone()

        self.assertEqual(
            result,
            ("student01", "UNAUTHORIZED_ACCESS", 0)
        )


if __name__ == "__main__":
    unittest.main()
