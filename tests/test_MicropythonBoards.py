#!/usr/bin/env python
from __future__ import print_function
import sys
sys.path.insert(0, '.')
from cloudmanager.board import MicropythonBoards


for result in MicropythonBoards().execute("import os;print(os.uname())"):
    print(result.read().strip())
