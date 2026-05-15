import arxiv
import asyncio
import re
from html import escape
from typing import List, Dict, Any
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer


async def fetch_arxiv_papers(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Asynchronously fetch papers from ArXiv.
    """
    client = arxiv.Client()
    search = arxiv.Search(
        query=query, max_results=max_results, sort_by=arxiv.SortCriterion.Relevance
    )

    loop = asyncio.get_event_loop()

    def get_results():
        return list(client.results(search))

    # Run the synchronous arxiv library call in a thread pool
    papers = await loop.run_in_executor(None, get_results)

    results = []
    for paper in papers:
        results.append(
            {
                "title": paper.title,
                "authors": [author.name for author in paper.authors],
                "summary": paper.summary,
                "published": paper.published.strftime("%Y-%m-%d"),
                "pdf_url": paper.pdf_url,
                "categories": paper.categories,
                "entry_id": paper.entry_id,
            }
        )
    return results


def generate_markdown_report(
    query: str, optimized_query: str, papers: List[Dict[str, Any]], analysis: str
) -> str:
    """
    Generate a structured Markdown report.
    """
    report = f"# ArXiv Research Report: {query}\n\n"
    report += f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    report += f"**Optimized Query:** `{optimized_query}`\n\n"

    report += "## Research Summary\n"
    report += f"{analysis}\n\n"

    report += "## Retrieved Papers\n\n"
    for i, paper in enumerate(papers, 1):
        report += f"### {i}. {paper['title']}\n"
        report += f"- **Authors:** {', '.join(paper['authors'])}\n"
        report += f"- **Published:** {paper['published']}\n"
        report += f"- **Categories:** {', '.join(paper['categories'])}\n"
        report += f"- **PDF:** [{paper['pdf_url']}]({paper['pdf_url']})\n\n"
        report += f"**Abstract:**\n{paper['summary']}\n\n"
        report += "---\n\n"

    report += "## References\n"
    for paper in papers:
        report += f"- {paper['title']}. Available at: {paper['pdf_url']}\n"

    return report


def markdown_to_reportlab_html(text: str) -> str:
    """
    Convert a small, safe subset of Markdown to ReportLab Paragraph markup.
    """
    escaped = escape(text)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)
    escaped = re.sub(r"__(.+?)__", r"<b>\1</b>", escaped)
    return escaped.replace("\n", "<br/>")


def export_to_pdf(
    query: str, analysis: str, papers: List[Dict[str, Any]], filename: str
):
    """
    Export the research summary to a PDF file.
    """
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph(escape(f"ArXiv Research Report: {query}"), styles["Title"]))
    story.append(Spacer(1, 12))

    # Analysis
    story.append(Paragraph("Research Summary", styles["Heading2"]))
    clean_analysis = markdown_to_reportlab_html(analysis)
    story.append(Paragraph(clean_analysis, styles["Normal"]))
    story.append(Spacer(1, 12))

    # Papers
    story.append(Paragraph("Retrieved Papers", styles["Heading2"]))
    for paper in papers:
        story.append(Paragraph(f"<b>{escape(paper['title'])}</b>", styles["Normal"]))
        story.append(
            Paragraph(
                escape(f"Authors: {', '.join(paper['authors'])}"),
                styles["Italic"],
            )
        )
        pdf_url = escape(paper["pdf_url"], quote=True)
        story.append(
            Paragraph(
                f"Link: <a href='{pdf_url}'>{pdf_url}</a>",
                styles["Normal"],
            )
        )
        story.append(
            Paragraph(
                markdown_to_reportlab_html(f"Abstract: {paper['summary']}"),
                styles["Normal"],
            )
        )
        story.append(Spacer(1, 6))

    doc.build(story)
