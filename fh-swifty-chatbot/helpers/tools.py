from langchain_tavily import TavilySearch
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.tools import tool
import json
import chainlit as cl

@tool
@cl.step(type="tool", name="🔍 Suche auf FH-Website")
async def find_info_on_fhswf_website(query: str) -> str:
    """Find information on the FH Südwestfalen website."""
    current_step = cl.context.current_step
    
    # Set the input to show what we're searching for
    if current_step:
        current_step.input = f"Suche nach: {query}"
    
    print(f"Searching for: FH swf {query} - on the FH Südwestfalen website")

    # Search for the query on the FH Südwestfalen website
    tool = TavilySearch(
        max_results=3,
        include_domains=["fh-swf.de"],
    )
    
    # Update step to show search phase
    if current_step:
        current_step.output = "Durchsuche FH-Website nach relevanten Informationen..."
    
    results = tool.invoke({"query": "FH swf " + query})
    urls=[result['url'] for result in results['results']]
    
    # Update step to show loading phase
    if current_step:
        current_step.output = f"Lade Inhalte von {len(urls)} gefundenen Seiten..."
    
    loader = WebBaseLoader(urls)
    contents = loader.load()

    # Return the content of the FH Südwestfalen website
    final_results = [content.model_dump() for content in contents]

    print(f"Found {len(final_results[0])} results")
    print(final_results[0]['metadata']['source'])

    # Set final output to show completion
    if current_step:
        found_sources = [result.get('metadata', {}).get('source', 'Unknown') for result in final_results]
        sources_text = "\n".join([f"- {source}" for source in found_sources[:3]])
        current_step.output = f"✅ {len(final_results)} Seite(n) geladen:\n{sources_text}"

    return json.dumps(final_results, indent=2)