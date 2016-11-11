import json
import os
import subprocess
import sys
import requests
import tarfile
import tempfile
from .board import MicropythonBoards


def install_package(package_name):
    package_info = package_name.split('=')
    package_version = None
    package_name = package_info[0]
    if len(package_info) == 2:
        package_version = package_info[-1]
    url = 'https://pypi.python.org/pypi/{package}/json'.format(package=package_name)
    response = requests.get(url)
    package = response.json()
    if not package_version:
        package_version = package['info']['version']
    url = package['releases'][package_version]['url']
    with tempfile.TemporaryDirectory() as tempdir:
        response = requests.get(url)
        with open(os.path.basename(url), 'wb') as file_handle:
            file_handle.write(response.content)
        tar = tarfile.open(os.path.basename(url))
        tar.extractall()
        tar.close()

        for root, dirs, files in os.walk('.'):
            for name in files:
                filename = os.path.join(root, name)
                if filename.endswith('.py'):
                    if filename.startswith('./'):
                        filename = filename[2:]
                        dest = os.path.join('lib', filename)
                        print(filename)
                        # MicropythonBoards().upload(filename=filename, dest=dest, range=range)


def install_package_pip(package_name):
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