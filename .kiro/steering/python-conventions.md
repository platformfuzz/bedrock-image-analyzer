# Python Conventions

## Module Layout

- Single `main.py` application file at repository root
- No nested package structure — the app module is `main`
- Tests in `tests/` directory with `conftest.py` for shared fixtures

## Framework

- **FastAPI** for the HTTP API with automatic OpenAPI documentation
- **Pydantic** BaseModel for request/response validation
- **boto3** for AWS Bedrock client
- **uvicorn** as the ASGI server

## Coding Standards

- All functions and methods include type annotations
- Docstrings on all public classes, functions, and modules
- Use stdlib `logging` module (no print statements)
- Constants in UPPER_SNAKE_CASE at module level
- Use `json.dumps()` / `json.loads()` for JSON serialization

## Dependencies

- Runtime dependencies in `requirements.txt` (kept minimal for container size)
- Dev/test dependencies in `requirements-dev.txt`
- No version pins in requirements files (upstream CI validates compatibility)

## Testing

- **pytest** as the test runner
- **Hypothesis** for property-based tests (min 100 examples per property)
- **FastAPI TestClient** for HTTP endpoint testing
- Mock external services (Bedrock) using `unittest.mock.patch`
- Patch target is `main.bedrock_client` (module-level client instance)
- Tests organized by behavior, not by function

## Linting

- **Ruff** for linting and import sorting
- Default ruff rules (no custom configuration needed)
- Run with `ruff check .`

## Dockerfile Conventions

- Base image: `python:3.14-slim`
- Non-root user (`appuser`) for runtime
- Layer optimization: COPY requirements.txt and pip install before COPY . .
- Expose port 8000
- CMD uses uvicorn with explicit host 0.0.0.0
- `.dockerignore` excludes tests, CI, and dev files from the image
