import pathlib

# Write wizard.py using write_text - the @ decorators are just string content
content = []
content.append('"""Wizard router - multi-step project scoping and generation."""')
content.append('')
content.append('import json')
content.append('import os')
content.append('import subprocess')
content.append('import zipfile')
content.append('from pathlib import Path')
content.append('')
content.append('from fastapi import APIRouter, File, Form, Request, UploadFile')
content.append('from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse')
content.append('from fastapi.templating import Jinja2Templates')
content.append('')
content.append('router = APIRouter(prefix="/wizard", tags=["wizard"])')
content.append('templates = Jinja2Templates(directory="app/templates")')
content.append('templates.env.globals["app_name"] = "Auto Development Studio"')
content.append('')
content.append('GENERATED_DIR = Path(__file__).resolve().parent.parent.parent / "generated"')
content.append('GENERATED_DIR.mkdir(exist_ok=True)')
content.append('GENERATE_SCRIPT = Path(__file__).resolve().parent.parent.parent / "scripts" / "generate_project.py"')
content.append('')

# Decorator helper
def route(method, path, fn_sig, body_lines):
    content.append(f'@router.{method}("{path}")')
    content.append(f'async def {fn_sig}:')
    for line in body_lines:
        content.append(line)
    content.append('')

route('get', '', 'wizard_start(request: Request)', [
    '    return templates.TemplateResponse(request, "wizard/scope.html")',
])

route('get', '/questions', 'wizard_questions(request: Request)', [
    '    scope = request.session.get("wizard_data", {}).get("scope", "")',
    '    return templates.TemplateResponse(request, "wizard/questions.html", {"scope": scope})',
])

route('get', '/preview', 'wizard_preview(request: Request)', [
    '    data = request.session.get("wizard_data", {})',
    '    if not data or not data.get("name"):',
    '        return RedirectResponse("/wizard", status_code=302)',
    '    return templates.TemplateResponse(request, "wizard/preview.html", {"data": data})',
])

route('post', '/save-scope', 'save_scope(request: Request, scope: str = Form(""), scope_file: UploadFile = File(None))', [
    '    scope_text = scope.strip()',
    '    if scope_file and scope_file.filename:',
    '        try:',
    '            raw = await scope_file.read()',
    '            ft = raw.decode("utf-8", errors="replace").strip()',
    '            if ft:',
    '                scope_text = ft + "\\n\\n--- Additional Context ---\\n" + scope_text if scope_text else ft',
    '        except Exception:',
    '            pass',
    '    if not scope_text:',
    "        return HTMLResponse('<div class=\"p-4 bg-red-50 text-red-700 rounded-lg\">Please enter or upload a scope.</div>', status_code=400)",
    '    request.session["wizard_data"] = {"scope": scope_text}',
    '    resp = HTMLResponse("", status_code=200)',
    '    resp.headers["HX-Redirect"] = "/wizard/questions"',
    '    return resp',
])

route('post', '/save-answers', 'save_answers(request: Request, name: str = Form(alias="project_name", default=""), tagline: str = Form(""), color: str = Form(alias="brand_color", default="#ff6600"), with_auth: str = Form(alias="enable_auth", default="no"), with_db: str = Form(alias="enable_database", default="yes"), pages: str = Form(""), deps: str = Form(alias="extra_deps", default=""))', [
    '    data = request.session.get("wizard_data", {})',
'    data.update({"name": name, "tagline": tagline, "color": color, "with_auth": with_auth, "with_db": with_db, "pages": pages, "deps": deps})',
    '    request.session["wizard_data"] = data',
    '    resp = HTMLResponse("", status_code=200)',
    '    resp.headers["HX-Redirect"] = "/wizard/preview"',
    '    return resp',
])

route('post', '/generate', 'generate_project(request: Request)', [
    '    data = request.session.get("wizard_data", {})',
    '    if not data or not data.get("name"):',
    '        return JSONResponse({"error": "No project data."}, status_code=400)',
    '    input_data = {"name": data["name"], "tagline": data.get("tagline",""), "color": data.get("color","#ff6600"), "with_auth": data.get("with_auth","no")=="yes", "with_db": data.get("with_db","yes")=="yes", "pages": data.get("pages",""), "deps": data.get("deps",""), "scope": data.get("scope","")}',
    '    input_path = GENERATED_DIR / f"_input_{data[chr(110)+chr(97)+chr(109)+chr(101)].replace(chr(32),chr(95))}.json"',
    '    input_path.write_text(json.dumps(input_data, indent=2))',
    '    cmd = ["python", str(GENERATE_SCRIPT), "--input", str(input_path), "--output", str(GENERATED_DIR)]',
    '    try:',
    '        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)',
    '        input_path.unlink(missing_ok=True)',
    '        if result.returncode != 0:',
    '            return JSONResponse({"error": "Failed: " + result.stderr[:500]}, status_code=500)',
    '        pn = data["name"].replace(" ", "-").lower()',
    '        return JSONResponse({"success": True, "project_name": pn, "download_url": "/wizard/download/" + pn})',
    '    except Exception as e:',
    '        input_path.unlink(missing_ok=True)',
    '        return JSONResponse({"error": str(e)}, status_code=500)',
])

route('get', '/download/{project_name}', 'download_project(project_name: str)', [
    '    zp = GENERATED_DIR / f"{project_name}.zip"',
    '    if not zp.exists():',
    '        for c in GENERATED_DIR.glob(f"*{project_name}*"):',
    '            if c.suffix == ".zip": zp = c; break',
    '    if not zp.exists():',
    '        return JSONResponse({"error": "Not found."}, status_code=404)',
    '    return FileResponse(zp, media_type="application/zip", filename=f"{project_name}.zip")',
])

route('get', '/success/{project_name}', 'wizard_success(request: Request, project_name: str)', [
    '    request.session.pop("wizard_data", None)',
    '    return templates.TemplateResponse(request, "wizard/success.html", {"project_name": project_name})',
])

pathlib.Path("app/routers/wizard.py").write_text("\n".join(content), encoding="utf-8")
print("WRITTEN: app/routers/wizard.py")

# Now patch generator
gen = pathlib.Path("scripts/generate_project.py").read_text(encoding="utf-8")
if "SCOPE.md" not in gen:
    lines = gen.split("\n")
    for i, line in enumerate(lines):
        if "ZIP it" in line:
            insert = [
                "",
                "    # ___ Write scope to SCOPE.md ___",
                '    scope_text = input_data.get("scope", "")',
                "    if scope_text:",
                '        scope_file = out / "SCOPE.md"',
                '        scope_md = "# Project Scope\\n\\n" + scope_text + "\\n"',
                "        scope_file.write_text(scope_md)",
                "",
            ]
            lines[i:i] = insert
            pathlib.Path("scripts/generate_project.py").write_text("\n".join(lines), encoding="utf-8")
            print(f"PATCHED: generate_project.py (inserted before line {i})")
            break
    else:
        print("FAILED: could not find ZIP marker")
        for i, l in enumerate(lines[-30:], start=len(lines)-30):
            print(f"  {i}: {l}")
else:
    print("SKIP: generator already has SCOPE.md")

# Validate syntax
import ast
for f in ["app/routers/wizard.py", "scripts/generate_project.py"]:
    try:
        ast.parse(open(f, encoding="utf-8").read())
        print(f"SYNTAX OK: {f}")
    except SyntaxError as e:
print(f"SYNTAX ERROR in {f}: {e}")
