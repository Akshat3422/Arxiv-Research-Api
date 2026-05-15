import os
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
from utils import fetch_arxiv_papers, generate_markdown_report, export_to_pdf

load_dotenv()


# Define the state for the research assistant
class ResearchState(TypedDict):
    query: str
    optimized_query: str
    papers: List[Dict[str, Any]]
    analysis: str
    report_path: str
    pdf_path: str


# 1. Query Optimization Node
async def optimize_query_node(state: ResearchState):
    query = state["query"]
    # Default to Groq if available, fallback to OpenAI or error out if neither
    if os.getenv("GROQ_API_KEY"):
        llm = ChatGroq(model="llama-3.3-70b-versatile")
    else:
        raise ValueError("Missing API key for GROQ or OPENAI")

    system_msg = (
        "You are an expert research librarian. Your task is to optimize the user's research query for ArXiv search. "
        "Expand technical keywords, add domain-specific terminology, and improve semantic search quality. "
        "Return ONLY the optimized search query as a single string, with no additional text or explanation."
    )
    human_msg = f"Original query: {query}"

    response = await llm.ainvoke(
        [SystemMessage(content=system_msg), HumanMessage(content=human_msg)]
    )
    optimized = response.content.strip()
    # Clean up any quotes the LLM might have added
    optimized = optimized.strip('"').strip("'")

    print(f"--- Optimized Query: {optimized} ---")
    return {"optimized_query": optimized}


# 2. ArXiv Retrieval Node
async def retrieve_papers_node(state: ResearchState):
    optimized_query = state["optimized_query"]
    print(f"--- Fetching papers for: {optimized_query} ---")
    papers = await fetch_arxiv_papers(optimized_query, max_results=8)
    print(f"--- Found {len(papers)} papers ---")
    return {"papers": papers}


# 3. Processing & Output Node
async def process_papers_node(state: ResearchState):
    papers = state["papers"]
    query = state["query"]

    if not papers:
        return {"analysis": "No relevant papers were found on ArXiv for this query."}

    if os.getenv("GROQ_API_KEY"):
        llm = ChatGroq(model="llama-3.3-70b-versatile")
    else:
        raise ValueError("Missing API key for GROQ")
    context = ""
    for i, p in enumerate(papers, 1):
        context += f"Paper {i}:\nTitle: {p['title']}\nAbstract: {p['summary']}\n\n"

    system_msg = (
        "You are a senior speech AI research analyst. Produce a deep technical literature review, not a surface summary. "
        "Analyze the following ArXiv paper abstracts against the user's objective. "
        "For every relevant paper, extract the concrete pipeline stages, model architecture choices, preprocessing features, "
        "training or adaptation strategy, evaluation signals, strengths, weaknesses, and assumptions. "
        "Compare papers across STT, TTS, voice conversion, speech enhancement, VAD/endpointing, speaker conditioning, "
        "prosody modeling, latency, robustness, and deployment constraints for voice agents. "
        "Make clear where a claim is directly supported by the abstract and where it is an engineering implication. "
        "Include: an executive synthesis, topic clusters, per-paper technical notes, cross-paper comparison, "
        "practical design recommendations for a voice-agent preprocessing pipeline, open research gaps, and a short reading priority list. "
        "Use clear Markdown headings, dense but readable bullets, and avoid generic filler."
    )
    human_msg = f"User Research Objective: {query}\n\nRetrieved Papers:\n{context}"

    print("--- Analyzing papers ---")
    response = await llm.ainvoke(
        [SystemMessage(content=system_msg), HumanMessage(content=human_msg)]
    )
    return {"analysis": response.content}


# 4. Document Generation Node
async def generate_document_node(state: ResearchState):
    query = state["query"]
    optimized_query = state["optimized_query"]
    papers = state["papers"]
    analysis = state["analysis"]

    print("--- Generating research report ---")
    report_md = generate_markdown_report(query, optimized_query, papers, analysis)

    # Create filename from query
    safe_query = "".join([c if c.isalnum() else "_" for c in query])
    file_path = f"research_report_{safe_query[:50]}.md"
    pdf_path = f"research_report_{safe_query[:50]}.pdf"

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(report_md)

    print(f"--- Exporting to PDF ---")
    export_to_pdf(query, analysis, papers, pdf_path)

    print(f"--- Reports generated: {file_path}, {pdf_path} ---")
    return {"report_path": file_path, "pdf_path": pdf_path}


# Build the LangGraph workflow
workflow = StateGraph(ResearchState)

# Add nodes
workflow.add_node("optimize_query", optimize_query_node)
workflow.add_node("retrieve_papers", retrieve_papers_node)
workflow.add_node("process_papers", process_papers_node)
workflow.add_node("generate_document", generate_document_node)

# Add edges
workflow.set_entry_point("optimize_query")
workflow.add_edge("optimize_query", "retrieve_papers")
workflow.add_edge("retrieve_papers", "process_papers")
workflow.add_edge("process_papers", "generate_document")
workflow.add_edge("generate_document", END)

# Compile the app
research_assistant = workflow.compile()
