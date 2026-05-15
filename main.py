import argparse
import asyncio
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from graph import research_assistant


class InvalidResearchRequest(ValueError):
    pass


app = FastAPI(
    title="ArXiv Research Assistant API",
    description="Research a topic on ArXiv and generate Markdown/PDF reports.",
    version="1.0.0",
)


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


@app.post("/research", response_model=ResearchResponse)
async def research(request: ResearchRequest):
    try:
        return await run_research(request.query)
    except InvalidResearchRequest as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


async def run_assistant(query: str):
    print(f"\nStarting ArXiv Research Assistant for: '{query}'\n")

    try:
        final_state = await run_research(query)
        print("\nResearch complete.")
        print(f"Markdown Report: {final_state['report_path']}")
        print(f"PDF Report: {final_state['pdf_path']}")
    except Exception as exc:
        print(f"\nError during research: {exc}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ArXiv Research Assistant")
    parser.add_argument("query", type=str, help="Research query or topic")

    args = parser.parse_args()
    asyncio.run(run_assistant(args.query))
