from __future__ import print_function
import fileinput
import asyncio

asyncLib = asyncio.__file__
lineNum = 0

# This script is used to address an issue on Windows with asyncio in the Tornado web server.
# See links below for more information
# https://github.com/tornadoweb/tornado/issues/2608
# https://www.tornadoweb.org/en/stable/releases/v6.0.4.html#general-changes
# https://bugs.python.org/issue37373

with open(asyncLib, 'r+') as origLib:
    lines = origLib.readlines()
    for line in lines:
        lineNum += 1
        if line.startswith('import sys'):
            print('Found 1.')
            print(line, end='')
            importLine = lineNum
        elif line.startswith('    from .windows_events import'):
            print('Found 2.')
            print(line, end='')
            asyncLine = lineNum

if importLine is not None and asyncLine is not None:
    origLib = fileinput.input(asyncLib, inplace = True)
    for n, line in enumerate(origLib, start=1):
        if n == importLine:
            print('import asyncio')
        if n == asyncLine + 1:
            print('    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())')
        print(line, end='')