FROM python:3.14-slim

EXPOSE 8000

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Keeps Python from generating .pyc files in the container
# Turns off buffering for easier container logging
ENV PYTHONDONTWRITEBYTECODE=1 \
PYTHONUNBUFFERED=1 \
PYTHONHASHSEED=random \
UV_NO_CACHE=1 \
UV_COMPILE_BYTECODE=1 \
UV_SYSTEM_PYTHON=1 

WORKDIR /app
COPY . /app

# Install the application dependencies.
RUN uv sync --frozen --no-dev --no-cache

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

CMD ["uv", "run", "serve.py"]
