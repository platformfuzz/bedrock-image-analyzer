# Domain Context

## Project Purpose

This is a standalone container image repository for an AI-powered image analysis API. The application uses Amazon Bedrock Claude 3 Sonnet to analyze images provided via URL and return natural language descriptions. It is deployed as a container on AWS ECS Fargate, with infrastructure managed in a separate Terraform repository. Container images are published to GitHub Container Registry (GHCR) via automated workflows.

## Architecture

```text
Client → ALB (managed by ECS Express Mode) → ECS Fargate Task → FastAPI Container → Amazon Bedrock Claude
```

The container runs a Python FastAPI application that:
1. Validates model availability in the configured AWS region at startup
2. Receives image URLs via POST /analyze
3. Sends the image to Amazon Bedrock Claude 3 Sonnet for analysis
4. Returns the AI-generated description to the caller

## API Endpoints

- **POST /analyze** — Accepts `{"image_url": "https://..."}`, invokes Bedrock Claude, returns `{"image_url": "...", "description": "..."}`
- **GET /health** — Returns `{"status": "healthy"}` for load balancer health checks

## Error Model

- HTTP 422 for invalid/missing image URL (Pydantic HttpUrl validation)
- HTTP 502 when Bedrock invocation fails (network issues, model errors)
- HTTP 503 when the configured model is not available in the deployment AWS region

## Configuration

- `MODEL_ID` environment variable — Bedrock model identifier (default: `anthropic.claude-3-sonnet-20240229-v1:0`)
- `MAX_TOKENS` environment variable — Maximum tokens for model response (default: `1024`)
- `AWS_DEFAULT_REGION` — AWS region for Bedrock calls (resolved from boto3 session or environment)

## Startup Validation

The app uses a FastAPI lifespan context manager to validate model availability before serving requests. If the configured `MODEL_ID` is not available in the current AWS region, the app fails to start with a descriptive `RuntimeError`.

## Runtime Environment

- Container runs on AWS ECS Fargate (infrastructure in separate repo)
- Requires AWS credentials with `bedrock:InvokeModel` permission
- Model and region validated at startup via `bedrock:GetFoundationModel`
- Listens on port 8000 via uvicorn

## CI/CD Pipelines

- **python-lint-test.yml** — Lints with ruff and runs pytest on push/PR
- **build-and-release.yml** — Builds and pushes Docker image to GHCR on main branch push and version tags; creates GitHub Releases on tag push
- **ci.yml** — Builds Docker image (no push) on PRs to validate Dockerfile
- **commitmsg-conform.yml** — Validates commit messages on PRs (reusable workflow)
- **markdown-lint.yml** — Lints markdown on push/PR (reusable workflow)

## File Structure

```text
.
├── main.py                 # Single-file FastAPI application
├── requirements.txt        # Runtime dependencies (fastapi, uvicorn, boto3, pydantic)
├── requirements-dev.txt    # Dev dependencies (pytest, hypothesis, httpx, ruff)
├── Dockerfile              # Production container build
├── tests/                  # Property-based tests
└── .github/workflows/      # CI/CD pipelines
```

## Key Concepts

- **Single-file application** — All application logic lives in `main.py`
- **Startup validation** — Model availability checked before serving traffic via lifespan hook
- **Property-based testing** — Uses Hypothesis to generate invalid inputs and verify rejection
- **Non-root container** — Dockerfile creates and runs as `appuser` for security
- **GHCR publishing** — Container images tagged with semver, SHA, and `latest`
- **Decoupled from infrastructure** — This repo owns only the application code and container build; Terraform lives separately
