import argparse
import asyncio

from api.index import run_research


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
