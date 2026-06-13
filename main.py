"""FastAPI application for AI-powered image analysis using Amazon Bedrock."""

import base64
import json
import logging
import os
from contextlib import asynccontextmanager

import boto3
import httpx
from botocore.exceptions import ClientError
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl

logger = logging.getLogger(__name__)

DEFAULT_MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0"
DEFAULT_MAX_TOKENS = 1024
INFERENCE_PROFILE_PREFIXES = ("global.", "us.", "eu.", "au.", "apac.", "jp.")

MODEL_ID = os.environ.get("MODEL_ID", DEFAULT_MODEL_ID)
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", str(DEFAULT_MAX_TOKENS)))
MAX_IMAGE_BYTES = int(os.environ.get("MAX_IMAGE_BYTES", str(5 * 1024 * 1024)))
IMAGE_FETCH_TIMEOUT_SECONDS = float(os.environ.get("IMAGE_FETCH_TIMEOUT_SECONDS", "30"))

bedrock_client = boto3.client("bedrock-runtime")


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


def _get_aws_region() -> str:
    """Return the AWS region used by the Bedrock client."""
    session = boto3.Session()
    return session.region_name or os.environ.get("AWS_DEFAULT_REGION", "us-east-1")


def _is_model_not_available_error(error_code: str, message: str) -> bool:
    """Return True when a Bedrock error indicates the model is unavailable in this region."""
    lowered = message.lower()
    model_indicators = (
        "model identifier is invalid",
        "could not resolve model",
        "model not found",
        "not available in this region",
        "unsupported model",
        "foundation model",
    )
    if error_code == "ResourceNotFoundException":
        return True
    if error_code == "ValidationException" and any(indicator in lowered for indicator in model_indicators):
        return True
    return False


def _model_region_error_message() -> str:
    """Build a user-facing error message for unsupported model/region combinations."""
    region = _get_aws_region()
    return (
        f"Model '{MODEL_ID}' is not available in AWS region '{region}'. "
        "Deploy to a supported region or set MODEL_ID to a model available in this region."
    )


def _is_inference_profile_id(model_id: str) -> bool:
    """Return True when MODEL_ID is a Bedrock inference profile (e.g. au.*, global.*)."""
    return model_id.startswith(INFERENCE_PROFILE_PREFIXES)


def _fetch_image(image_url: str) -> tuple[str, str]:
    """Download an image and return its media type and base64-encoded bytes.

    Bedrock Claude models require base64 image sources; URL sources are not supported.
    """
    try:
        with httpx.Client(follow_redirects=True, timeout=IMAGE_FETCH_TIMEOUT_SECONDS) as client:
            response = client.get(image_url)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise ValueError(f"Failed to fetch image: {exc}") from exc

    content_type = response.headers.get("content-type", "").split(";")[0].strip().lower()
    if not content_type.startswith("image/"):
        raise ValueError(
            f"URL did not return an image (content-type: {content_type or 'unknown'})"
        )

    if len(response.content) > MAX_IMAGE_BYTES:
        raise ValueError(f"Image exceeds maximum size of {MAX_IMAGE_BYTES} bytes")

    image_b64 = base64.standard_b64encode(response.content).decode("ascii")
    return content_type, image_b64


def validate_model_availability() -> None:
    """Verify MODEL_ID is available in the current AWS region.

    Raises:
        RuntimeError: If the configured model is not available in the deployment region.
    """
    region = _get_aws_region()
    control_client = boto3.client("bedrock", region_name=region)
    try:
        if _is_inference_profile_id(MODEL_ID):
            control_client.get_inference_profile(inferenceProfileIdentifier=MODEL_ID)
        else:
            control_client.get_foundation_model(modelIdentifier=MODEL_ID)
    except ClientError as exc:
        error = exc.response.get("Error", {})
        code = error.get("Code", "")
        message = error.get("Message", str(exc))
        if _is_model_not_available_error(code, message):
            raise RuntimeError(_model_region_error_message()) from exc
        raise


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Run startup validation before serving requests."""
    validate_model_availability()
    yield


app = FastAPI(
    title="Image Analysis API",
    description="AI-powered image analysis using Amazon Bedrock",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="healthy")


@app.post(
    "/analyze",
    response_model=AnalyzeResponse,
    responses={
        502: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
def analyze(request: AnalyzeRequest) -> AnalyzeResponse | JSONResponse:
    """Analyze an image using Amazon Bedrock Claude model."""
    image_url = str(request.image_url)

    try:
        media_type, image_b64 = _fetch_image(image_url)
    except ValueError as exc:
        return JSONResponse(
            status_code=422,
            content={"error": str(exc)},
        )

    try:
        body = json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": MAX_TOKENS,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_b64,
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

    except ClientError as exc:
        error = exc.response.get("Error", {})
        code = error.get("Code", "")
        message = error.get("Message", str(exc))
        if _is_model_not_available_error(code, message):
            logger.error(
                "Model %s is not available in region %s: %s",
                MODEL_ID,
                _get_aws_region(),
                message,
            )
            return JSONResponse(
                status_code=503,
                content={"error": _model_region_error_message()},
            )

        logger.error("Bedrock invocation failed: %s", message)
        return JSONResponse(
            status_code=502,
            content={"error": f"Bedrock invocation failed: {message}"},
        )

    except Exception as exc:
        logger.error("Bedrock invocation failed: %s", str(exc))
        return JSONResponse(
            status_code=502,
            content={"error": f"Bedrock invocation failed: {str(exc)}"},
        )
