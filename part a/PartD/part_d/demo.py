import argparse
import os
from pathlib import Path
import shutil
import sys
import tempfile

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('mode', choices=['before', 'after'])
args = parser.parse_args()
with tempfile.TemporaryDirectory(prefix='part-d-demo-') as temporary:
    shutil.copytree(root/'website', temporary, dirs_exist_ok=True)
    if args.mode == 'before':
        shutil.copyfile(root/'part_d/baseline/app.py.txt', Path(temporary)/'app.py')
        shutil.copytree(root/'part_d/baseline/templates', Path(temporary)/'templates', dirs_exist_ok=True)
    os.chdir(temporary)
    sys.path.insert(0, temporary)
    from app import app
    print('PART D '+args.mode.upper()+' -- disposable database, http://127.0.0.1:5001', flush=True)
    app.run(host='127.0.0.1', port=5001, debug=False, use_reloader=False)
