from pathlib import Path
p = Path('app/templates/brand_studio.html')
c = p.read_text(encoding='utf-8').lstrip('\ufeff')
p.write_text(c, encoding='utf-8')
print(f"BOM stripped, size now: {len(c)}")
