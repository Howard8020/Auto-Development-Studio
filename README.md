# Auto Development Studio

An AI-powered web studio for auto-generating full-stack web applications.

Built with **FastAPI**, **Tailwind CSS v3**, **HTMX**, and **Alpine.js**.

## Getting Started

```bash
uv sync
npm install
npx tailwindcss -i ./app/static/css/input.css -o ./app/static/css/output.css --minify
cp .env.example .env
uvicorn app.main:app --reload
```

## Project Wizard

Visit `/wizard` to generate a new project from a detailed scope and guided questions.

## Features
- Google OAuth authentication (optional)
- Project generation wizard
- SQLite database with SQLAlchemy
- Tailwind CSS v3 with orange brand palette
- HTMX and Alpine.js for interactivity
- Render-ready deployment