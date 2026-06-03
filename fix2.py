import pathlib

f = pathlib.Path("app/routers/wizard.py")
lines = f.read_text(encoding="utf-8").split("\n")

# Find line "    # Build command"
start = None
end = None
for i, l in enumerate(lines):
    if "# Build command" in l and i > 120:
        start = i
    if start and "    if not with_db:" in l:
        end = i + 2  # include the cmd.append("--no-db") line
        break

if start is None or end is None:
    print(f"FAILED: start={start}, end={end}")
else:
    new_block = [
        "    # Build JSON input for generator",
        "    input_data = {",
        '        "name": name,',
        '        "tagline": tagline,',
        '        "color": color,',
        '        "with_auth": with_auth,',
        '        "with_db": with_db,',
        '        "pages": pages,',
        '        "deps": deps,',
        '        "scope": scope,',
        "    }",
        '    safe_name = name.replace(" ", "_").lower()',
        '    input_path = GENERATED_DIR / f"_input_{safe_name}.json"',
        "    input_path.write_text(json.dumps(input_data, indent=2))",
        "",
        "    cmd = [",
        '        "python", str(GENERATE_SCRIPT),',
        '        "--input", str(input_path),',
        '        "--output", str(GENERATED_DIR),',
        "    ]",
    ]

    lines = lines[:start] + new_block + lines[end:]
    f.write_text("\n".join(lines), encoding="utf-8")
    print(f"Replaced lines {start+1}-{end+1} with JSON input approach")

    # Also add input_path cleanup after subprocess result
    t = f.read_text(encoding="utf-8")
    if "input_path.unlink" not in t:
        t = t.replace(
            "        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)",
            "        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)\n        input_path.unlink(missing_ok=True)",
        )
        f.write_text(t, encoding="utf-8")
        print("Added input_path cleanup")

# Validate
import ast
try:
    ast.parse(f.read_text(encoding="utf-8"))
    print("SYNTAX OK")
except SyntaxError as e:
    print(f"SYNTAX ERROR: {e}")
