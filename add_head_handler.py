import re
p = 'app/main.py'
c = open(p, encoding='utf-8').read()
m = re.search(r'^(app\s*=\s*FastAPI\(.*?\))', c, re.MULTILINE)
if m:
    handler = m.group(1) + '\n\n\n@app.head("/")\nasync def health_head():\n    from fastapi.responses import Response\n    return Response(status_code=200)\n'
    c = c[:m.start()] + handler + c[m.end():]
    open(p, 'w', encoding='utf-8').write(c)
    print('HEAD handler added')
else:
    print('Could not find app = FastAPI(...)')
