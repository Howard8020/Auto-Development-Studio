import pathlib

f = pathlib.Path("scripts/generate_project.py")
t = f.read_text(encoding="utf-8")

if "SCOPE.md" in t:
    print("SKIP: already has SCOPE.md")
else:
    # Also fix field name reads to accept both old and new names
    t = t.replace(
        'name = input_data.get("project_name", "my-app")',
        'name = input_data.get("project_name") or input_data.get("name", "my-app")'
    )
    t = t.replace(
        'color = input_data.get("brand_color", "#ff6600")',
        'color = input_data.get("brand_color") or input_data.get("color", "#ff6600")'
    )

    # Insert scope writing before ZIP section
    marker = "    # ___ ZIP it ___"
    scope_block = '''    # ___ Write scope to SCOPE.md ___
    scope_text = input_data.get("scope", "")
    if scope_text:
        scope_path = out / "SCOPE.md"
        scope_md = "# Project Scope\\n\\n" + scope_text + "\\n"
        scope_path.write_text(scope_md, encoding="utf-8")
        print(f"  Wrote SCOPE.md ({len(scope_text)} chars)")

'''
    if marker in t:
        t = t.replace(marker, scope_block + marker)
        f.write_text(t, encoding="utf-8")
        print("PATCHED: generator - added SCOPE.md output + field aliases")
    else:
        print("FAILED: could not find ZIP marker")

    import ast
    try:
        ast.parse(f.read_text(encoding="utf-8"))
        print("SYNTAX OK")
    except SyntaxError as e:
        print(f"ERROR line {e.lineno}: {e.msg}")
