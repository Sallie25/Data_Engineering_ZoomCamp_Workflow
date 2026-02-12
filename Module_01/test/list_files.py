import os
from pathlib import Path

current_dir = Path.cwd()
# print(current_dir)

current_file = Path(__file__).name
# print(current_file)


print(f"Files in {current_dir} are: \n")

for filepath in current_dir.iterdir():
    if filepath.name == current_file:
        continue

    print(f"- {filepath.name}")

    """Read the entire contents of the file if the filepath is a file and not a directory"""
    if filepath.is_file():
        content = filepath.read_text(encoding='utf-8')
        print(f"     Content: {content}.")