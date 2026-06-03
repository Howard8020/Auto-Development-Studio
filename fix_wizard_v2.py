#!/usr/bin/env python3
"""Fix wizard.py to match actual generator CLI contract + patch generator to use scope."""
import json
from pathlib import Path

REPO = Path(".")
print("=== Fixing wizard.py and generator ===\n")

# ── 1. Rewrite wizard.py ──────────────────────────────────────────────────────
wizard_py = r'''"""Wizard router - multi-step project scoping and generation."""

import json
import os
import subprocess
import tempfile
import zipfile
from pathlib import Path

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/wizard", tags=["wizard"])

templates = Jinja2Templates(directory="app/templates")
templates.env.globals["app_name"] = "Auto Development Studio"

GENERATED_DIR = Path(__file__).resolve().parent.parent.parent / "generated"
GENERATED_DIR.mkdir(exist_ok=True)

GENERATE_SCRIPT = Path(__file__).resolve().parent.parent.parent / "scripts" / "generate_project.py"


@router.get("")
async def wizard_start(request: Request):
    """Step 1: Project scope input."""
    return templates.TemplateResponse(request, "wizard/scope.html")


@router.get("/questions")
async def wizard_questions(request: Request):
    """Step 2: Guided questionnaire."""
    scope = request.session.get("wizard_data", {}).get("scope", "")
    return templates.TemplateResponse(request, "wizard/questions.html", {"scope": scope})


@router.get("/preview")
async def wizard_preview(request: Request):
    """Step 3: Preview before generation."""
    data = request.session.get("wizard_data", {})
    if not data or not data.get("name"):
        return RedirectResponse("/wizard", status_code=302)
    return templates.TemplateResponse(request, "wizard/preview.html", {"data": data})


@router.post("/save-scope")
async def save_scope(
    request: Request,
    scope: str = Form(""),
    scope_file: UploadFile = File(None),
):
    """Save the project scope and redirect to questions."""
    scope_text = scope.strip()

    if scope_file and scope_file.filename:
        try:
            content = await scope_file.read()
            file_text = content.decode("utf-8", errors="replace").strip()
            if file_text:
                if scope_text:
                    scope_text = f"{file_text}\n\n--- Additional Context ---\n{scope_text}"
                else:
                    scope_text = file_text
        except Exception:
            pass

    if not scope_text:
        return HTMLResponse(
            '<div class="p-4 bg-red-50 text-red-700 rounded-lg"><strong>Error:</strong> Please enter or upload a project scope.</div>',
            status_code=400,
        )

    request.session["wizard_data"] = {"scope": scope_text}

    resp = HTMLResponse("", status_code=200)
    resp.headers["HX-Redirect"] = "/wizard/questions"
    return resp


@router.post("/save-answers")
async def save_answers(
    request: Request,
    name: str = Form(alias="project_name", default=""),
    tagline: str = Form(""),
    color: str = Form(alias="brand_color", default="#ff6600"),
    with_auth: str = Form(alias="enable_auth", default="no"),
    with_db: str = Form(alias="enable_database", default="yes"),
    pages: str = Form(""),
    deps: str = Form(alias="extra_deps", default=""),
):
    """Save questionnaire answers and redirect to preview."""
    data = request.session.get("wizard_data", {})
    data.update({
        "name": name,
        "tagline": tagline,
        "color": color,
        "with_auth": with_auth,
        "with_db": with_db,
        "pages": pages,
        "deps": deps,
    })
    request.session["wizard_data"] = data

    resp = HTMLResponse("", status_code=200)
    resp.headers["HX-Redirect"] = "/wizard/preview"
    return resp


@router.post("/generate")
async def generate_project(request: Request):
    """Generate the project from wizard data."""
    data = request.session.get("wizard_data", {})
    if not data or not data.get("name"):
        return JSONResponse({"error": "No project data found. Please start the wizard again."}, status_code=400)

    # Build the JSON input that the generator expects
    input_data = {
        "name": data["name"],
        "tagline": data.get("tagline", ""),
        "color": data.get("color", "#ff6600"),
        "with_auth": data.get("with_auth", "no") == "yes",
        "with_db": data.get("with_db", "yes") == "yes",
        "pages": data.get("pages", ""),
        "deps": data.get("deps", ""),
        "scope": data.get("scope", ""),
    }

    # Write temp JSON input
    input_path = GENERATED_DIR / f"_input_{data['name'].replace(' ', '_').lower()}.json"
    input_path.write_text(json.dumps(input_data, indent=2))

    cmd = [
        "python", str(GENERATE_SCRIPT),
        "--input", str(input_path),
        "--output", str(GENERATED_DIR),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        # Clean up temp input
        input_path.unlink(missing_ok=True)

        if result.returncode != 0:
            return JSONResponse({
                "error": f"Generation failed: {result.stderr[:500]}\nStdout: {result.stdout[:500]}",
            }, status_code=500)

        # Parse output for the zip path
        lines = [l for l in result.stdout.strip().split("\n") if l.strip()]
        zip_path = None
        project_name = data["name"].replace(" ", "-").lower()

        for line in lines:
            if "ZIP:" in line or line.endswith(".zip"):
                candidate = line.split(":")[-1].strip()
                if Path(candidate).exists():
                    zip_path = candidate
                    break

        if not zip_path:
            # Try to find the zip by convention
            candidate = str(GENERATED_DIR / f"{project_name}.zip")
            if Path(candidate).exists():
                zip_path = candidate

        download_url = f"/wizard/download/{project_name}"

        return JSONResponse({
            "success": True,
            "project_name": project_name,
            "download_url": download_url,
            "redirect": f"/wizard/success/{project_name}",
        })

    except subprocess.TimeoutExpired:
        input_path.unlink(missing_ok=True)
        return JSONResponse({"error": "Generation timed out."}, status_code=500)
    except Exception as e:
        input_path.unlink(missing_ok=True)
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/download/{project_name}")
async def download_project(project_name: str):
    """Download a generated project as zip."""
    # Try exact name first, then look for zip
    zip_path = GENERATED_DIR / f"{project_name}.zip"
    if not zip_path.exists():
        # Search for any matching zip
        for candidate in GENERATED_DIR.glob(f"*{project_name}*"):
            if candidate.suffix == ".zip":
                zip_path = candidate
                break

    if not zip_path.exists():
        return JSONResponse({"error": "Project not found."}, status_code=404)

    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"{project_name}.zip",
    )


@router.get("/success/{project_name}")
async def wizard_success(request: Request, project_name: str):
    """Success page after generation."""
    request.session.pop("wizard_data", None)
    return templates.TemplateResponse(request, "wizard/success.html", {"project_name": project_name})
'''

# ── 2. Patch generator to write SCOPE.md ──────────────────────────────────────
gen_path = REPO / "scripts" / "generate_project.py"
gen_content = gen_path.read_text(encoding="utf-8")

if "SCOPE.md" not in gen_content:
    # Insert scope writing before the ZIP section
    marker = "    # ___ ZIP it ___"
    scope_block = '''    # ___ Write scope to SCOPE.md ___
scope_text = input_data.get("scope", "")
    if scope_text:
        scope_file = out / "SCOPE.md"
        scope_md = f"# Project Scope\\n\\n{scope_text}\\n"
        scope_file.write_text(scope_md)
        print(f"  Wrote SCOPE.md ({len(scope_text)} chars)")

'''
    if marker in gen_content:
        gen_content = gen_content.replace(marker, scope_block + marker)
        gen_path.write_text(gen_content, encoding="utf-8")
        print("PATCHED: generate_project.py - added SCOPE.md output")
    else:
        # Try alternate marker
        marker2 = "# ___ ZIP"
        lines = gen_content.split("\n")
        for i, line in enumerate(lines):
            if "ZIP" in line and "#" in line:
                print(f"  Found ZIP marker at line {i}: {line.strip()}")
                # Insert before this line
                indent = "    "
                scope_lines = [
                    "",
                    f"{indent}# ___ Write scope to SCOPE.md ___",
                    f'{indent}scope_text = input_data.get("scope", "")',
                    f"{indent}if scope_text:",
                    f'{indent}    scope_file = out / "SCOPE.md"',
                    f'{indent}    scope_md = f"# Project Scope\\n\\n{{scope_text}}\\n"',
                    f"{indent}    scope_file.write_text(scope_md)",
                    f'{indent}    print(f"  Wrote SCOPE.md ({{len(scope_text)}} chars)")',
                    "",
                ]
                lines[i:i] = scope_lines
                gen_path.write_text("\n".join(lines), encoding="utf-8")
                print("PATCHED: generate_project.py (alternate insertion)")
                break
        else:
            print("WARNING: Could not find ZIP marker in generator")
            # Show what's around line 190-200 for debugging
            lines = gen_content.split("\n")
            for i in range(max(0, len(lines)-30), len(lines)):
                print(f"  {i}: {lines[i]}")
else:
    print("SKIP: generate_project.py already has SCOPE.md")

# ── 3. Write wizard.py ────────────────────────────────────────────────────────
(REPO / "app" / "routers" / "wizard.py").write_text(wizard_py, encoding="utf-8")
print("WRITTEN: app/routers/wizard.py")

# ── 4. Validate syntax ────────────────────────────────────────────────────────
import ast
for fpath in ["app/routers/wizard.py", "scripts/generate_project.py"]:
    try:
        ast.parse(open(fpath, encoding="utf-8").read())
        print(f"SYNTAX OK: {fpath}")
    except SyntaxError as e:
        print(f"SYNTAX ERROR: {fpath}: {e}")

print("\nDone! Ready to commit.")
@"
import json
from pathlib import Path
import ast

REPO = Path(".")

# Write wizard.py
wizard = '''\"\"\"Wizard router - multi-step project scoping and generation.\"\"\"

import json
import os
import subprocess
import zipfile
from pathlib import Path

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/wizard", tags=["wizard"])
templates = Jinja2Templates(directory="app/templates")
templates.env.globals["app_name"] = "Auto Development Studio"

GENERATED_DIR = Path(__file__).resolve().parent.parent.parent / "generated"
GENERATED_DIR.mkdir(exist_ok=True)
GENERATE_SCRIPT = Path(__file__).resolve().parent.parent.parent / "scripts" / "generate_project.py"

@router.get("")
async def wizard_start(request: Request):
    return templates.TemplateResponse(request, "wizard/scope.html")

@router.get("/questions")
async def wizard_questions(request: Request):
    scope = request.session.get("wizard_data", {}).get("scope", "")
return templates.TemplateResponse(request, "wizard/questions.html", {"scope": scope})

@router.get("/preview")
async def wizard_preview(request: Request):
    data = request.session.get("wizard_data", {})
    if not data or not data.get("name"):
        return RedirectResponse("/wizard", status_code=302)
    return templates.TemplateResponse(request, "wizard/preview.html", {"data": data})

@router.post("/save-scope")
async def save_scope(request: Request, scope: str = Form(""), scope_file: UploadFile = File(None)):
    scope_text = scope.strip()
    if scope_file and scope_file.filename:
        try:
            content = await scope_file.read()
            file_text = content.decode("utf-8", errors="replace").strip()
            if file_text:
                scope_text = f"{file_text}\\n\\n--- Additional Context ---\\n{scope_text}" if scope_text else file_text
        except Exception:
            pass
    if not scope_text:
        return HTMLResponse(
            '<div class="p-4 bg-red-50 text-red-700 rounded-lg">Please enter or upload a scope.</div>',
            status_code=400,
        )
    request.session["wizard_data"] = {"scope": scope_text}
    resp = HTMLResponse("", status_code=200)
    resp.headers["HX-Redirect"] = "/wizard/questions"
    return resp

@router.post("/save-answers")
async def save_answers(
    request: Request,
    name: str = Form(alias="project_name", default=""),
    tagline: str = Form(""),
    color: str = Form(alias="brand_color", default="#ff6600"),
    with_auth: str = Form(alias="enable_auth", default="no"),
    with_db: str = Form(alias="enable_database", default="yes"),
    pages: str = Form(""),
    deps: str = Form(alias="extra_deps", default=""),
):
    data = request.session.get("wizard_data", {})
    data.update({
        "name": name, "tagline": tagline, "color": color,
        "with_auth": with_auth, "with_db": with_db, "pages": pages, "deps": deps,
    })
    request.session["wizard_data"] = data
    resp = HTMLResponse("", status_code=200)
    resp.headers["HX-Redirect"] = "/wizard/preview"
    return resp

@router.post("/generate")
async def generate_project(request: Request):
    data = request.session.get("wizard_data", {})
    if not data or not data.get("name"):
        return JSONResponse({"error": "No project data."}, status_code=400)
    input_data = {
        "name": data["name"], "tagline": data.get("tagline", ""),
        "color": data.get("color", "#ff6600"),
        "with_auth": data.get("with_auth", "no") == "yes",
        "with_db": data.get("with_db", "yes") == "yes",
        "pages": data.get("pages", ""), "deps": data.get("deps", ""),
        "scope": data.get("scope", ""),
    }
    input_path = GENERATED_DIR / f"_input_{data['name'].replace(' ', '_')}.json"
    input_path.write_text(json.dumps(input_data, indent=2))
    cmd = ["python", str(GENERATE_SCRIPT), "--input", str(input_path), "--output", str(GENERATED_DIR)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        input_path.unlink(missing_ok=True)
        if result.returncode != 0:
            return JSONResponse({"error": f"Failed: {result.stderr[:500]}"}, status_code=500)
        project_name = data["name"].replace(" ", "-").lower()
        return JSONResponse({"success": True, "project_name": project_name,
            "download_url": f"/wizard/download/{project_name}"})
    except Exception as e:
        input_path.unlink(missing_ok=True)
        return JSONResponse({"error": str(e)}, status_code=500)

@router.get("/download/{project_name}")
async def download_project(project_name: str):
    zip_path = GENERATED_DIR / f"{project_name}.zip"
    if not zip_path.exists():
        for c in GENERATED_DIR.glob(f"*{project_name}*"):
            if c.suffix == ".zip":
                zip_path = c
                break
    if not zip_path.exists():
        return JSONResponse({"error": "Not found."}, status_code=404)
    return FileResponse(zip_path, media_type="application/zip", filename=f"{project_name}.zip")

@router.get("/success/{project_name}")
async def wizard_success(request: Request, project_name: str):
    request.session.pop("wizard_data", None)
    return templates.TemplateResponse(request, "wizard/success.html", {"project_name": project_name})
'''

(REPO / "app" / "routers" / "wizard.py").write_text(wizard, encoding="utf-8")
print("WRITTEN: wizard.py")

# Patch generator
gen = (REPO / "scripts" / "generate_project.py").read_text(encoding="utf-8")
if "SCOPE.md" not in gen:
    # Find the ZIP marker line
    lines = gen.split("\n")
    for i, line in enumerate(lines):
        if "ZIP it" in line or "ZIP" in line and "___" in line:
            indent = "    "
            insert = [
                "",
                indent + '# ___ Write scope to SCOPE.md ___',
                indent + 'scope_text = input_data.get("scope", "")',
                indent + 'if scope_text:',
                indent + '    scope_file = out / "SCOPE.md"',
                indent + '    scope_md = f"# Project Scope\\n\\n{scope_text}\\n"',
                indent + '    scope_file.write_text(scope_md)',
                indent + '    print(f"  Wrote SCOPE.md ({len(scope_text)} chars)")',
                "",
            ]
            lines[i:i] = insert
            (REPO / "scripts" / "generate_project.py").write_text("\n".join(lines), encoding="utf-8")
            print(f"PATCHED: generate_project.py (inserted before line {i})")
            break
    else:
        # Fallback: find last occurrence of 'zip' related code
        for i, line in enumerate(lines):
            if "zip_path" in line and "Path" in line:
                indent = "    "
                insert = [
                    "",
                    indent + 'scope_text = input_data.get("scope", "")',
                    indent + 'if scope_text:',
                    indent + '    scope_file = out / "SCOPE.md"',
                    indent + '    scope_md = f"# Project Scope\\n\\n{scope_text}\\n"',
                    indent + '    scope_file.write_text(scope_md)',
                    "",
                ]
                lines[i:i] = insert
                (REPO / "scripts" / "generate_project.py").write_text("\n".join(lines), encoding="utf-8")
                print(f"PATCHED: generate_project.py (fallback, before line {i})")
                break
        else:
            print("FAILED to find insertion point")
else:
    print("SKIP: already patched")

# Validate
for f in ["app/routers/wizard.py", "scripts/generate_project.py"]:
    try:
        ast.parse(open(f, encoding="utf-8").read())
        print(f"OK: {f}")
    except SyntaxError as e:
        print(f"ERROR: {f}: {e}")
