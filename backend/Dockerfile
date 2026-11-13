# One image for the API, the Celery worker and Celery beat; compose chooses the command.

# --- build: install the locked dependencies into a virtualenv ----------------
FROM python:3.12.16-slim-trixie AS build
COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /bin/uv
# Compile .pyc now so containers start faster. Copy files instead of hard-linking them,
# because the virtualenv is copied to the next stage. Use the image's Python, never a download.
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /app
# Only the dependency files: this layer stays cached until uv.lock changes.
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --locked --no-dev

# --- runtime: no uv, no build cache, not root --------------------------------
FROM python:3.12.16-slim-trixie
RUN useradd --system --no-create-home --uid 10001 app
WORKDIR /app
COPY --from=build /app/.venv /app/.venv
# Owned by root (COPY's default): "app" can read the code but not change it.
COPY . .
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=config.settings.prod
USER app
EXPOSE 8000
CMD ["sh", "docker/start-api.sh"]
