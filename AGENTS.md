# AGENTS.md

This file provides guidance to Any CodeAgents when working with code in this repository.

## Project Overview

Agent Quant is a trading agent system that integrates LLMs to generate trading signals based on market data analysis. The system fetches stock market data, builds prompts for AI agents, receives trading signals, and executes virtual trades with performance analysis.

**Key Languages**: Python 3.14
**Package Manager**: uv
**Framework**: FastAPI

## Essential Commands

```bash
# Install dependencies
uv sync

# Run development server
uv run serve.py

# Lint and auto-fix code
uv run ruff check --fix

# Run tests
uv run pytest

# Run specific test file
uv run pytest tests/api/routes/test_auth.py

# Apply database migrations (if alembic migrations are configured)
uv run alembic upgrade head
```

## Architecture

### Module Hierarchy

The application follows a modular architecture with clear separation of concerns:

- **`app/main.py`**: FastAPI application entry point, initializes AgentOS, mounts routes/middleware/exception handlers
- **`app/core/`**: Configuration (`config.py`), database sessions (`db.py`), dependencies (`deps.py`), initialization logic (`init_data.py`)
- **`app/api/`**: HTTP API endpoints organized by feature in `routes/` subdirectories
- **`app/models/`**: SQLModel database entities and Pydantic validation models
- **`app/scheduler/`**: Background task management using APScheduler (jobs definition and registry)
- **`app/utils/`**: Cross-cutting utilities (responses, exceptions, logging, calculators)

### Model Structure

All database models follow a three-layer pattern:

- `*Base`: Common fields shared across all model variants
- Entity (`table=True`): SQLModel database table definition
- `Create`/`Update`/`Read`: Pydantic validation models

Example reference: `app/models/post.py`

## Development Guidelines

### Code Standards

- **Language**: All responses and documentation in Chinese
- **Linting**: Ruff with line length 100, auto-fix enabled
- **Imports**: Organized with isort; **no longer** require `from __future__ import annotations` (leverages Python 3.14 PEP 649 deferred evaluation)
- **Design**: Keep code simple and practical, avoid over-engineering
- **Complexity**: Minimize cyclomatic complexity, maximize code reuse
- **Modifications**: Minimize changes to unrelated modules

### Testing

- Framework: pytest with async support
- Database: SQLite for isolated testing via `tests/conftest.py`
- Fixtures: Use existing `test_user` fixture, extend factories for test data
- Authentication: Use `tests/utils/auth.py` for JWT-based auth testing
- Markers: Integration tests marked with `@pytest.mark.integration`

### API Development

- Responses must use envelope pattern: `app/utils/responses.py`
- Business exceptions inherit from `app/utils/exceptions.py`
- Dependencies injected via `app/core/deps.py`
- New routes added to `app/api/routes/` and registered in `app/api/__init__.py`

### Scheduler Development

- Framework: APScheduler (`AsyncIOScheduler`)
- Lifecycle: Started within `app/main.py` lifespan context
- Configuration: Tasks defined in `app/scheduler/jobs.py`

### Database Migrations

- Alembic configured with SQLModel
- New models must inherit from `app/models/base_model.py`
- Table names use singular form of entity name

### Environment Configuration

- Copy `.env.example` to `.env` for local development
- Update all three: `.env`, `.env.example`, and `app/core/config.py`
- Secrets should never be committed to version control

## Important Patterns

### Dependency Injection

All shared dependencies (DB sessions, auth) are centralized in `app/core/deps.py` and injected into route handlers.

### Response Standardization

All API responses use the envelope pattern:

```python
from app.utils.responses import success_response, error_response
```

### Logging

Centralized Loguru configuration in `app/utils/logging.py` with request logging middleware.

### Exception Handling

Custom exceptions inherit from base classes in `app/utils/exceptions.py` and are automatically converted to standardized responses.
