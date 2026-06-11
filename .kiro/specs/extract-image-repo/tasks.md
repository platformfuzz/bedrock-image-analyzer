# Implementation Plan

## Overview

Extract the containerized FastAPI application from the source Terraform repository into this standalone repository (`bedrock-image-analyzer-image`). Create all application files, tests, CI workflows, Kiro configuration, and documentation. Then clean up the source repository by removing the embedded application code.

## Tasks

- [x] 1. Create target repository core application files
  - [x] 1.1. Create `main.py` — copy from source repo `app/main.py` (no changes needed)
  - [x] 1.2. Create `requirements.txt` — copy from source repo `app/requirements.txt` (no changes needed)
  - [x] 1.3. Create `Dockerfile` — copy from source repo `app/Dockerfile` (no changes needed, COPY . . already works with flat layout)
  - [x] 1.4. Create `.dockerignore` — exclude tests/, .github/, .kiro/, .gitignore, requirements-dev.txt, README.md, .hypothesis/, __pycache__/
  - [x] 1.5. Create `requirements-dev.txt` — pytest, hypothesis, httpx, ruff

- [x] 2. Create target repository tests with adapted imports
  - [x] 2.1. Create `tests/__init__.py` — empty package marker
  - [x] 2.2. Create `tests/conftest.py` — adapted from source, patch "main.bedrock_client" and import "from main import app"
  - [x] 2.3. Create `tests/test_app.py` — copy from source (no changes needed, uses fixtures from conftest)

- [x] 3. Create GitHub Actions workflows
  - [x] 3.1. Create `.github/workflows/commitmsg-conform.yml` — reusable workflow from actionsforge/actions on pull_request
  - [x] 3.2. Create `.github/workflows/markdown-lint.yml` — reusable workflow from actionsforge/actions on push and pull_request
  - [x] 3.3. Create `.github/workflows/python-lint-test.yml` — local workflow: Python 3.14, install deps, ruff check, pytest tests/ -v

- [x] 4. Create Kiro steering files
  - [x] 4.1. Create `.kiro/steering/domain-context.md` — describe the image analyzer application purpose, endpoints, architecture, error model, runtime environment
  - [x] 4.2. Create `.kiro/steering/python-conventions.md` — describe module layout, framework, logging, type hints, dependencies, testing, linting, Dockerfile conventions

- [x] 5. Create repository documentation and metadata
  - [x] 5.1. Create `README.md` — document project purpose, prerequisites, local development, Docker build, testing, API endpoints, project structure
  - [x] 5.2. Create `.gitignore` — Python-specific ignores
  - [x] 5.3. Create `LICENSE` — MIT license attributed to John Ajera

- [x] 6. Remove application from source repository
  - [x] 6.1. Delete `app/` directory from source repo
  - [x] 6.2. Delete `tests/test_app.py` from source repo
  - [x] 6.3. Delete `tests/conftest.py` from source repo
  - [x] 6.4. Update `ecr.tf` — remove `null_resource.docker_build_push` resource; keep ECR repository and lifecycle policy
  - [x] 6.5. Update source repo `README.md` — remove app/ references, note image is built externally
  - [x] 6.6. Update source repo `.gitignore` — remove Python-specific entries

## Task Dependency Graph

```
Task 1 → Task 2
Task 1 → Task 6
Task 2 → Task 6
Task 3 → Task 6
Task 4 → Task 6
Task 5 → Task 6
```

## Notes

- Tasks 1, 3, 4, and 5 have no dependencies and can run in parallel.
- Task 2 depends on Task 1 (tests import from main.py).
- Task 6 depends on all other tasks (cleanup only after extraction is complete).
- The source repo is at `/home/johna/workspace/jajera/terraform-aws-ecs-express-mode-demo`.
