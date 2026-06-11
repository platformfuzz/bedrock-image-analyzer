"""Property-based tests for the container application."""

import string

from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st


# Feature: ecs-express-mode-demo, Property 3: Invalid URL rejection produces 422
# **Validates: Requirements 3.7**


def _invalid_url_strategy():
    """Generate strings that are NOT valid HTTP/HTTPS URLs per Pydantic HttpUrl.

    Pydantic HttpUrl requires:
    - A scheme of http or https
    - A host component (even a single character counts)

    Strategies that produce truly invalid URLs:
    - Empty strings
    - Whitespace-only strings
    - Strings without any scheme
    - Non-HTTP schemes (ftp://, file://, mailto:, etc.)
    - http:// or https:// without a host
    - Random garbage text without valid URL structure
    """
    return st.one_of(
        # Empty string
        st.just(""),
        # Whitespace-only strings
        st.text(alphabet=string.whitespace, min_size=1, max_size=10),
        # Random short garbage (no scheme, no valid URL structure)
        st.text(
            alphabet=string.ascii_letters + string.digits + "!@#$%^&*",
            min_size=1,
            max_size=50,
        ).filter(lambda s: not s.startswith(("http://", "https://"))),
        # Non-HTTP schemes (Pydantic rejects these)
        st.sampled_from([
            "ftp://example.com/file.txt",
            "file:///etc/passwd",
            "mailto:user@example.com",
            "data:text/plain;base64,SGVsbG8=",
            "javascript:alert(1)",
            "gopher://example.com",
            "telnet://example.com:23",
        ]),
        # HTTP/HTTPS scheme but missing host entirely
        st.sampled_from([
            "http://",
            "https://",
            "http:",
            "https:",
            "http:/",
            "https:/",
        ]),
        # Just a path (no scheme)
        st.from_regex(r"/[a-z]{1,20}/[a-z]{1,10}", fullmatch=True),
        # Words that look like domains but lack scheme
        st.from_regex(r"[a-z]{3,10}\.[a-z]{2,4}", fullmatch=True),
        # Partial/broken scheme prefixes
        st.sampled_from([
            "htp://example.com",
            "htps://example.com",
            "://example.com",
            "//example.com",
        ]),
    )


class TestInvalidUrlRejection:
    """Property 3: Invalid URL rejection produces 422.

    For any string that is not a valid HTTP(S) URL, the /analyze endpoint
    SHALL return HTTP 422 with error details and SHALL NOT invoke Bedrock.
    """

    @given(invalid_url=_invalid_url_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_invalid_url_rejection_produces_422(self, invalid_url, client, mock_bedrock_client):
        """Invalid URLs must be rejected with 422 and no Bedrock invocation."""
        # Reset mock state between hypothesis iterations
        mock_bedrock_client.invoke_model.reset_mock()

        response = client.post("/analyze", json={"image_url": invalid_url})

        # Must return 422 for invalid URLs
        assert response.status_code == 422, (
            f"Expected 422 for invalid URL {invalid_url!r}, got {response.status_code}"
        )

        # Response must contain error detail information (FastAPI uses "detail" for validation errors)
        body = response.json()
        assert "detail" in body, (
            f"Expected 'detail' field in 422 response for URL {invalid_url!r}, got {body}"
        )
        assert len(body["detail"]) > 0, "Expected non-empty 'detail' field in 422 response"

        # Bedrock client must NOT have been invoked
        mock_bedrock_client.invoke_model.assert_not_called()
