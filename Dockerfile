FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
COPY pyproject.toml /app
RUN uv sync --no-dev
COPY . /app
RUN uv pip install -e .
EXPOSE 8000
CMD ["uv", "run", "chainlit", "run", "fh-swifty-chatbot/agent_langgraph_app.py", "--host", "0.0.0.0"]