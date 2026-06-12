# Design: Extract Image Repository

## Overview

This design describes extracting the container application (FastAPI image analyzer) from the monolithic Terraform repository (`terraform-aws-ecs-express-mode-demo`) into a dedicated standalone repository (`bedrock-image-analyzer`). The new repository is focused solely on the container image: its source code, tests, CI linting, and Kiro steering files. The Terraform repo retains all infrastructure code but removes the application source and app-related tests.

---

## 1. Target Repository File Layout

The `bedrock-image-analyzer` repository uses a flat layout with application files at the repo root (not nested in an `app/` subdirectory). This matches the Dockerfile's `WORKDIR /app` + `COPY . .` pattern — the Docker build context is the repo root.

```text
bedrock-image-analyzer/
├── main.py                         # FastAPI application (from app/main.py)
├── requirements.txt                # Runtime dependencies (from app/requirements.txt)
├── requirements-dev.txt            # Test/lint dependencies (new)
├── Dockerfile                      # Container build (from app/Dockerfile, unchanged)
├── .gitignore                      # Python-specific ignores (new)
├── README.md                       # Repository documentation (new)
├── tests/
│   ├── __init__.py                 # Package marker
│   ├── conftest.py                 # Shared fixtures (adapted imports)
│   ├── test_app.py                 # Property-based tests for /analyze endpoint
│   └── test_validation.py          # Property-based tests for input validation
├── .github/
│   └── workflows/
│       └── python-lint-test.yml    # CI: lint + test (new, local workflow)
└── .kiro/
    ├── specs/
    │   └── extract-image-repo/
    │       ├── requirements.md
    │       ├── design.md           # This document
    │       └── tasks.md
    └── steering/
        ├── domain-context.md       # Application domain and architecture
        └── python-conventions.md   # Coding standards for the Python app
```

### Design Decisions

- **Flat root layout**: `main.py`, `requirements.txt`, and `Dockerfile` live at repo root. The Dockerfile already uses `COPY . .` relative to its build context, so no path changes are needed inside the Dockerfile.
- **No `app/` subdirectory**: Eliminates the `app.main` module path. Tests import directly from `main`.
- **`requirements-dev.txt`**: Separates test/lint tooling from runtime dependencies to keep the production image lean.
- **`test_terraform_structure.py` excluded**: This test validates Terraform file structure and has no relevance in the image repo.

---

## 2. GitHub Actions Design

### Workflow: `.github/workflows/python-lint-test.yml`

A local workflow (not a reusable workflow from actionsforge) since the linting and testing configuration is specific to this Python project.

```yaml
name: Python Lint and Test

on:
  push:
  pull_request:

jobs:
  lint-and-test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.14"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Lint with ruff
        run: ruff check .

      - name: Run tests
        run: pytest tests/ -v
```

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| Python 3.14 | Matches the `python:3.14-slim` base image in the Dockerfile |
| Ruff for linting | Modern, fast Python linter/formatter; single tool replaces flake8+isort+black |
| Local workflow | Project-specific lint/test config doesn't fit a generic reusable workflow |
| Both requirements files installed | Tests need runtime deps (fastapi, boto3) plus dev deps (pytest, hypothesis) |
| `pytest tests/ -v` | Explicit test directory, verbose output for CI readability |

### `requirements-dev.txt` Contents

```text
pytest
hypothesis
httpx
ruff
```

- **pytest** — Test runner
- **hypothesis** — Property-based testing (used in test_app.py and test_validation.py)
- **httpx** — Required by FastAPI's TestClient (ASGI transport)
- **ruff** — Linter and formatter

---

## 3. Kiro Steering Files

### `.kiro/steering/domain-context.md`

Covers the application domain for the standalone image repo:

- **Project purpose**: Standalone container image for AI-powered image analysis using Amazon Bedrock
- **Architecture**: FastAPI app → Bedrock Claude 3 Sonnet
- **API endpoints**: POST /analyze, GET /health
- **Error model**: 422 for invalid URLs, 502 for Bedrock failures
- **Runtime environment**: ECS Fargate via the separate Terraform repo
- **File structure**: Flat layout description of the image repo

### `.kiro/steering/python-conventions.md`

Covers Python coding standards specific to this project:

- **Module layout**: Single `main.py` application file at repo root
- **Framework**: FastAPI with Pydantic models for request/response validation
- **Logging**: stdlib `logging` module, no print statements
- **Type hints**: All function signatures use type annotations
- **Dependencies**: Runtime in `requirements.txt`, dev in `requirements-dev.txt`
- **Testing**: pytest + hypothesis for property-based tests, TestClient for HTTP
- **Linting**: Ruff with default rules
- **Dockerfile conventions**: Non-root user, slim base image, COPY-after-pip-install layer caching

---

## 4. Test Module Adaptation

The tests move from `tests/` in the source repo to `tests/` in the new repo. The key change is that `main.py` is now at repo root, so the module is `main` (not `app.main`).

### Import Path Changes

| File | Before (source repo) | After (image repo) |
|------|---------------------|-------------------|
| `conftest.py` | `patch("app.main.bedrock_client", ...)` | `patch("main.bedrock_client", ...)` |
| `conftest.py` | `from app.main import app` | `from main import app` |
| `test_app.py` | No direct imports of app module | No changes needed |
| `test_validation.py` | No imports of app module (tests regex patterns) | No changes needed |

### `conftest.py` — Adapted Version

```python
"""Shared test fixtures for the container application tests."""

import json
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def mock_bedrock_client():
    """Provide a mock Bedrock runtime client."""
    mock_client = MagicMock()
    default_response_body = json.dumps(
        {"content": [{"text": "A sample image description from Bedrock."}]}
    )
    mock_client.invoke_model.return_value = {
        "body": BytesIO(default_response_body.encode("utf-8"))
    }
    return mock_client


@pytest.fixture
def client(mock_bedrock_client):
    """Provide a FastAPI TestClient with the mock Bedrock client injected."""
    with patch("main.bedrock_client", mock_bedrock_client):
        from main import app

        with TestClient(app) as test_client:
            yield test_client
```

### Files Excluded from the Image Repo

- **`test_terraform_structure.py`** — Validates `.tf` files, IAM roles, outputs, workflows, and README sections specific to the Terraform repo. Not relevant to the image repo.

### Files Included (Unchanged Logic)

- **`test_app.py`** — Property-based tests for invalid URL rejection. Uses the `client` and `mock_bedrock_client` fixtures from conftest. No direct app imports, so no changes required.
- **`test_validation.py`** — Property-based tests for regex patterns (project name, AWS region). These test pure regex logic with no app imports, so no changes required.

---

## 5. Source Repo Cleanup

After extraction, the Terraform repository (`terraform-aws-ecs-express-mode-demo`) needs the following changes:

### Files/Directories to Delete

| Path | Reason |
|------|--------|
| `app/main.py` | Moved to image repo |
| `app/requirements.txt` | Moved to image repo |
| `app/Dockerfile` | Moved to image repo |
| `app/` (directory) | Empty after file removal |
| `tests/test_app.py` | Moved to image repo (app-specific tests) |
| `tests/test_validation.py` | Moved to image repo (validates app input patterns) |
| `tests/conftest.py` | Moved to image repo (app test fixtures) |

### Files to Update

| File | Change |
|------|--------|
| `ecr.tf` | Update `null_resource.docker_build_push` — remove or update the `app_hash` trigger and `docker build` path since the app source no longer lives in this repo. The ECR resource and lifecycle policy remain. |
| `README.md` | Remove the `app/` section from "Project Structure". Update description to note the container image is built from a separate repository. |
| `.gitignore` | Remove Python-specific entries (`__pycache__/`, `*.py[cod]`, `.venv/`, `.hypothesis/`) since Python code no longer lives here. |

### Files to Keep (Unchanged)

- All `.tf` files (except `ecr.tf` update above)
- `scripts/run.sh`
- `.github/workflows/` (all three existing workflows)
- `tests/test_terraform_structure.py` — Remains as it validates Terraform project structure
- `.kiro/` steering and spec files

### Consideration: `tests/` Directory After Cleanup

If `test_terraform_structure.py` remains as the only test file:
- Keep `tests/__init__.py` as the package marker
- The existing `.github/workflows/` do not run pytest (they run terraform fmt/validate), so no CI changes needed for the remaining test

---

## 6. Dockerfile

**No changes required.** The Dockerfile already works with the new flat layout:

```dockerfile
FROM python:3.14-slim

RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

The `COPY . .` copies from the Docker build context (repo root) into `/app`. Since `main.py` and `requirements.txt` are at repo root, and the CMD references `main:app`, all relative paths remain valid.

A `.dockerignore` should be created to exclude test and CI files from the image:

```text
tests/
.github/
.kiro/
.gitignore
requirements-dev.txt
README.md
.hypothesis/
__pycache__/
```

---

## Traceability Matrix

This matrix maps design components to the requirements they address. Requirement IDs reference the acceptance criteria in `requirements.md`.

| Design Section | Requirement IDs | Description |
|---------------|-----------------|-------------|
| 1. Target Repository File Layout | R1, R2 | Repository structure with flat layout, all source files at root |
| 2. GitHub Actions Design | R3 | CI workflow for linting (ruff) and testing (pytest + hypothesis) |
| 3. Kiro Steering Files | R4 | domain-context.md and python-conventions.md for the image repo |
| 4. Test Module Adaptation | R5 | Import path changes for flat layout (`main` instead of `app.main`) |
| 5. Source Repo Cleanup | R6 | Deletion of moved files, updates to ecr.tf and README |
| 6. Dockerfile | R7 | No changes needed — confirms compatibility with flat layout |

### Detailed Requirement Coverage

| Requirement | Design Component | How Addressed |
|-------------|-----------------|---------------|
| Application files at repo root | Section 1 | main.py, requirements.txt, Dockerfile at root (no app/ subdirectory) |
| requirements-dev.txt for test deps | Section 2 | pytest, hypothesis, httpx, ruff in separate dev requirements file |
| Python 3.14 in CI | Section 2 | Matches Dockerfile base image; set in setup-python action |
| Ruff for linting | Section 2 | Modern linter, replaces flake8/isort/black; configured in workflow |
| Local workflow (not reusable) | Section 2 | Project-specific; defined directly in python-lint-test.yml |
| Tests import from `main` module | Section 4 | conftest.py patches `main.bedrock_client`, imports `from main import app` |
| conftest.py patches `main.bedrock_client` | Section 4 | Mock path updated from `app.main.bedrock_client` to `main.bedrock_client` |
| test_terraform_structure.py excluded | Section 4, 5 | Stays in source repo; not relevant to image repo |
| Source repo app/ directory deleted | Section 5 | All three files moved, directory removed |
| ecr.tf updated | Section 5 | Docker build trigger and path updated for external image source |
| Dockerfile unchanged | Section 6 | COPY and CMD paths already compatible with flat layout |
| .dockerignore created | Section 6 | Excludes tests, CI, and dev files from production image |
