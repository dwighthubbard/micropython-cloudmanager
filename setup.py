import sys
# Remove current dir from sys.path, otherwise setuptools will peek up our
# module instead of system.
sys.path.pop(0)
from setuptools import setup


setup(
    name='micropython-cloudmanager',
    description='Micropython client that allows network attached boards to be controlled from a central redis server',
    long_description=open('README.rst').read(),
    url='https://github.com/dhubbard/micropython-cloudmanager',
    author='Dwight Hubbard',
    author_email="dwight@dwighthubbard.com",
    install_requires=[
        'python_version>="3.6"',
        'hostlists',
        'redislite',
        'python-daemon',
        'pip>=8.1.2',
        'netifaces',
        'watchdog',
        'requests'
    ],
    license='MIT',
    maintainer='Dwight Hubbard',
    maintainer_email='dwight@dwighthubbard.com',
    packages=['cloudmanager'],
    scripts=['scripts/micropython_board_manager', 'scripts/mbm', 'scripts/mbm_sync'],
    version='0.0.165',
    zip_safe=True,
)
