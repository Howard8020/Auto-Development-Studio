from pathlib import Path
files = [
    'app/templates/wizard/scope.html',
    'app/templates/wizard/questions.html', 
    'app/templates/wizard/preview.html',
    'app/templates/wizard/success.html',
    'app/templates/index.html'
]
for f in files:
    p = Path(f)
    if p.exists():
        c = p.read_text(encoding='utf-8').lstrip('\ufeff')
        print(f'\n{"="*60}')
        print(f'FILE: {f} ({len(c)} chars)')
        print(f'{"="*60}')
        print(c)
    else:
        print(f'{f}: NOT FOUND')
