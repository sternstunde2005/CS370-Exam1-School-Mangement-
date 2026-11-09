"""Run Part B, Part C and retained audit tests, persist machine-readable evidence, fail on errors."""
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import platform
import sys
import unittest
import warnings

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'website'))


class EvidenceResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.checks = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.checks.append({'test': test.id(), 'status': 'pass'})

    def addSubTest(self, test, subtest, error):
        super().addSubTest(test, subtest, error)
        self.checks.append({'test': str(subtest), 'status': 'pass' if error is None else 'fail'})


if __name__ == '__main__':
    warnings.filterwarnings('ignore', category=DeprecationWarning)
    suite = unittest.TestSuite()
    for pattern in ('test_authentication.py', 'test_permissions.py', 'test_audit_logger.py'):
        suite.addTests(unittest.defaultTestLoader.discover(str(root / 'website'), pattern=pattern))
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=EvidenceResult).run(suite)
    output = stream.getvalue()
    print(output)
    evidence = root / 'evidence'
    evidence.mkdir(exist_ok=True)
    (evidence / 'test-results.txt').write_text(output, encoding='utf-8')
    data = dict(timestamp_utc=datetime.now(timezone.utc).isoformat(), python=platform.python_version(),
                platform=platform.platform(), tests_run=result.testsRun, failures=len(result.failures),
                errors=len(result.errors), passed=result.wasSuccessful(), checks=result.checks,
                failure_details=[{'test': str(t), 'traceback': detail} for t, detail in result.failures + result.errors])
    (evidence / 'test-results.json').write_text(json.dumps(data, indent=2), encoding='utf-8')
    sys.exit(0 if result.wasSuccessful() else 1)
