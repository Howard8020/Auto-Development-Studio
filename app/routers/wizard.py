from fastapi import APIRouter, Request, Form, HTTPException
import zipfile
from fastapi.responses import HTMLResponse, FileResponse, PlainTextResponse
from starlette.responses import RedirectResponse
from starlette.templating import Jinja2Templates
import json, os, subprocess, re, urllib.request, urllib.error
from datetime import datetime
from pathlib import Path
from typing import Optional

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# ---- session helpers ----
S = {}  # simple in-memory session store

def get_session(req):
    sid = req.cookies.get("session", "default")
    if sid not in S:
        S[sid] = {"scope": "", "answers": {}, "compiled_scope": ""}
    return S[sid]

def save_session(req, data):
    sid = req.cookies.get("session", "default")
    S[sid].update(data)

# ---- AI config ----
def ai_config():
    return {
        "api_key": os.environ.get("AI_API_KEY") or os.environ.get("OPENAI_API_KEY") or "",
        "model": os.environ.get("AI_MODEL", "gpt-4o-mini"),
        "base_url": os.environ.get("AI_API_BASE", "https://api.openai.com/v1").rstrip("/"),
    }

# ================================================================
# Step 1: Scope
# ================================================================
@router.get("/wizard", response_class=HTMLResponse)
async def wizard_home(req: Request):
    return templates.TemplateResponse("wizard/scope.html", {"request": req})

@router.post("/wizard/save-scope")
async def wizard_save_scope(req: Request, scope: str = Form(""), scope_file: Optional[str] = Form(None)):
    s = get_session(req)
    text = scope.strip()
    if not text:
        text = scope_file or ""
    s["scope"] = text.strip()
    save_session(req, s)
    return RedirectResponse(url="/wizard/requirements", status_code=303)

# ================================================================
# Step 2: Requirements
# ================================================================
@router.get("/wizard/requirements", response_class=HTMLResponse)
async def wizard_requirements(req: Request):
    s = get_session(req)
    cfg = ai_config()
    return templates.TemplateResponse("wizard/requirements.html", {
        "request": req,
        "scope": s.get("scope", ""),
        "ai_enabled": bool(cfg["api_key"]),
    })

@router.post("/wizard/save-requirements")
async def wizard_save_requirements(req: Request):
    form = await req.form()
    answers = {}
    for key, val in form.multi_items():
        answers[key] = val
    s = get_session(req)
    s["answers"] = answers
    s["compiled_scope"] = compile_scope_document(answers, s.get("scope", ""))
    save_session(req, s)
    return RedirectResponse(url="/wizard/preview", status_code=303)

# ================================================================
# Step 3: Preview
# ================================================================
@router.get("/wizard/preview", response_class=HTMLResponse)
async def wizard_preview(req: Request):
    s = get_session(req)
    cfg = ai_config()
    return templates.TemplateResponse("wizard/preview.html", {
        "request": req,
        "scope": s.get("scope", ""),
        "answers": s.get("answers", {}),
        "compiled_scope": s.get("compiled_scope", ""),
        "ai_enabled": bool(cfg["api_key"]),
    })

# ================================================================
# Step 4: Generate
# ================================================================
@router.post("/wizard/generate")
async def wizard_generate(req: Request):
    s = get_session(req)
    answers = s.get("answers", {})
    scope_text = s.get("scope", "")
    compiled = s.get("compiled_scope", "")

cmd = ["python", "generate_project.py"]
    env = os.environ.copy()
    env["PROJECT_NAME"] = answers.get("project_name", "MyApp").strip()
    env["TAGLINE"] = answers.get("tagline", "").strip()
    env["BRAND_COLOR"] = answers.get("brand_color", "#6366f1").strip()
    env["ENABLE_AUTH"] = "yes" if answers.get("enable_auth") == "yes" else ""
    env["ENABLE_DATABASE"] = "yes" if answers.get("enable_database", "yes") == "yes" else ""
    env["PAGES"] = answers.get("pages", "").strip()
    env["EXTRA_DEPS"] = answers.get("extra_deps", "").strip()
    env["SCOPE"] = scope_text.strip()
    env["COMPILED_SCOPE"] = compiled.strip()

    if answers.get("enable_auth") == "yes":
        cmd.append("--auth")
    if answers.get("enable_database", "yes") == "yes":
        cmd.append("--database")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, env=env)
        output = result.stdout + result.stderr
        s["generate_output"] = output
        s["generate_success"] = result.returncode == 0
    except subprocess.TimeoutExpired:
        s["generate_output"] = "ERROR: Generation timed out after 120 seconds."
        s["generate_success"] = False
    except FileNotFoundError:
        s["generate_output"] = "ERROR: generate_project.py not found in workspace."
        s["generate_success"] = False

    save_session(req, s)
    return RedirectResponse(url="/wizard/success", status_code=303)

# ================================================================
# Step 5: Success
# ================================================================
@router.get("/wizard/success", response_class=HTMLResponse)
async def wizard_success(req: Request):
    s = get_session(req)
    return templates.TemplateResponse("wizard/success.html", {
        "request": req,
        "output": s.get("generate_output", "No output."),
        "success": s.get("generate_success", False),
        "scope": s.get("scope", ""),
        "project_name": s.get("answers", {}).get("project_name", "MyApp"),
    })

# ================================================================
# Export compiled scope as .md
# ================================================================
@router.get("/wizard/export-markdown")
async def wizard_export_markdown(req: Request):
    s = get_session(req)
    md = s.get("compiled_scope", "# Project Scope\n\nNo scope compiled yet.\n")
    project_name = s.get("answers", {}).get("project_name", "project-scope").strip().replace(" ", "-").lower()
    filename = f"{project_name}-scope.md"
    return PlainTextResponse(content=md, headers={
        "Content-Type": "text/markdown; charset=utf-8",
        "Content-Disposition": f'attachment; filename="{filename}"',
    })

# ================================================================


# ================================================================
# Download generated project
# ================================================================
@router.get("/wizard/download/{project_name}")
async def wizard_download(project_name: str):
    """Download a generated project as zip."""
    from pathlib import Path
    project_dir = Path(GENERATED_DIR) / project_name
    if not project_dir.exists():
        return JSONResponse({"error": "Project not found."}, status_code=404)

    zip_path = Path(GENERATED_DIR) / f"{project_name}.zip"
    if zip_path.exists():
        zip_path.unlink()

    import zipfile
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(str(project_dir)):
            for filename in files:
                file_path = os.path.join(root, filename)
                arcname = os.path.relpath(file_path, str(project_dir))
                zf.write(file_path, arcname)

    from fastapi.responses import FileResponse
    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"{project_name}.zip",
    )

# AI Suggest endpoint
# ================================================================
@router.post("/wizard/ai-suggest")
async def wizard_ai_suggest(req: Request):
    cfg = ai_config()
    if not cfg["api_key"]:
        raise HTTPException(400, "AI API key not configured. Set AI_API_KEY or OPENAI_API_KEY.")

    body = await req.json()
    category = body.get("category", "")
    current_answers = body.get("current_answers", {})

    answers_text = "\n".join(
        f"- **{k.replace('_',' ').title()}**: {v or '(empty)'}"
        for k, v in current_answers.items() if v
    )

    prompt = f"""You are a product scoping assistant. Based on the partial project answers below, suggest content for the **"{category.replace('_',' ').title()}"** field.

Current project answers:
{answers_text}

Generate a concise, actionable suggestion for the "{category.replace('_',' ').title()}" field only. Return just the suggested answer text, no preamble."""

    payload = json.dumps({
        "model": cfg["model"],
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 512,
        "temperature": 0.7,
    }).encode()

    req_url = f"{cfg['base_url']}/chat/completions"
    headers = {
        "Authorization": f"Bearer {cfg['api_key']}",
"Content-Type": "application/json",
    }

    try:
        http_req = urllib.request.Request(req_url, data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(http_req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            suggestion = data["choices"][0]["message"]["content"].strip()
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()[:200]
        suggestion = f"AI API error {e.code}: {err_body}"
    except Exception as e:
        suggestion = f"Error: {str(e)}"

    return {"suggestion": suggestion}

# ================================================================
# Scope compilation
# ================================================================
def compile_scope_document(answers: dict, scope_text: str = "") -> str:
    lines = []
    project_name = answers.get("project_name", "").strip() or "Project"

    lines.append(f"# {project_name} — Project Scope Document")
    lines.append(f"")
    lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")

    # 1. Overview
    lines.append(f"## 1. Project Overview")
    lines.append(f"")
    if scope_text:
        lines.append(f"**Scope Summary:**")
        lines.append(f"{scope_text}")
        lines.append(f"")
    tagline = answers.get("tagline", "").strip()
    if tagline:
        lines.append(f"**Tagline:** {tagline}")
        lines.append(f"")

    # 2. Business Context
    lines.append(f"## 2. Business Context & Objectives")
    lines.append(f"")
    for key, label in [("business_objectives", "Business Goals"), ("pain_points", "Pain Points"), ("success_vision", "Success Vision")]:
        val = answers.get(key, "").strip()
        if val:
            lines.append(f"### {label}")
            lines.append(f"{val}")
            lines.append(f"")

    # 3. Target Users
    lines.append(f"## 3. Target Users & Stakeholders")
    lines.append(f"")
    for key, label in [("target_users", "Target Users"), ("user_roles", "Roles & Permissions")]:
        val = answers.get(key, "").strip()
        if val:
            lines.append(f"### {label}")
            lines.append(f"{val}")
            lines.append(f"")

    # 4. Core Features
    lines.append(f"## 4. Core Functionality & Features")
    lines.append(f"")
    for key, label in [("must_have_features", "Must-Have (MVP)"), ("should_have_features", "Should-Have (Post-MVP)"), ("integrations", "Third-Party Integrations")]:
        val = answers.get(key, "").strip()
        if val:
            lines.append(f"### {label}")
            lines.append(f"{val}")
            lines.append(f"")

    # 5. UX & Interface
    lines.append(f"## 5. User Experience & Interface")
    lines.append(f"")
    platforms = []
    if answers.get("platform_web") == "yes": platforms.append("Web")
    if answers.get("platform_mobile") == "yes": platforms.append("Mobile")
    if answers.get("platform_api") == "yes": platforms.append("API")
    if platforms:
        lines.append(f"**Platforms:** {', '.join(platforms)}")
        lines.append(f"")
    design_req = answers.get("design_requirements", "").strip()
    if design_req:
        lines.append(f"### Design & Accessibility")
        lines.append(f"{design_req}")
        lines.append(f"")

    # 6. Technical
    lines.append(f"## 6. Technical & Non-Functional Requirements")
    lines.append(f"")
    for key, label in [("tech_stack", "Tech Stack"), ("performance", "Performance"), ("compliance", "Security & Compliance")]:
        val = answers.get(key, "").strip()
        if val:
            lines.append(f"### {label}")
            lines.append(f"{val}")
            lines.append(f"")

    # 7. Scope Boundaries
    lines.append(f"## 7. Scope Boundaries")
    lines.append(f"")
    for key, label in [("in_scope", "In Scope"), ("out_of_scope", "Out of Scope")]:
        val = answers.get(key, "").strip()
        if val:
            lines.append(f"### {label}")
            lines.append(f"{val}")
lines.append(f"")
    timeline = answers.get("timeline", "").strip()
    budget = answers.get("budget", "").strip()
    if timeline or budget:
        lines.append(f"**Timeline:** {timeline or 'TBD'}")
        lines.append(f"**Budget:** {budget or 'TBD'}")
        lines.append(f"")

    # 8. Success Metrics
    lines.append(f"## 8. Success Metrics & Post-Launch")
    lines.append(f"")
    for key, label in [("kpis", "KPIs"), ("analytics", "Analytics & Monitoring")]:
        val = answers.get(key, "").strip()
        if val:
            lines.append(f"### {label}")
            lines.append(f"{val}")
            lines.append(f"")

    # 9. Risks
    lines.append(f"## 9. Risks & Assumptions")
    lines.append(f"")
    for key, label in [("risks", "Risks"), ("assumptions", "Assumptions")]:
        val = answers.get(key, "").strip()
        if val:
            lines.append(f"### {label}")
            lines.append(f"{val}")
            lines.append(f"")
    extra = answers.get("additional_context", "").strip()
    if extra:
        lines.append(f"### Additional Context")
        lines.append(f"{extra}")
        lines.append(f"")

    return "\n".join(lines)
