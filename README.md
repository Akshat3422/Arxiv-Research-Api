# ArXiv Research Assistant

A FastAPI backend that searches ArXiv for a research topic, analyzes retrieved papers with a Groq-backed LangGraph workflow, and generates Markdown/PDF research reports.

The deployment entrypoint is Vercel-ready at `api/index.py`.

## Folder Structure

```text
.
|-- api/
|   |-- __init__.py
|   `-- index.py       # Vercel FastAPI entrypoint. Exposes app.
|-- graph.py           # LangGraph research workflow
|-- utils.py           # ArXiv fetching and report generation helpers
|-- main.py            # Optional local CLI runner
|-- requirements.txt   # Python dependencies
|-- vercel.json        # Vercel Python runtime config
|-- .env               # Local env vars only, do not commit
`-- research_report_*.md/.pdf
```

## Environment Variables

Required:

```text
GROQ_API_KEY=your_groq_api_key_here
```

Optional:

```text
CORS_ORIGINS=*
REPORT_OUTPUT_DIR=.
```

On Vercel, add `GROQ_API_KEY` in Project Settings > Environment Variables. The app writes generated reports to `/tmp` automatically when `VERCEL` is present.

## Local Setup

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run the FastAPI app locally:

```powershell
.\venv\Scripts\python.exe -m uvicorn api.index:app --host 127.0.0.1 --port 8000 --reload
```

Open:

```text
http://127.0.0.1:8000/
```

Optional CLI usage:

```powershell
.\venv\Scripts\python.exe main.py "preprocessing pipeline for STT and TTS voice agents"
```

## API Endpoints

Health check:

```http
GET /health
```

Run research:

```http
POST /research
Content-Type: application/json

{
  "query": "preprocessing pipeline for STT and TTS voice agents"
}
```

Open generated report files:

```http
GET /files/{file_path}
```

Only `.md` and `.pdf` report files are served.

## Deployed to Vercel
https://arxiv-research-api.vercel.app/
