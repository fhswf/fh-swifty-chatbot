from langchain_tavily import TavilySearch
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
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

    browser_conf = BrowserConfig(headless=True, browser_mode="builtin")
    
    # Crawl the FH Südwestfalen website and get the content
    async with AsyncWebCrawler(config=browser_conf) as crawler:
        js_code = [
                "const loadMoreButton = Array.from(document.querySelectorAll('button')).find(button => button.textContent.toLowerCase().includes('mehr')); loadMoreButton && loadMoreButton.click();"
        ]
        config = CrawlerRunConfig(
                cache_mode=CacheMode.ENABLED,
                js_code=js_code,
                excluded_tags=["header", "footer"],
            )
        contents = await crawler.arun_many(
            urls=[result['url'] for result in results['results']],
            config=config,
        )

    # Return the content of the FH Südwestfalen website
    final_results = [
        {
            'url': result['url'],
            #'content': result['content'],
            'raw_content': [content for content in contents if content.url == result['url']][0].markdown,
        }
        for result in results['results']
    ]

    print(f"Found {len(final_results[0])} results")
    print(final_results[0]['url'])

    return json.dumps(final_results, indent=2)