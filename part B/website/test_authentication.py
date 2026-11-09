"""Integration tests with real Argon2id, SQLite and enabled CSRF."""
from contextlib import closing, redirect_stdout
import hashlib
import io
from pathlib import Path
import sqlite3
import tempfile
import unittest
from app import app, init_db
from security_b import hash_password, verify_password

class AuthenticationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stored = hash_password('DemoPass123!')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.original = dict(app.config)
        self.addCleanup(self.restore)
        app.config.update(TESTING=True, SECRET_KEY='test-only-key', DATABASE=str(Path(self.temp.name)/'test.db'))
        with redirect_stdout(io.StringIO()):
            init_db()
        for uid, role in [(1, 'student'), (2, 'faculty')]:
            self.sql('INSERT INTO users VALUES (?, ?, ?, ?, ?)', (uid, role, role+'@example.test', self.stored, role))
        self.client = app.test_client()

    def restore(self):
        app.config.clear()
        app.config.update(self.original)

    def sql(self, query, params=()):
        with closing(sqlite3.connect(app.config['DATABASE'])) as conn, conn:
            return conn.execute(query, params).fetchall()

    def post(self, path, data=None, client=None):
        c = client or self.client
        c.get('/login')
        with c.session_transaction() as sess:
            token = sess['_csrf_token']
        return c.post(path, data={'csrf_token': token, **(data or {})})

    def login(self, password='DemoPass123!', username='student@example.test', client=None):
        return self.post('/login', {'email':username, 'password':password}, client)

    def test_student_and_faculty_login(self):
        for role in ['student', 'faculty']:
            c = app.test_client()
            r = self.login(username=role+'@example.test', client=c)
            self.assertEqual(r.status_code, 302)
            self.assertTrue(r.location.endswith('/'+role+'_dashboard'))
            self.assertEqual(c.get(r.location).status_code, 200)

    def test_salted_argon2id_storage(self):
        a, b = hash_password('same password'), hash_password('same password')
        self.assertTrue(a.startswith('$argon2id$'))
        self.assertNotEqual(a, b)
        self.assertTrue(verify_password(a, 'same password'))
        self.assertFalse(verify_password(a, 'wrong'))
        self.assertFalse(verify_password('corrupt', 'anything'))

    def test_incorrect_unknown_and_sql_injection_credentials(self):
        for username in ['student@example.test', 'missing@example.test', "' OR 1=1 --"]:
            r = self.login('wrong', username)
            self.assertEqual(r.status_code, 401)
            self.assertIn(b'Invalid username or password', r.data)
        self.assertEqual(self.client.get('/student_dashboard').status_code, 401)

    def test_account_lock_survives_new_client_and_initialization(self):
        for i in range(5):
            self.assertEqual(self.login('wrong').status_code, 429 if i == 4 else 401)
        with redirect_stdout(io.StringIO()):
            init_db()
        self.assertEqual(self.login(client=app.test_client()).status_code, 429)

    def test_expired_lock_allows_login(self):
        for _ in range(5): self.login('wrong')
        self.sql('UPDATE login_limits SET until = 0')
        self.assertEqual(self.login().status_code, 302)

    def test_success_resets_account_failures(self):
        for _ in range(4): self.login('wrong')
        self.assertEqual(self.login().status_code, 302)
        self.post('/logout')
        self.assertEqual(self.login('wrong').status_code, 401)
        self.assertEqual(self.sql("SELECT failures FROM login_limits WHERE key LIKE 'account:%'")[0][0], 1)

    def test_ip_limits_rotating_usernames(self):
        app.config['AUTH_IP_LIMIT'] = 3
        for i in range(3):
            self.assertEqual(self.login('wrong', f'missing{i}').status_code, 429 if i == 2 else 401)
        self.assertEqual(self.login().status_code, 429)

    def test_protected_resources_require_login(self):
        for path in ['/student_dashboard','/faculty_dashboard','/admin_dashboard','/analytics','/export_data','/api/student_risk/1','/api/performance_evolution','/api/student_records/1']:
            with self.subTest(path=path): self.assertEqual(self.client.get(path).status_code, 401)
        self.assertEqual(self.client.post('/faculty_dashboard').status_code, 401)

    def test_logout_revokes_copied_cookie(self):
        self.login()
        copied = self.client.get_cookie('session').value
        self.assertEqual(self.post('/logout').status_code, 302)
        self.assertEqual(self.client.get('/student_dashboard').status_code, 401)
        c = app.test_client()
        c.set_cookie('session', copied)
        self.assertEqual(c.get('/student_dashboard').status_code, 401)
        self.assertEqual(self.sql('SELECT * FROM auth_sessions'), [])

    def test_expired_session_is_rejected(self):
        self.login()
        self.sql('UPDATE auth_sessions SET expires = 0')
        self.assertEqual(self.client.get('/student_dashboard').status_code, 401)

    def test_password_change_invalidates_session(self):
        self.login()
        self.sql('UPDATE users SET password = ? WHERE id = 1', (hash_password('NewPassword123!'),))
        self.assertEqual(self.client.get('/student_dashboard').status_code, 401)

    def test_old_cookie_without_server_session_rejected(self):
        with self.client.session_transaction() as sess: sess.update(user_id=1, role='student')
        self.assertEqual(self.client.get('/student_dashboard').status_code, 401)

    def test_login_rotates_session_and_csrf(self):
        self.login()
        self.client.get('/login')
        with self.client.session_transaction() as sess: old_token, old_csrf = sess['auth_token'], sess['_csrf_token']
        copied = self.client.get_cookie('session').value
        self.login()
        self.client.get('/login')
        with self.client.session_transaction() as sess:
            self.assertNotEqual(sess['auth_token'], old_token)
            self.assertNotEqual(sess['_csrf_token'], old_csrf)
        c = app.test_client()
        c.set_cookie('session', copied)
        self.assertEqual(c.get('/student_dashboard').status_code, 401)

    def test_csrf_and_post_only_logout(self):
        self.assertEqual(self.client.post('/login', data={'email':'student@example.test','password':'DemoPass123!'}).status_code, 400)
        self.login()
        self.assertEqual(self.client.get('/logout').status_code, 405)
        self.assertEqual(self.client.post('/logout').status_code, 400)
        self.assertEqual(self.client.get('/student_dashboard').status_code, 200)

    def test_legacy_hash_upgraded_only_on_success(self):
        old = hashlib.sha256(b'DemoPass123!').hexdigest()
        self.sql('UPDATE users SET password = ? WHERE id = 1', (old,))
        self.assertEqual(self.login('wrong').status_code, 401)
        self.assertEqual(self.sql('SELECT password FROM users WHERE id = 1')[0][0], old)
        self.assertEqual(self.login().status_code, 302)
        stored = self.sql('SELECT password FROM users WHERE id = 1')[0][0]
        self.assertTrue(stored.startswith('$argon2id$'))
        self.assertTrue(verify_password(stored, 'DemoPass123!'))

    def test_registration_argon2_and_student_role(self):
        data = dict(name='New User', email='new@example.test', password='NewPassword123!', role='faculty')
        self.assertEqual(self.post('/register', data).status_code, 302)
        row = self.sql('SELECT password, role FROM users WHERE email = ?', (data['email'],))[0]
        self.assertTrue(verify_password(row[0], data['password']))
        self.assertTrue(row[0].startswith('$argon2id$'))
        self.assertEqual(row[1], 'student')
        data.update(email='weak@example.test', password='short')
        self.assertEqual(self.post('/register', data).status_code, 400)

    def test_cookies_cache_and_audit_without_secrets(self):
        self.login('wrong')
        r = self.login()
        self.assertIn('HttpOnly', r.headers['Set-Cookie'])
        self.assertIn('SameSite=Lax', r.headers['Set-Cookie'])
        self.assertEqual(self.client.get('/student_dashboard').headers['Cache-Control'], 'no-store')
        self.post('/logout')
        rows = self.sql('SELECT action, success, details FROM audit_logs')
        self.assertIn(('LOGIN', 0, 'Invalid login credentials'), rows)
        self.assertIn(('LOGIN', 1, 'student login successful'), rows)
        self.assertTrue(any(r[0]=='LOGOUT' for r in rows))
        self.assertNotIn('DemoPass123!', str(rows))
        self.assertNotIn('$argon2id$', str(rows))

    def test_missing_or_oversized_login_rejected(self):
        for data in [{}, {'email':'x','password':'a'*1025}]:
            self.assertEqual(self.post('/login', data).status_code, 401)

if __name__ == '__main__': unittest.main(verbosity=2)
