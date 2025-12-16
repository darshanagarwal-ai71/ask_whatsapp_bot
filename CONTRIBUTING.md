# Contributing to ASK WhatsApp Bot

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Database Changes](#database-changes)
- [Testing](#testing)

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Assume good intentions

## Getting Started

### Prerequisites

Ensure you have:
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) installed
- PostgreSQL 15+ running locally or via Docker
- Git configured with your name and email


## Development Setup

1. **Install dependencies**:
   ```bash
   uv sync
   ```

2. **Configure environment**:
   ```bash
   cp env.example .env
   # Edit .env with your credentials
   ```

3. **Start PostgreSQL** (if using Docker):
   ```bash
   docker compose up -d db
   ```

4. **Run migrations**:
   ```bash
   uv run alembic upgrade head
   ```

5. **Start the application**:
   ```bash
   ./start.sh
   ```

## Making Changes

### Create a Feature Branch

Always create a new branch for your changes:

```bash
git checkout -b feature/your-feature-name
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions or updates

### Commit Guidelines

Use [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>: <description>

[optional body]

[optional footer]
```

**Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, semicolons, etc.)
- `refactor:` - Code refactoring
- `perf:` - Performance improvements
- `test:` - Adding or updating tests
- `chore:` - Build process or auxiliary tool changes

**Examples:**
```bash
git commit -m "feat: add support for media messages"
git commit -m "fix: resolve session timeout issue"
git commit -m "docs: update deployment instructions"
```

### Keep Your Fork Updated

Regularly sync with upstream:

```bash
git fetch upstream
git checkout main
git merge upstream/main
git push origin main
```

## Pull Request Process

1. **Ensure your code follows the project's style**
2. **Update documentation** if you've changed functionality
3. **Test your changes thoroughly**
4. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```
5. **Open a Pull Request** with:
   - Clear, descriptive title
   - Detailed description of changes
   - Reference to related issues (e.g., "Closes #123")
   - Screenshots or logs if applicable

### PR Checklist

- [ ] Code follows project style guidelines
- [ ] All tests pass
- [ ] Documentation updated (if needed)
- [ ] Database migrations created (if models changed)
- [ ] Commit messages follow conventional format
- [ ] PR description is clear and complete

## Coding Standards

### Python Style

Follow [PEP 8](https://pep8.org/) guidelines:

- Use 4 spaces for indentation
- Maximum line length: 88 characters (Black formatter default)
- Use descriptive variable names
- Add docstrings to functions and classes

**Function docstring example:**
```python
def process_message(message: str, user_id: str) -> dict:
    """
    Process incoming WhatsApp message and relay to ASK agent.
    
    Args:
        message: The text message from user
        user_id: Unique identifier for the user
        
    Returns:
        dict: Response from ASK agent
        
    Raises:
        ValueError: If message is empty
    """
    pass
```

### Code Organization

- Keep functions focused and single-purpose
- Use type hints where possible
- Handle errors gracefully with appropriate logging
- Avoid hardcoded values; use configuration
- Keep business logic separate from route handlers

### Environment Variables

- Add new variables to `env.example` with placeholder values
- Document new variables in README
- Use `config.py` for centralized configuration management

## Database Changes

### Creating Migrations

After modifying `app/models.py`:

```bash
uv run alembic revision --autogenerate -m "describe your change"
```

### Migration Best Practices

- Review generated migration before committing
- Test both upgrade and downgrade paths
- Use descriptive migration messages
- Avoid data loss operations when possible
- Document breaking changes in PR

### Testing Migrations

```bash
# Apply migration
uv run alembic upgrade head

# Test rollback
uv run alembic downgrade -1

# Re-apply
uv run alembic upgrade head
```

## Testing

### Manual Testing

1. Start the application
2. Test the affected functionality
3. Verify no regressions in existing features
4. Test error handling and edge cases

### Testing Checklist

- [ ] Application starts without errors
- [ ] Database migrations apply successfully
- [ ] WhatsApp messages are received and processed
- [ ] ASK agent integration works correctly
- [ ] Session timeout behavior is correct
- [ ] Error handling works as expected

## Reporting Issues

### Bug Reports

Include:
- Clear, descriptive title
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)
- Relevant logs or error messages
- Screenshots if applicable

### Feature Requests

Include:
- Clear description of the feature
- Use case and motivation
- Proposed implementation (if you have ideas)
- Potential impact on existing functionality

## Getting Help

- Check existing [Issues](../../issues) and [Discussions](../../discussions)
- Read the [README](README.md) thoroughly
- Join project discussions on GitHub
- Ask questions in a new Discussion topic

## Recognition

Contributors will be recognized in:
- GitHub contributors list
- Release notes for significant contributions
- Project documentation (for major features)

Thank you for contributing to ASK WhatsApp Bot! 🎉