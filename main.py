"""FastAPI application for AI-powered image analysis using Amazon Bedrock."""

import json
import logging

import boto3
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl

logger = logging.getLogger(__name__)

app = FastAPI(title="Image Analysis API", description="AI-powered image analysis using Amazon Bedrock")

bedrock_client = boto3.client("bedrock-runtime")

MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0"


class AnalyzeRequest(BaseModel):
    """Request model for POST /analyze."""

    image_url: HttpUrl


class AnalyzeResponse(BaseModel):
    """Response model for POST /analyze."""

    image_url: str
    description: str


class HealthResponse(BaseModel):
    """Response model for GET /health."""

    status: str


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="healthy")


@app.post("/analyze", response_model=AnalyzeResponse, responses={502: {"model": ErrorResponse}})
def analyze(request: AnalyzeRequest) -> AnalyzeResponse | JSONResponse:
    """Analyze an image using Amazon Bedrock Claude model."""
    image_url = str(request.image_url)

    try:
        body = json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1024,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "url",
                                    "url": image_url,
                                },
                            },
                            {
                                "type": "text",
                                "text": "Describe this image in detail.",
                            },
                        ],
                    }
                ],
            }
        )

        response = bedrock_client.invoke_model(
            modelId=MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=body,
        )

        response_body = json.loads(response["body"].read())
        description = response_body["content"][0]["text"]

        return AnalyzeResponse(image_url=image_url, description=description)

    except Exception as e:
        logger.error("Bedrock invocation failed: %s", str(e))
        return JSONResponse(
            status_code=502,
            content={"error": f"Bedrock invocation failed: {str(e)}"},
        )
