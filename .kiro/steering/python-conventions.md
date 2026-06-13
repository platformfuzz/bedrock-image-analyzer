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
- **`asynccontextmanager`** lifespan for startup validation hooks

## Application Patterns

- Module-level client instances (e.g., `bedrock_client = boto3.client(...)`)
- Environment variable configuration with defaults via `os.environ.get()`
- FastAPI lifespan context manager for startup checks (model availability validation)
- Helper functions prefixed with `_` for internal logic
- `JSONResponse` for non-2xx responses with custom status codes
- Prefix-based dispatch for Bedrock API selection (inference profiles vs foundation models)

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
- Patch targets: `main.bedrock_client`, `main.validate_model_availability`, `main.MODEL_ID`, `main._get_aws_region`, `main.boto3.client`
- Tests organized by behavior, not by function
- `conftest.py` sets `AWS_DEFAULT_REGION` env var before app import
- Unit tests for startup validation cover both foundation model and inference profile code paths

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
- `.dockerignore` excludes tests, CI, dev files, LICENSE, and cache directories from the image

## CI/CD Workflows

- `python-lint-test.yml` — Local workflow: ruff check + pytest (Python 3.14)
- `build-and-release.yml` — Docker build + push to GHCR on main/tags; GitHub Release on tag
- `ci.yml` — Docker build (no push) on PRs to validate Dockerfile
- `commitmsg-conform.yml` — Reusable workflow from actionsforge/actions
- `markdown-lint.yml` — Reusable workflow from actionsforge/actions
