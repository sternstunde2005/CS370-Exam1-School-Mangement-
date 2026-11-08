import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]


def worker(mode):
    sys.path.insert(0, os.getcwd())
    from app import app
    app.config['TESTING'] = True
    fixed = mode == 'after'
    results = []
    with sqlite3.connect('school.db') as db:
        student = db.execute("SELECT id FROM users WHERE role='student' ORDER BY id").fetchone()[0]

    def record(label, passed, observed):
        results.append(dict(test=label, passed=bool(passed), observed=observed))

    def token(client, path='/login'):
        page = client.get(path).get_data(as_text=True)
        match = re.search(r'name="csrf_token" value="([^"]+)"', page)
        return match.group(1) if match else ''

    def login():
        client = app.test_client()
        response = client.post('/login', data=dict(email='admin', password='admin', csrf_token=token(client)))
        assert response.status_code == 302
        return client

    def snapshot():
        with sqlite3.connect('school.db') as db:
            return [db.execute('SELECT * FROM '+table+' ORDER BY id').fetchall() for table in ('grades', 'absences')]

    client = login()
    good = dict(student_id=str(student), module_name='Part D Test', grade='15', absences='2', teacher_name='Demo Teacher', academic_year='2024-2025', semester='1')
    current_token = token(client, '/admin_dashboard')
    for label, value in [('missing', None), ('incorrect', 'wrong'), ('other session', token(app.test_client()))]:
        data = dict(good)
        data['module_name'] += label
        if value is not None:
            data['csrf_token'] = value
        before = snapshot()
        response = client.post('/admin_dashboard', data=data, headers={'Origin':'http://127.0.0.1:8001'})
        changed = snapshot() != before
        record('CSRF '+label, (response.status_code == 400 and not changed) if fixed else (response.status_code == 302 and changed), dict(status=response.status_code, database_changed=changed))

    cases = [('grade', '99'), ('grade', '-1'), ('grade', 'nan'), ('grade', 'inf'), ('grade', 'abc'), ('absences', '-5'), ('absences', '1.5'), ('student_id', '999999999'), ('module_name', ''), ('module_name', 'x'*101), ('teacher_name','x'*101), ('academic_year', '2024-2030'), ('semester','3')]
    for field, value in cases:
        data = dict(good, csrf_token=current_token)
        data[field] = value
        before = snapshot()
        try:
            response = client.post('/admin_dashboard', data=data)
            status = response.status_code
        except (ValueError, sqlite3.Error) as error:
            status = type(error).__name__
        changed = snapshot() != before
        passed = status == 400 and not changed if fixed else True
        record('Validation '+field+'='+repr(value), passed, dict(status=status, database_changed=changed))

    for grade in ['0', '20', '15.5']:
        data = dict(good, grade=grade, csrf_token=current_token)
        response = client.post('/admin_dashboard', data=data)
        with sqlite3.connect('school.db') as db:
            stored = db.execute('SELECT grade FROM grades WHERE student_id=? AND module_name=?',(student, good['module_name'])).fetchone()[0]
        record('Valid grade '+grade, response.status_code == 302 and stored == float(grade), dict(status=response.status_code, stored_grade=stored))
    for path in ['/admin_dashboard','/analytics','/api/performance_evolution','/export_data?format=csv','/export_data?format=excel','/export_data?format=pdf'] if fixed else []:
        response = client.get(path)
        record('Regression '+path,response.status_code==200, response.status_code)
    if fixed:
        response = client.get('/logout')
        record('GET logout refused', response.status_code==405, response.status_code)
        response = client.post('/logout',data={'csrf_token':current_token})
        with client.session_transaction() as sess:
            cleared = 'user_id' not in sess
        record('POST logout succeeds',response.status_code==302 and cleared,response.status_code)
        response = client.post('/login',data=dict(email='admin',password='admin',csrf_token=current_token))
        record('Stale token refused',response.status_code==400,response.status_code)
        student_client=app.test_client()
        response=student_client.post('/login',data=dict(email='alex.demo@example.test',password='Student123!',csrf_token=token(student_client)), follow_redirects=True)
        record('Student login and dashboard',response.status_code==200 and b'Alex' in response.data,response.status_code)
        new=app.test_client()
        response=new.post('/register',data=dict(name='D Test',email='d-test@example.test',password='Demo123!',csrf_token=token(new,'/register')))
        record('Registration form works',response.status_code==302,response.status_code)
    print(json.dumps(results))


def main():
    report = {'executed_at': datetime.now(timezone.utc).isoformat(), 'method':'Flask test client, isolated copies of supplied fictional database', 'results':{}}
    for mode in ['before','after']:
        with tempfile.TemporaryDirectory(prefix='part-d-') as temporary:
            shutil.copytree(ROOT/'website', temporary, dirs_exist_ok=True)
            if mode == 'before':
                shutil.copyfile(ROOT/'part_d/baseline/app.py.txt', Path(temporary)/'app.py')
                shutil.copytree(ROOT/'part_d/baseline/templates', Path(temporary)/'templates', dirs_exist_ok=True)
            result = subprocess.run([sys.executable, str(Path(__file__).resolve()), '--worker', mode],cwd=temporary,text=True,capture_output=True)
            if result.returncode:
                raise RuntimeError(result.stderr)
            report['results'][mode]=json.loads(result.stdout)
    destination=ROOT/'part_d/test-results.json'
    destination.write_text(json.dumps(report,indent=2),encoding='utf-8')
    for mode, rows in report['results'].items():
        print('\n'+mode.upper())
        for row in rows:
            print(('PASS ' if row['passed'] else 'FAIL ')+row['test']+' '+json.dumps(row['observed']))
    print('\nBefore validation rows are observations, not assertions of secure behavior.')
    print('Saved '+str(destination))
    assert all(row['passed'] for rows in report['results'].values() for row in rows)


if __name__ == '__main__':
    if '--worker' in sys.argv:
        worker(sys.argv[-1])
    else:
        main()
