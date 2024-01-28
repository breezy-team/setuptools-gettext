import os
import shutil
import subprocess
import tempfile

env = os.environ.copy()
env['PYTHONPATH'] = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..'))


def test_example_build():
    td = tempfile.mkdtemp()
    shutil.copytree("example", td + "/example")
    subprocess.check_call(
        ['python', 'setup.py', 'build_mo'],
        cwd=os.path.join(td, 'example'),
        env=env)


def test_example_install():
    td = tempfile.mkdtemp()
    shutil.copytree("example", td + "/example")
    root = tempfile.mkdtemp()
    subprocess.check_call(
        ['python', 'setup.py', 'install_mo', f'--root={root}'],
        cwd=os.path.join(td, 'example'),
        env=env)


def test_update_pot():
    td = tempfile.mkdtemp()
    shutil.copytree("example", td + "/example")
    p = os.path.join(td, 'example', 'hallowereld', 'example.py')
    with open(p, 'w') as f:
        f.write('print(_("Hello Example"))')
    subprocess.check_call(
        ['python', 'setup.py', 'update_pot'],
        cwd=os.path.join(td, 'example'),
        env=env)
    with open(os.path.join(td, 'example', 'po', 'hallowereld.pot')) as f:
        assert 'Hello Example' in f.read()
