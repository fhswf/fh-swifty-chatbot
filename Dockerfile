FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
COPY pyproject.toml /app
RUN uv sync
COPY . /app
RUN uv pip install -e .
EXPOSE 8000
CMD ["uv", "run", "fastapi", "run", "api/main_pydantic.py"]