p = open('app/main.py', encoding='utf-8').read()
p = p.replace(
    "from fastapi import FastAPI, Request",
    "from fastapi import FastAPI, Request\nfrom fastapi.responses import RedirectResponse"
)
p = p.replace(
    "app = FastAPI(title=settings.app_name, debug=settings.debug)",
    "app = FastAPI(title=settings.app_name, debug=settings.debug)\n\n@app.get('/')\nasync def root_redirect():\n    return RedirectResponse(url='/wizard')"
)
open('app/main.py', 'w', encoding='utf-8').write(p)
print("Patched ?")
