from langchain_tavily import TavilySearch
from langchain_community.document_loaders import SeleniumURLLoader
from langchain_core.tools import tool
import json
import chainlit as cl

@tool
@cl.step(type="tool")
async def find_info_on_fhswf_website(query: str) -> str:
    """Find information on the FH Südwestfalen website."""
    print(f"Searching for: FH swf {query} - on the FH Südwestfalen website")

    # Search for the query on the FH Südwestfalen website
    tool = TavilySearch(
        max_results=3,
        include_domains=["fh-swf.de"],
    )
    results = tool.invoke({"query": "FH swf " + query})
    urls=[result['url'] for result in results['results']]
    loader = SeleniumURLLoader(urls)
    contents = loader.load()

    # Return the content of the FH Südwestfalen website
    final_results = [content.model_dump() for content in contents]

    print(f"Found {len(final_results[0])} results")
    print(final_results[0]['metadata']['source'])

    return json.dumps(final_results, indent=2)