import pathlib

f = pathlib.Path("app/routers/wizard.py")
t = f.read_text(encoding="utf-8")

# Fix 1: Path(file) -> Path(__file__)
t = t.replace("Path(file).resolve()", "Path(__file__).resolve()")

# Fix 2: Add _HERE shorthand to avoid repeating __file__
old_generated = 'GENERATED_DIR = Path(__file__).resolve().parent.parent.parent / "generated"'
old_script = 'GENERATE_SCRIPT = Path(__file__).resolve().parent.parent.parent / "scripts" / "generate_project.py"'
t = t.replace(old_generated, '_HERE = Path(__file__).resolve().parent.parent.parent\nGENERATED_DIR = _HERE / "generated"')
t = t.replace(old_script, 'GENERATE_SCRIPT = _HERE / "scripts" / "generate_project.py"')

# Fix 3: python3 -> python (Windows)
t = t.replace('"python3",', '"python",')

# Fix 4: --output-dir -> --output
t = t.replace('"--output-dir",', '"--output",')

f.write_text(t, encoding="utf-8")
print("Fixed wizard.py imports and paths")

# Now check what the cmd array looks like
lines = f.read_text().split('\n')
for i, l in enumerate(lines):
    if '--name' in l or '--tagline' in l or '--color' in l or '--pages' in l or '--deps' in l or '--no-auth' in l or '--no-db' in l or '--scope' in l:
        print(f"  Line {i+1}: {l}")
