import shutil
from pathlib import Path

DOCS_SOURCE_DIR = Path.cwd()  / "source"
print(DOCS_SOURCE_DIR)

folders = ["Python", "Data", "Utilities"]
for folder in folders:
    print(DOCS_SOURCE_DIR / folder)
    shutil.rmtree(DOCS_SOURCE_DIR/folder)

