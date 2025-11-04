# Contributing to Qilbee Mycelial Network

Thank you for your interest in contributing to Qilbee Mycelial Network! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Release Process](#release-process)

## Code of Conduct

We are committed to providing a welcoming and inspiring community for all. Please be respectful and constructive in your interactions.

### Our Standards

- **Be respectful**: Treat everyone with respect and kindness
- **Be constructive**: Provide helpful feedback and suggestions
- **Be collaborative**: Work together towards common goals
- **Be inclusive**: Welcome contributors of all backgrounds and experience levels

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/qilbee-mycelial-network.git
   cd qilbee-mycelial-network
   ```

3. **Add the upstream repository**:
   ```bash
   git remote add upstream https://github.com/aicubetechnology/qilbee-mycelial-network.git
   ```

4. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

### Prerequisites

- Python 3.9 or higher
- Docker and Docker Compose
- Git
- Make (optional, for convenience commands)

### Local Development Environment

1. **Install dependencies**:
   ```bash
   cd sdk
   pip install -e ".[dev]"
   ```

2. **Start infrastructure services**:
   ```bash
   make up
   ```

3. **Run tests**:
   ```bash
   make test
   ```

4. **Verify setup**:
   ```bash
   make test-all
   ```

### Docker Development

All services can be run via Docker Compose:

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check existing issues. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce** the issue
- **Expected vs actual behavior**
- **Environment details** (OS, Python version, etc.)
- **Code samples** or error messages

Use the bug report template:

```markdown
**Description**
A clear description of the bug.

**To Reproduce**
Steps to reproduce the behavior:
1. Initialize client with...
2. Call method...
3. Observe error...

**Expected Behavior**
What you expected to happen.

**Actual Behavior**
What actually happened.

**Environment**
- OS: [e.g., Ubuntu 22.04]
- Python: [e.g., 3.11.2]
- SDK Version: [e.g., 0.1.0]

**Additional Context**
Any other relevant information.
```

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. Include:

- **Use case**: Why is this enhancement needed?
- **Proposed solution**: How should it work?
- **Alternatives considered**: What other approaches did you consider?
- **Additional context**: Screenshots, mockups, etc.

### Contributing Code

1. **Pick an issue** or create a new one
2. **Discuss your approach** in the issue comments
3. **Write code** following our coding standards
4. **Add tests** for new functionality
5. **Update documentation** as needed
6. **Submit a pull request**

## Coding Standards

### Python Style Guide

We follow [PEP 8](https://pep8.org/) with some modifications:

- **Line length**: 100 characters (enforced by Black)
- **Type hints**: Required for all public APIs
- **Docstrings**: Google style for all public functions/classes

### Code Formatting

We use automated formatters:

```bash
# Format code with Black
black sdk/

# Lint with Ruff
ruff check sdk/

# Type check with mypy
mypy sdk/
```

### Example Code Style

```python
from typing import List, Optional
import httpx
from pydantic import BaseModel


class Nutrient(BaseModel):
    """A nutrient containing context to share across the network.

    Args:
        summary: Brief description of the nutrient content
        embedding: 1536-dimension vector representation
        snippets: Optional code snippets or text fragments
        sensitivity: Data sensitivity level

    Example:
        >>> nutrient = Nutrient.seed(
        ...     summary="Database optimization advice",
        ...     embedding=[0.1, 0.2, ...],
        ...     sensitivity=Sensitivity.INTERNAL
        ... )
    """

    summary: str
    embedding: List[float]
    snippets: Optional[List[str]] = None
    sensitivity: str = "INTERNAL"

    @classmethod
    def seed(
        cls,
        summary: str,
        embedding: List[float],
        **kwargs
    ) -> "Nutrient":
        """Create a new nutrient instance.

        Args:
            summary: Brief description
            embedding: Vector representation
            **kwargs: Additional nutrient properties

        Returns:
            A new Nutrient instance
        """
        return cls(summary=summary, embedding=embedding, **kwargs)
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): subject

body

footer
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(client): add support for QUIC transport

Implement QUIC transport protocol for lower latency
communication with the mycelial network.

Closes #123
```

```
fix(routing): correct edge weight calculation

Edge weights were not properly normalized, causing
incorrect routing decisions.

Fixes #456
```

## Testing Guidelines

### Writing Tests

- **Unit tests**: Test individual functions/methods
- **Integration tests**: Test component interactions
- **End-to-end tests**: Test full user workflows

### Test Structure

```python
import pytest
from qilbee_mycelial_network import MycelialClient, Nutrient


class TestNutrient:
    """Tests for Nutrient model."""

    def test_seed_creates_nutrient(self):
        """Test that seed() creates a valid nutrient."""
        nutrient = Nutrient.seed(
            summary="test summary",
            embedding=[0.1] * 1536
        )

        assert nutrient.summary == "test summary"
        assert len(nutrient.embedding) == 1536

    def test_invalid_embedding_dimension_raises_error(self):
        """Test that invalid embedding dimensions raise error."""
        with pytest.raises(ValueError):
            Nutrient.seed(
                summary="test",
                embedding=[0.1] * 100  # Wrong dimension
            )


@pytest.mark.asyncio
class TestMycelialClient:
    """Tests for MycelialClient."""

    async def test_broadcast_sends_nutrient(self, mock_client):
        """Test that broadcast() sends nutrient to network."""
        async with MycelialClient.create_from_env() as client:
            nutrient = Nutrient.seed(
                summary="test",
                embedding=[0.1] * 1536
            )

            response = await client.broadcast(nutrient)

            assert response.status == "success"
```

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_client.py

# Specific test
pytest tests/test_client.py::TestMycelialClient::test_broadcast_sends_nutrient

# With coverage
pytest --cov=qilbee_mycelial_network --cov-report=html

# Integration tests only
pytest tests/integration/

# Skip slow tests
pytest -m "not slow"
```

### Test Coverage

- Aim for **>80% code coverage**
- **100% coverage** for critical paths (security, data handling)
- Coverage reports generated in `htmlcov/`

## Pull Request Process

### Before Submitting

1. **Update your branch** with the latest upstream changes:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run all checks**:
   ```bash
   make test-all
   black sdk/
   ruff check sdk/
   mypy sdk/
   ```

3. **Update documentation**:
   - Update README if adding features
   - Add docstrings to new code
   - Update CHANGELOG.md

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests passing
- [ ] Manual testing performed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests added for new functionality
- [ ] Dependent changes merged

## Related Issues
Closes #(issue number)
```

### Review Process

1. **Automated checks** must pass (CI/CD)
2. **At least one approving review** required
3. **Address review comments**
4. **Squash commits** if requested
5. **Maintainer merges** after approval

## Release Process

### Versioning

We use [Semantic Versioning](https://semver.org/):

- **MAJOR**: Incompatible API changes
- **MINOR**: Backward-compatible functionality
- **PATCH**: Backward-compatible bug fixes

### Release Steps

1. **Update version** in:
   - `sdk/pyproject.toml`
   - `sdk/setup.py`
   - `sdk/qilbee_mycelial_network/__init__.py`

2. **Update CHANGELOG.md**:
   ```markdown
   ## [0.2.0] - 2025-01-15

   ### Added
   - QUIC transport support
   - Custom agent profiles

   ### Changed
   - Improved routing algorithm performance

   ### Fixed
   - Edge weight normalization bug
   ```

3. **Create release commit**:
   ```bash
   git add .
   git commit -m "chore: release v0.2.0"
   git tag -a v0.2.0 -m "Release version 0.2.0"
   ```

4. **Push to GitHub**:
   ```bash
   git push upstream main
   git push upstream v0.2.0
   ```

5. **Build and publish**:
   ```bash
   cd sdk
   python -m build
   twine upload dist/*
   ```

6. **Create GitHub Release** with changelog

## Questions?

- **GitHub Discussions**: https://github.com/aicubetechnology/qilbee-mycelial-network/discussions
- **Email**: contact@aicube.ca
- **Issues**: https://github.com/aicubetechnology/qilbee-mycelial-network/issues

---

Thank you for contributing to Qilbee Mycelial Network!
