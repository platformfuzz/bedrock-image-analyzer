# Domain Context

## Project Purpose

This is a standalone container image repository for an AI-powered image analysis API. The application uses Amazon Bedrock Claude 3 Sonnet to analyze images provided via URL and return natural language descriptions. It is deployed as a container on AWS ECS Fargate, with infrastructure managed in a separate Terraform repository.

## Architecture

```text
Client → ALB (managed by ECS Express Mode) → ECS Fargate Task → FastAPI Container → Amazon Bedrock Claude
```

The container runs a Python FastAPI application that:
1. Receives image URLs via POST /analyze
2. Sends the image to Amazon Bedrock Claude 3 Sonnet for analysis
3. Returns the AI-generated description to the caller

## API Endpoints

- **POST /analyze** — Accepts `{"image_url": "https://..."}`, invokes Bedrock Claude, returns `{"image_url": "...", "description": "..."}`
- **GET /health** — Returns `{"status": "healthy"}` for load balancer health checks

## Error Model

- HTTP 422 for invalid/missing image URL (Pydantic HttpUrl validation)
- HTTP 502 when Bedrock invocation fails (network issues, model errors)

## Runtime Environment

- Container runs on AWS ECS Fargate (infrastructure in separate repo)
- Requires AWS credentials with `bedrock:InvokeModel` permission
- Uses `anthropic.claude-3-sonnet-20240229-v1:0` model ID
- Listens on port 8000 via uvicorn

## File Structure

```text
.
├── main.py                 # Single-file FastAPI application
├── requirements.txt        # Runtime dependencies (fastapi, uvicorn, boto3, pydantic)
├── requirements-dev.txt    # Dev dependencies (pytest, hypothesis, httpx, ruff)
├── Dockerfile              # Production container build
├── tests/                  # Property-based tests
└── .github/workflows/      # CI pipelines
```

## Key Concepts

- **Single-file application** — All application logic lives in `main.py`
- **Property-based testing** — Uses Hypothesis to generate invalid inputs and verify rejection
- **Non-root container** — Dockerfile creates and runs as `appuser` for security
- **Decoupled from infrastructure** — This repo owns only the application code and container build; Terraform lives separately
