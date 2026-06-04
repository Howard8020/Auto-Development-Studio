from pathlib import Path
p = Path('app/main.py')
lines = p.read_text(encoding='utf-8').splitlines()
lines = [l for l in lines if 'wizard._init_templates' not in l]
p.write_text('\n'.join(lines) + '\n', encoding='utf-8')
print("Removed wizard._init_templates line")
