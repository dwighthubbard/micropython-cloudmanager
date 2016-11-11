import os
import subprocess
import sys
import tempfile
from .board import MicropythonBoards


def install_package(package_name):
    with tempfile.TemporaryDirectory() as tempdir:
        os.chdir(tempdir)
        command = 'pip install --system --target="{tempdir}" {package}'.format(executable=sys.executable, tempdir=tempdir, package=package_name)
        print(command)
        os.system(command)
        # directory = 'lib/{0}/site-packages'.format(os.path.basename(sys.executable))
        for root, dirs, files in os.walk('.'):
            for name in files:
                filename = os.path.join(root, name)
                if filename.endswith('.py'):
                    if filename.startswith('./'):
                        filename = filename[2:]
                        dest = os.path.join('lib', filename)
                        print(filename)
                        MicropythonBoards().upload(filename=filename, dest=dest, range=range)


if __name__ == '__main__':
    install_package('hostlists')