import os
import sys
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from graph import research_assistant


class InvalidResearchRequest(ValueError):
    pass


app = FastAPI(
    title="ArXiv Research Assistant API",
    description="Research a topic on ArXiv and generate Markdown/PDF reports.",
    version="1.0.0",
)


def get_cors_origins() -> List[str]:
    raw_origins = os.getenv("CORS_ORIGINS", "*")
    return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


HOME_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>ArXiv Research Assistant</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f6f7fb;
      --panel: #ffffff;
      --text: #1b1f2a;
      --muted: #626b7f;
      --line: #dde2ee;
      --brand: #2155d6;
      --brand-dark: #173e9d;
      --danger: #b42318;
      --ok: #087443;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--text);
    }

    main {
      width: min(1080px, calc(100% - 32px));
      margin: 0 auto;
      padding: 40px 0 56px;
    }

    header { margin-bottom: 24px; }

    h1 {
      margin: 0 0 8px;
      font-size: clamp(2rem, 4vw, 3.25rem);
      line-height: 1.05;
      letter-spacing: 0;
    }

    .subtitle {
      margin: 0;
      max-width: 760px;
      color: var(--muted);
      font-size: 1rem;
      line-height: 1.6;
    }

    .search-panel,
    .result-panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: 0 18px 50px rgba(27, 31, 42, 0.08);
    }

    .search-panel {
      padding: 18px;
      margin-bottom: 18px;
    }

    form {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 12px;
      align-items: end;
    }

    label {
      display: block;
      margin-bottom: 8px;
      color: var(--muted);
      font-size: 0.9rem;
      font-weight: 650;
    }

    textarea {
      width: 100%;
      min-height: 108px;
      resize: vertical;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px 14px;
      color: var(--text);
      font: inherit;
      line-height: 1.45;
      outline: none;
      background: #fff;
    }

    textarea:focus {
      border-color: var(--brand);
      box-shadow: 0 0 0 3px rgba(33, 85, 214, 0.16);
    }

    button {
      min-height: 46px;
      border: 0;
      border-radius: 8px;
      padding: 0 18px;
      background: var(--brand);
      color: #fff;
      cursor: pointer;
      font: inherit;
      font-weight: 750;
      white-space: nowrap;
    }

    button:hover { background: var(--brand-dark); }
    button:disabled { cursor: wait; opacity: 0.72; }

    .status {
      min-height: 24px;
      margin-top: 12px;
      color: var(--muted);
      font-size: 0.95rem;
    }

    .status.error { color: var(--danger); }
    .status.done { color: var(--ok); }

    .result-panel {
      display: none;
      padding: 22px;
    }

    .result-panel.visible { display: block; }

    .meta-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 20px;
    }

    .meta {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      min-width: 0;
      background: #fbfcff;
    }

    .meta span {
      display: block;
      margin-bottom: 6px;
      color: var(--muted);
      font-size: 0.78rem;
      font-weight: 750;
      text-transform: uppercase;
    }

    .meta code,
    .meta a {
      overflow-wrap: anywhere;
      color: var(--text);
    }

    h2 {
      margin: 22px 0 10px;
      font-size: 1.25rem;
      letter-spacing: 0;
    }

    .analysis {
      padding: 14px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fbfcff;
      white-space: pre-wrap;
      line-height: 1.55;
    }

    .papers {
      display: grid;
      gap: 12px;
      margin-top: 12px;
    }

    .paper {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      background: #fff;
    }

    .paper h3 {
      margin: 0 0 8px;
      font-size: 1rem;
      line-height: 1.35;
    }

    .paper p {
      margin: 7px 0;
      color: var(--muted);
      line-height: 1.5;
    }

    a {
      color: var(--brand);
      text-decoration: none;
      font-weight: 700;
    }

    a:hover { text-decoration: underline; }

    @media (max-width: 760px) {
      main { width: min(100% - 24px, 1080px); padding-top: 28px; }
      form { grid-template-columns: 1fr; }
      button { width: 100%; }
      .meta-grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <main>
    <header>
      <h1>ArXiv Research Assistant</h1>
      <p class="subtitle">Enter a research topic and generate an interactive technical report with papers, analysis, Markdown output, and PDF output.</p>
    </header>

    <section class="search-panel">
      <form id="research-form">
        <div>
          <label for="query">Research query</label>
          <textarea id="query" name="query" placeholder="Example: preprocessing pipeline for STT and TTS voice agents" required></textarea>
        </div>
        <button id="submit-btn" type="submit">Run Research</button>
      </form>
      <div id="status" class="status"></div>
    </section>

    <section id="results" class="result-panel" aria-live="polite">
      <div class="meta-grid">
        <div class="meta">
          <span>Optimized query</span>
          <code id="optimized-query"></code>
        </div>
        <div class="meta">
          <span>Generated files</span>
          <div><a id="markdown-link" href="#" target="_blank" rel="noreferrer">Markdown report</a></div>
          <div><a id="pdf-link" href="#" target="_blank" rel="noreferrer">PDF report</a></div>
        </div>
      </div>

      <h2>Analysis</h2>
      <div id="analysis" class="analysis"></div>

      <h2>Retrieved Papers</h2>
      <div id="papers" class="papers"></div>
    </section>
  </main>

  <script>
    const form = document.querySelector("#research-form");
    const queryInput = document.querySelector("#query");
    const button = document.querySelector("#submit-btn");
    const statusBox = document.querySelector("#status");
    const results = document.querySelector("#results");
    const optimizedQuery = document.querySelector("#optimized-query");
    const markdownLink = document.querySelector("#markdown-link");
    const pdfLink = document.querySelector("#pdf-link");
    const analysis = document.querySelector("#analysis");
    const papers = document.querySelector("#papers");

    function setStatus(message, kind = "") {
      statusBox.textContent = message;
      statusBox.className = `status ${kind}`.trim();
    }

    function fileUrl(path) {
      return `/files/${encodeURIComponent(path)}`;
    }

    function renderPapers(items) {
      papers.innerHTML = "";
      items.forEach((paper, index) => {
        const article = document.createElement("article");
        article.className = "paper";

        const title = document.createElement("h3");
        title.textContent = `${index + 1}. ${paper.title}`;

        const authors = document.createElement("p");
        authors.textContent = `Authors: ${paper.authors.join(", ")}`;

        const published = document.createElement("p");
        published.textContent = `Published: ${paper.published} | Categories: ${paper.categories.join(", ")}`;

        const summary = document.createElement("p");
        summary.textContent = paper.summary;

        const link = document.createElement("a");
        link.href = paper.pdf_url;
        link.target = "_blank";
        link.rel = "noreferrer";
        link.textContent = "Open paper PDF";

        article.append(title, authors, published, summary, link);
        papers.appendChild(article);
      });
    }

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const query = queryInput.value.trim();
      if (!query) {
        setStatus("Please enter a research query.", "error");
        return;
      }

      button.disabled = true;
      button.textContent = "Researching...";
      results.classList.remove("visible");
      setStatus("Searching ArXiv and generating the report. This can take a little while.");

      try {
        const response = await fetch("/research", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query })
        });
        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.detail || "Research failed.");
        }

        optimizedQuery.textContent = data.optimized_query;
        markdownLink.href = fileUrl(data.report_path);
        pdfLink.href = fileUrl(data.pdf_path);
        analysis.textContent = data.analysis;
        renderPapers(data.papers);
        results.classList.add("visible");
        setStatus("Research complete.", "done");
      } catch (error) {
        setStatus(error.message, "error");
      } finally {
        button.disabled = false;
        button.textContent = "Run Research";
      }
    });
  </script>
</body>
</html>
"""


class ResearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Research query or topic")


class Paper(BaseModel):
    title: str
    authors: List[str]
    summary: str
    published: str
    pdf_url: str
    categories: List[str]
    entry_id: str


class ResearchResponse(BaseModel):
    query: str
    optimized_query: str
    papers: List[Paper]
    analysis: str
    report_path: str
    pdf_path: str


@app.get("/", response_class=HTMLResponse)
async def home():
    return HOME_HTML


async def run_research(query: str) -> Dict[str, Any]:
    query = query.strip()
    if not query:
        raise InvalidResearchRequest("Please provide a research query.")

    initial_state = {
        "query": query,
        "optimized_query": "",
        "papers": [],
        "analysis": "",
        "report_path": "",
        "pdf_path": "",
    }

    return await research_assistant.ainvoke(initial_state)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


def get_report_path(file_path: str) -> Path:
    path = Path(file_path)
    if path.is_absolute() or ".." in path.parts:
        raise HTTPException(status_code=400, detail="Invalid file path.")

    output_dir = Path(os.getenv("REPORT_OUTPUT_DIR", "/tmp" if os.getenv("VERCEL") else "."))
    return output_dir / path.name


@app.get("/files/{file_path:path}")
async def get_report_file(file_path: str):
    resolved = get_report_path(file_path)
    if resolved.suffix.lower() not in {".md", ".pdf"}:
        raise HTTPException(status_code=403, detail="Only report files can be opened.")

    if not resolved.is_file():
        raise HTTPException(status_code=404, detail="File not found.")

    return FileResponse(resolved)


@app.post("/research", response_model=ResearchResponse)
async def research(request: ResearchRequest):
    try:
        return await run_research(request.query)
    except InvalidResearchRequest as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
