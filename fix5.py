import pathlib

f = pathlib.Path("app/routers/wizard.py")
t = f.read_text(encoding="utf-8")

old = '''    input_data = {
        "name": name,
        "tagline": tagline,
        "color": color,
        "with_auth": with_auth,
        "with_db": with_db,
        "pages": pages,
        "deps": deps,
        "scope": scope,
    }'''

new = '''    # Remap field names to match generate_project.py expectations
    input_data = {
        "project_name": name,
        "tagline": tagline,
        "brand_color": color,
        "use_auth": "yes" if with_auth else "no",
        "use_db": "yes" if with_db else "no",
        "pages": pages,
        "models": deps,
        "scope": scope,
    }'''

if old in t:
    t = t.replace(old, new)
    f.write_text(t, encoding="utf-8")
    print("PATCHED: wizard input_data field mapping")
else:
    print("COULD NOT find old block. Searching...")
    for i, l in enumerate(t.split(chr(10))):
        if "input_data" in l and i > 120:
            print(f"  {i+1}: {l}")

import ast
try:
    ast.parse(f.read_text(encoding="utf-8"))
    print("SYNTAX OK")
except SyntaxError as e:
    print(f"ERROR: {e}")
