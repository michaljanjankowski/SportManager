FROM ghcr.io/astral-sh/uv:0.12.15 AS uv
FROM python:3.12-slim-bookworm

COPY --from=uv /uv /usr/local/bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_PYTHON_DOWNLOADS=never \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-dev --no-cache

RUN useradd --create-home --uid 10001 app
COPY . .
USER app

EXPOSE 8000
ENTRYPOINT ["sh", "/app/docker/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
