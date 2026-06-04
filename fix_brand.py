from pathlib import Path
p = Path('app/routers/brand_studio.py')
c = p.read_text(encoding='utf-8')
fence = chr(96)*3
c = c.replace('if text.startswith(""):', 'if text.startswith("' + fence + '"):')
c = c.replace('if text.endswith("")', 'if text.endswith("' + fence + '"):')
p.write_text(c, encoding='utf-8')
print("Fixed brand_studio.py")
