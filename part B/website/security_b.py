"""Part B: Argon2id, persistent login throttling, revocable sessions."""
from contextlib import contextmanager
from datetime import timedelta
import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import time

from argon2 import PasswordHasher, Type
from argon2.exceptions import VerificationError, InvalidHashError
from flask import current_app, request, session

PH = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4, type=Type.ID)
DUMMY_HASH = PH.hash(secrets.token_urlsafe(32))


def hash_password(password):
    return PH.hash(password)


def verify_password(stored, password):
    try:
        return PH.verify(stored, password)
    except (VerificationError, InvalidHashError):
        return False


@contextmanager
def database():
    conn = sqlite3.connect(current_app.config['DATABASE'], timeout=15)
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def init_auth_tables(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS login_limits (
        key TEXT PRIMARY KEY, failures INTEGER NOT NULL, until REAL NOT NULL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS auth_sessions (
        token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL,
        password_hash TEXT NOT NULL, expires REAL NOT NULL)''')


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def revoke_session():
    token = session.get('auth_token')
    if isinstance(token, str):
        with database() as conn:
            conn.execute('DELETE FROM auth_sessions WHERE token_hash = ?', (digest(token),))
    session.clear()


def authenticate(username, password):
    """Reserve failures under an SQLite write lock, shared across workers/restarts.

    Five failures per account or 30 per source address within 15 minutes.
    Address comes from the socket, never a client-supplied forwarded header.
    """
    now = time.time()
    window = current_app.config['AUTH_LOCK_SECONDS']
    account_key = 'account:' + digest(username)
    ip_key = 'ip:' + digest(request.remote_addr or 'unknown')
    keys = [(account_key, current_app.config['AUTH_ACCOUNT_LIMIT']),
            (ip_key, current_app.config['AUTH_IP_LIMIT'])]
    with database() as conn:
        conn.execute('BEGIN IMMEDIATE')
        conn.execute('DELETE FROM login_limits WHERE until <= ?', (now,))
        conn.execute('DELETE FROM auth_sessions WHERE expires <= ?', (now,))
        for key, limit in keys:
            state = conn.execute('SELECT failures FROM login_limits WHERE key = ?', (key,)).fetchone()
            if state and state[0] >= limit:
                return None, True
        user = conn.execute('SELECT id, name, password, role FROM users WHERE email = ?',
                            (username,)).fetchone()
        stored = user[2] if user else DUMMY_HASH
        legacy = bool(re.fullmatch(r'[0-9a-f]{64}', stored))
        valid = verify_password(DUMMY_HASH if legacy else stored, password)
        if legacy:
            valid = hmac.compare_digest(stored, digest(password))
        if user and valid and user[3] in {'student', 'faculty', 'admin'}:
            # Upgrade legacy SHA-256 only after proving knowledge of the password.
            if legacy or PH.check_needs_rehash(stored):
                stored = hash_password(password)
                conn.execute('UPDATE users SET password = ? WHERE id = ?', (stored, user[0]))
            conn.execute('DELETE FROM login_limits WHERE key = ?', (account_key,))
            # Do not reset IP failures by logging into an attacker's own account.
            old = session.get('auth_token')
            if isinstance(old, str):
                conn.execute('DELETE FROM auth_sessions WHERE token_hash = ?', (digest(old),))
            token = secrets.token_urlsafe(32)
            conn.execute('INSERT INTO auth_sessions VALUES (?, ?, ?, ?)',
                         (digest(token), user[0], stored, now + current_app.config['AUTH_SESSION_SECONDS']))
            session.clear()
            session.permanent = True
            session.update(user_id=user[0], role=user[3], name=user[1], auth_token=token)
            return user, False
        locked = False
        for key, limit in keys:
            conn.execute('''INSERT INTO login_limits VALUES (?, 1, ?)
                ON CONFLICT(key) DO UPDATE SET failures = failures + 1''', (key, now + window))
            failures = conn.execute('SELECT failures FROM login_limits WHERE key = ?', (key,)).fetchone()[0]
            locked |= failures >= limit
        return None, locked


def install_auth(app):
    app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax',
                      SESSION_COOKIE_SECURE=os.environ.get('COOKIE_SECURE') == '1',
                      PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
                      SESSION_REFRESH_EACH_REQUEST=False,
                      AUTH_SESSION_SECONDS=1800, AUTH_ACCOUNT_LIMIT=5,
                      AUTH_IP_LIMIT=30, AUTH_LOCK_SECONDS=900,
                      MAX_CONTENT_LENGTH=1024 * 1024)

    # Must precede Part C's load_identity and role enforcement.
    @app.before_request
    def validate_session():
        if 'user_id' not in session:
            return
        token = session.get('auth_token')
        if not isinstance(token, str):
            session.clear()
            return
        with database() as conn:
            row = conn.execute('''SELECT s.user_id FROM auth_sessions s JOIN users u
                ON u.id = s.user_id WHERE s.token_hash = ? AND s.expires > ?
                AND s.password_hash = u.password''', (digest(token), time.time())).fetchone()
        if row is None or row[0] != session.get('user_id'):
            session.clear()

    @app.after_request
    def prevent_cached_private_pages(response):
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Pragma'] = 'no-cache'
        return response
