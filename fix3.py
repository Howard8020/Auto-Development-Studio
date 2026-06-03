import pathlib
f = pathlib.Path("app/routers/wizard.py")
t = f.read_text(encoding="utf-8")

# Fix line 66: scope_text = file_text needs 20 spaces indent
t = t.replace("\nscope_text = file_text\n", "\n                    scope_text = file_text\n")

f.write_text(t, encoding="utf-8")

import ast
try:
    ast.parse(f.read_text(encoding="utf-8"))
    print("SYNTAX OK")
except SyntaxError as e:
    print(f"ERROR: {e}")
