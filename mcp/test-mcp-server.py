from fastmcp import FastMCP
from typing import Literal
mcp = FastMCP("Demo 🚀")

@mcp.tool
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

@mcp.tool
def get_weather(city: Literal["isernlohn", "duisburg", "essen"]) -> str:
    """Get the weather of a city"""
    return f"The weather of {city} is sunny"


if __name__ == "__main__":
    mcp.run(transport="http", port=8001)