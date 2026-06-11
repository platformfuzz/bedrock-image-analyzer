# Requirements Document

## Introduction

Extract the containerized FastAPI application from the `terraform-aws-ecs-express-mode-demo` repository into a standalone repository (`platformfuzz/bedrock-image-analyzer-image`). The new repository will be a fully self-contained container image project with its own CI workflows, tests, documentation, and Kiro configuration. The original Terraform repository will be updated to remove the embedded application code and Docker build resource, referencing the externally-built image instead.

## Glossary

- **Source_Repo**: The existing repository at `/home/johna/workspace/jajera/terraform-aws-ecs-express-mode-demo` containing Terraform infrastructure and the embedded container application
- **Target_Repo**: The new standalone repository at `~/workspace/platformfuzz/bedrock-image-analyzer-image` containing only the container application
- **Container_App**: The FastAPI Python application that provides image analysis via Amazon Bedrock Claude
- **CI_Workflow**: A GitHub Actions workflow file that automates linting, testing, or building
- **Reusable_Workflow**: A workflow from the `actionsforge/actions` repository called via the `uses` directive
- **Kiro_Config**: The `.kiro/` directory containing steering files and spec configuration

## Requirements

### Requirement 1: Create Target Repository Structure

**User Story:** As a developer, I want a new standalone repository for the container image, so that the application lifecycle is decoupled from the Terraform infrastructure lifecycle.

#### Acceptance Criteria

1. THE Target_Repo SHALL contain a root-level `Dockerfile` copied from `Source_Repo/app/Dockerfile`
2. THE Target_Repo SHALL contain a root-level `main.py` copied from `Source_Repo/app/main.py`
3. THE Target_Repo SHALL contain a root-level `requirements.txt` copied from `Source_Repo/app/requirements.txt`
4. THE Target_Repo SHALL contain a `tests/` directory with `conftest.py`, `test_app.py`, and `__init__.py` adapted from the Source_Repo application tests
5. THE Target_Repo SHALL contain a `.gitignore` file appropriate for a Python container image project
6. THE Target_Repo SHALL contain a `LICENSE` file with the MIT license attributed to John Ajera
7. THE Target_Repo SHALL contain a `README.md` documenting the project purpose, usage, local development, and testing

### Requirement 2: GitHub Actions CI Workflows

**User Story:** As a developer, I want automated CI pipelines in the new repository, so that code quality and correctness are validated on every push and pull request.

#### Acceptance Criteria

1. THE Target_Repo SHALL contain a `.github/workflows/commitmsg-conform.yml` workflow that calls `actionsforge/actions/.github/workflows/commitmsg-conform.yml@main` on pull requests
2. THE Target_Repo SHALL contain a `.github/workflows/markdown-lint.yml` workflow that calls `actionsforge/actions/.github/workflows/markdown-lint.yml@main` on push and pull request events
3. THE Target_Repo SHALL contain a `.github/workflows/python-lint-test.yml` workflow that runs Python linting and tests on push and pull request events
4. WHEN the `python-lint-test.yml` workflow runs, THE CI_Workflow SHALL install dependencies, run linting, and execute the test suite including property-based tests

### Requirement 3: Kiro Configuration for Target Repository

**User Story:** As a developer, I want Kiro steering files in the new repository, so that AI-assisted development follows the project conventions.

#### Acceptance Criteria

1. THE Target_Repo SHALL contain a `.kiro/steering/` directory with project-appropriate steering files
2. THE Target_Repo SHALL contain a domain context steering file describing the image analyzer application purpose, endpoints, and architecture
3. THE Target_Repo SHALL contain a Python conventions steering file describing coding patterns, testing approach, and project structure

### Requirement 4: Test Adaptation for Standalone Repository

**User Story:** As a developer, I want the existing tests to work in the new repository structure, so that test coverage is preserved after extraction.

#### Acceptance Criteria

1. WHEN tests are executed in the Target_Repo, THE test suite SHALL import the application from the root-level `main.py` module
2. THE `conftest.py` SHALL patch the Bedrock client at the correct module path for the new repository layout
3. THE test suite SHALL include the existing property-based tests using Hypothesis with a minimum of 100 iterations
4. THE Target_Repo SHALL include a test dependencies specification (e.g., `requirements-dev.txt`) listing pytest, hypothesis, httpx, and related test libraries

### Requirement 5: Remove Application from Source Repository

**User Story:** As a developer, I want the embedded application removed from the Terraform repository, so that there is a single source of truth for the container image.

#### Acceptance Criteria

1. WHEN the extraction is complete, THE Source_Repo SHALL no longer contain the `app/` directory
2. WHEN the extraction is complete, THE Source_Repo SHALL no longer contain `tests/test_app.py` or the application-specific fixtures in `tests/conftest.py`
3. THE `ecr.tf` file SHALL retain the `aws_ecr_repository` and `aws_ecr_lifecycle_policy` resources
4. THE `ecr.tf` file SHALL no longer contain the `null_resource.docker_build_push` resource
5. THE Source_Repo `README.md` SHALL be updated to remove references to the `app/` directory and document that the container image is built externally
6. THE Source_Repo `.gitignore` SHALL be updated to remove Python-specific entries if no Python code remains

### Requirement 6: Docker Build Compatibility

**User Story:** As a developer, I want the container image to be buildable from the new repository root, so that CI and local development workflows function correctly.

#### Acceptance Criteria

1. WHEN `docker build .` is run in the Target_Repo root, THE Dockerfile SHALL produce a working container image
2. THE Dockerfile SHALL use a non-root user for running the application
3. THE Dockerfile SHALL expose port 8000 and run uvicorn as the default command
4. THE Target_Repo SHALL maintain the same application behavior (POST /analyze, GET /health) as the original embedded application
