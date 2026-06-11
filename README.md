# bedrock-image-analyzer-image

AI-powered image analysis container using Amazon Bedrock Claude.

This is a Python FastAPI application that accepts image URLs and returns
AI-generated descriptions using Amazon Bedrock Claude 3 Sonnet. It is designed
to run as a container on AWS ECS Fargate.

## Prerequisites

- Python 3.14+
- Docker (for building the container image)
- AWS credentials with `bedrock:InvokeModel` permission

## Local Development

Install dependencies:

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

Run the application:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Docker Build

Build the container image:

```bash
docker build -t bedrock-image-analyzer:latest .
```

Run the container:

```bash
docker run -p 8000:8000 \
  -e AWS_ACCESS_KEY_ID=... \
  -e AWS_SECRET_ACCESS_KEY=... \
  -e AWS_DEFAULT_REGION=us-east-1 \
  bedrock-image-analyzer:latest
```

## Testing

Install dev dependencies:

```bash
pip install -r requirements-dev.txt
```

Run linting:

```bash
ruff check .
```

Run the test suite:

```bash
pytest tests/ -v
```

The tests use property-based testing with Hypothesis to validate input
rejection behavior.

## API Endpoints

### POST /analyze

Accepts an image URL and returns an AI-generated description.

**Request:**

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://example.com/image.jpg"}'
```

**Response:**

```json
{
  "image_url": "https://example.com/image.jpg",
  "description": "AI-generated description of the image..."
}
```

### GET /health

Health check endpoint for load balancer integration.

```bash
curl http://localhost:8000/health
```

**Response:**

```json
{"status": "healthy"}
```

### Error Responses

| Status | Condition |
|--------|-----------|
| 422 | Invalid or missing image URL (Pydantic validation) |
| 502 | Bedrock invocation failure |

## Project Structure

```text
.
├── main.py                 # FastAPI application (POST /analyze, GET /health)
├── requirements.txt        # Runtime Python dependencies
├── requirements-dev.txt    # Test and lint dependencies
├── Dockerfile              # Container image build (non-root user, port 8000)
├── .dockerignore           # Files excluded from Docker build context
├── tests/
│   ├── __init__.py         # Package marker
│   ├── conftest.py         # Shared test fixtures (mock Bedrock client)
│   └── test_app.py         # Property-based tests for URL validation
├── .github/workflows/
│   ├── commitmsg-conform.yml   # Commit message convention enforcement
│   ├── markdown-lint.yml       # Markdown linting
│   └── python-lint-test.yml    # Python linting and tests
└── README.md               # This file
```
