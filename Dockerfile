FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install system dependencies required for Playwright Chromium
RUN apt-get update && apt-get install -y \
    libglib2.0-0 libgobject-2.0-0 libnspr4 \
    libnss3 libnss3-dev \
    libgio-2.0-0 libdbus-1-3 libatk1.0-0 \
    libatk-bridge2.0-0 libcups2 libexpat1 \
    libxcb1 libxkbcommon0 libatspi2.0-0 \
    libx11-6 libxcomposite1 libxdamage1 \
    libxext6 libxfixes3 libxrandr2 \
    libgbm1 libcairo2 libpango-1.0-0 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml /app
RUN uv sync
RUN uv run playwright install chromium
COPY . /app
RUN uv pip install -e .
EXPOSE 8000
CMD ["uv", "run", "chainlit", "run", "fh-swifty-chatbot/agent_langgraph_app.py", "--host", "0.0.0.0"]