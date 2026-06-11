"""Shared test fixtures for the container application tests."""

import json
import os
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Set a dummy region before importing the app module to avoid NoRegionError
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")


@pytest.fixture
def mock_bedrock_client():
    """Provide a mock Bedrock runtime client.

    The mock can be configured to return successful responses or raise exceptions.
    By default, it returns a successful response with a sample description.
    """
    mock_client = MagicMock()

    # Default successful response
    default_response_body = json.dumps(
        {"content": [{"text": "A sample image description from Bedrock."}]}
    )
    mock_client.invoke_model.return_value = {
        "body": BytesIO(default_response_body.encode("utf-8"))
    }

    return mock_client


@pytest.fixture
def client(mock_bedrock_client):
    """Provide a FastAPI TestClient with the mock Bedrock client injected.

    Patches the module-level bedrock_client in main so that tests
    do not require real AWS credentials or network access.
    """
    with patch("main.bedrock_client", mock_bedrock_client):
        from main import app

        with TestClient(app) as test_client:
            yield test_client
