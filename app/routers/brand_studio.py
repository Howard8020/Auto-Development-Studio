"""Brand Studio - AI-powered brand identity extraction."""
import os, uuid, json, base64, httpx
from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from pathlib import Path

router = APIRouter(prefix="/brand", tags=["brand-studio"])
_templates = None

def _init_templates(templates):
    global _templates
    _templates = templates

DEFAULT_KIT = {
    "style_name": "Modern Dark",
    "mood": ["professional", "clean", "modern"],
    "colors": {
        "bg_primary": "#0f0f1a", "bg_secondary": "#1a1a2e",
        "bg_card": "#ffffff08", "text_primary": "#e0e0e0",
        "text_secondary": "#a0a0b0", "accent": "#6366f1",
        "cta": "#22c55e", "gradient_start": "#6366f1", "gradient_end": "#06b6d4",
    },
    "typography": {"heading_weight": "700", "heading_transform": "none", "body_size": "16px", "line_height": "1.7"},
    "ui": {"border_radius": "0.75rem", "shadow_style": "soft", "button_style": "filled", "card_border": "subtle"},
    "favicon": {"shape": "circle", "icon_description": "geometric abstract mark"},
}


@router.get("/step", response_class=HTMLResponse)
async def brand_step(request: Request):
    session = request.session
    return _templates.TemplateResponse(request, "brand_studio.html", {
        "request": request, "step": 4, "total": 7,
        "project_name": session.get("project_name", ""),
        "brand_kit": session.get("brand_kit", {}),
    })


@router.post("/analyze")
async def analyze_brand(request: Request, images: list[UploadFile] = File(default=[])):
    uploads_dir = Path("uploads") / "brand"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    image_data = []
    for img in images:
        if img.filename:
            content = await img.read()
            ext = Path(img.filename).suffix or ".png"
            filepath = uploads_dir / f"{uuid.uuid4().hex}{ext}"
            filepath.write_bytes(content)
            image_data.append({
                "path": str(filepath),
                "b64": base64.b64encode(content).decode(),
                "mime": img.content_type or "image/png",
            })
    if not image_data:
        return JSONResponse({"error": "No images uploaded"}, status_code=400)
    brand_kit = await _run_vision_analysis(image_data)
    request.session["brand_kit"] = brand_kit
    return JSONResponse(brand_kit)


@router.post("/customize")
async def customize_brand(request: Request, brand_data: str = Form(...)):
    try:
        brand_kit = json.loads(brand_data)
    except json.JSONDecodeError:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)
    request.session["brand_kit"] = brand_kit
    return JSONResponse({"status": "ok", "brand_kit": brand_kit})


@router.post("/skip")
async def skip_brand(request: Request):
    request.session["brand_kit"] = DEFAULT_KIT
    return JSONResponse({"status": "ok", "brand_kit": DEFAULT_KIT, "skipped": True})


async def _run_vision_analysis(image_data: list[dict]) -> dict:
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    model = os.getenv("BRAND_VISION_MODEL", "anthropic/claude-sonnet-4")
    content_blocks = []
    for img in image_data:
        mime, b64 = img["mime"], img["b64"]
        content_blocks.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}})
    prompt = (
        "Analyze these design reference images and extract a brand kit. "
        "Return ONLY valid JSON (no markdown fences): "
        '{"style_name":"...","mood":["..."],"colors":{"bg_primary":"#","bg_secondary":"#","bg_card":"#",'
        '"text_primary":"#","text_secondary":"#","accent":"#","cta":"#","gradient_start":"#","gradient_end":"#"},'
        '"typography":{"heading_weight":"700","heading_transform":"none","body_size":"16px","line_height":"1.7"},'
        '"ui":{"border_radius":"0.75rem","shadow_style":"soft","button_style":"filled","card_border":"subtle"},'
'"favicon":{"shape":"circle","icon_description":"..."}}. Be opinionated. No generic blue defaults.'
    )
    content_blocks.append({"type": "text", "text": prompt})
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": model, "messages": [{"role": "user", "content": content_blocks}], "max_tokens": 1500})
        if resp.status_code != 200:
            return DEFAULT_KIT.copy()
        text = resp.json()["choices"][0]["message"]["content"].strip()
        if text.startswith("```"):
            text = "\n".join(text.split("\n")[1:])
        if text.endswith("```"):
            text = text[:-3]
        return json.loads(text.strip())
    except Exception:
        return DEFAULT_KIT.copy()
