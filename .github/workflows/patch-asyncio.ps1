$fileName = 'c:\hostedtoolcache\windows\python\3.8.5\x64\lib\asyncio\__init__.py'
(Get-Content $fileName) -replace "from .windows_events import \*", "$&`n    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())" | Set-Content $fileName
(Get-Content $fileName) -replace "import sys", "$&`nimport asyncio" | Set-Content $fileName