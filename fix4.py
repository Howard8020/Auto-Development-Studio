import pathlib
f = pathlib.Path("app/routers/wizard.py")
t = f.read_text(encoding="utf-8")

# Fix line 190
t = t.replace("\nfor root, _, files in os.walk(project_dir):\n", "\n        for root, _, files in os.walk(project_dir):\n")

f.write_text(t, encoding="utf-8")

import ast
try:
    ast.parse(f.read_text(encoding="utf-8"))
    print("SYNTAX OK - wizard.py is clean")
except SyntaxError as e:
    print(f"ERROR at line {e.lineno}: {e.msg}")
