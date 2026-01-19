# Contributing to Inventory Management System

Thank you for your interest in contributing to the Inventory Management System! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Poetry (Python dependency management)
- Docker and Docker Compose
- Git

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/yourusername/inventory-management-system.git
   cd inventory-management-system
   ```

2. **Install Dependencies**
   ```bash
   # Python dependencies
   poetry install --with dev
   
   # UI dependencies
   cd services/ui
   npm install
   cd ../..
   ```

3. **Set Up Pre-commit Hooks**
   ```bash
   poetry run pre-commit install
   ```

4. **Start Development Environment**
   ```bash
   docker-compose up -d
   ```

5. **Run Tests**
   ```bash
   poetry run pytest
   ```

## 🎯 How to Contribute

### Types of Contributions

We welcome several types of contributions:

- **Bug Reports**: Help us identify and fix issues
- **Feature Requests**: Suggest new functionality
- **Code Contributions**: Implement features or fix bugs
- **Documentation**: Improve or add documentation
- **Testing**: Add or improve test coverage
- **Performance**: Optimize existing code

### Before You Start

1. **Check Existing Issues**: Look for existing issues or discussions
2. **Create an Issue**: For new features or bugs, create an issue first
3. **Discuss**: Comment on the issue to discuss your approach
4. **Get Assignment**: Wait for maintainer approval before starting work

## 📝 Development Process

### 1. Create a Branch

```bash
# Create and switch to a new branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/bug-description
```

### 2. Make Changes

Follow our coding standards (see below) and make your changes.

### 3. Test Your Changes

```bash
# Run all tests
poetry run pytest

# Run specific test categories
poetry run pytest tests/unit/
poetry run pytest tests/integration/
poetry run pytest tests/property/

# Check code coverage
poetry run pytest --cov=services --cov=shared --cov-report=html
```

### 4. Code Quality Checks

```bash
# Format code
poetry run black .
poetry run isort .

# Lint code
poetry run flake8

# Type checking
poetry run mypy services/ shared/

# Run pre-commit hooks
poetry run pre-commit run --all-files
```

### 5. Commit Changes

Use conventional commit messages:

```bash
git commit -m "feat: add user profile management"
git commit -m "fix: resolve authentication token expiry issue"
git commit -m "docs: update API documentation"
git commit -m "test: add property tests for user validation"
```

### 6. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## 📋 Coding Standards

### Python Code Style

- **Formatting**: Use Black with default settings
- **Import Sorting**: Use isort with Black-compatible settings
- **Line Length**: 88 characters (Black default)
- **Type Hints**: Use type hints for all function parameters and return values
- **Docstrings**: Use Google-style docstrings for all public functions and classes

#### Example:
```python
from typing import List, Optional

def create_user(
    username: str, 
    email: str, 
    role_id: Optional[str] = None
) -> User:
    """Create a new user with the specified details.
    
    Args:
        username: The unique username for the user
        email: The user's email address
        role_id: Optional role ID to assign to the user
        
    Returns:
        The created User object
        
    Raises:
        ValidationError: If username or email is invalid
        DuplicateError: If username or email already exists
    """
    # Implementation here
    pass
```

### TypeScript/React Code Style

- **Formatting**: Use Prettier with default settings
- **Linting**: Follow ESLint rules
- **Components**: Use functional components with hooks
- **Props**: Define interfaces for all component props
- **Naming**: Use PascalCase for components, camelCase for functions/variables

#### Example:
```typescript
interface UserProfileProps {
  user: User;
  onUpdate: (user: User) => void;
  isLoading?: boolean;
}

const UserProfile: React.FC<UserProfileProps> = ({ 
  user, 
  onUpdate, 
  isLoading = false 
}) => {
  // Component implementation
  return (
    <div>
      {/* JSX here */}
    </div>
  );
};
```

### Testing Standards

#### Unit Tests
- **Coverage**: Aim for >90% code coverage
- **Isolation**: Mock external dependencies
- **Naming**: Use descriptive test names
- **Structure**: Follow Arrange-Act-Assert pattern

```python
def test_create_user_with_valid_data_returns_user():
    # Arrange
    username = "testuser"
    email = "test@example.com"
    
    # Act
    user = create_user(username, email)
    
    # Assert
    assert user.username == username
    assert user.email == email
    assert user.id is not None
```

#### Integration Tests
- **Real Dependencies**: Use real database connections
- **Cleanup**: Ensure tests clean up after themselves
- **Transactions**: Use database transactions for isolation

#### Property-Based Tests
- **Hypothesis**: Use Hypothesis for property-based testing
- **Properties**: Test invariants that should always hold
- **Edge Cases**: Let Hypothesis find edge cases

```python
from hypothesis import given, strategies as st

@given(st.text(min_size=1, max_size=50))
def test_username_validation_property(username):
    """Property: Valid usernames should always pass validation."""
    if is_valid_username_format(username):
        user = create_user(username, f"{username}@example.com")
        assert user.username == username
```

## 🔍 Code Review Process

### What We Look For

1. **Correctness**: Does the code work as intended?
2. **Testing**: Are there appropriate tests?
3. **Style**: Does it follow our coding standards?
4. **Performance**: Are there any performance concerns?
5. **Security**: Are there any security implications?
6. **Documentation**: Is the code well-documented?

### Review Checklist

- [ ] Code follows style guidelines
- [ ] Tests are included and pass
- [ ] Documentation is updated
- [ ] No breaking changes (or properly documented)
- [ ] Performance impact is acceptable
- [ ] Security considerations are addressed

## 🐛 Bug Reports

### Before Reporting

1. **Search Existing Issues**: Check if the bug is already reported
2. **Reproduce**: Ensure you can consistently reproduce the issue
3. **Minimal Example**: Create a minimal example that demonstrates the bug

### Bug Report Template

```markdown
## Bug Description
A clear and concise description of what the bug is.

## Steps to Reproduce
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

## Expected Behavior
A clear description of what you expected to happen.

## Actual Behavior
A clear description of what actually happened.

## Environment
- OS: [e.g. macOS 12.0]
- Python Version: [e.g. 3.11.0]
- Browser: [e.g. Chrome 96.0]
- Version: [e.g. 0.1.0]

## Additional Context
Add any other context about the problem here.

## Screenshots
If applicable, add screenshots to help explain your problem.

## Logs
Include relevant log output if available.
```

## 💡 Feature Requests

### Before Requesting

1. **Check Roadmap**: See if the feature is already planned
2. **Search Issues**: Check if someone else has requested it
3. **Consider Scope**: Ensure the feature fits the project's goals

### Feature Request Template

```markdown
## Feature Description
A clear and concise description of the feature you'd like to see.

## Problem Statement
What problem does this feature solve? What's the use case?

## Proposed Solution
Describe the solution you'd like to see implemented.

## Alternatives Considered
Describe any alternative solutions or features you've considered.

## Additional Context
Add any other context, mockups, or examples about the feature request.

## Implementation Notes
If you have ideas about how this could be implemented, share them here.
```

## 🏗️ Architecture Guidelines

### Microservices Principles

- **Single Responsibility**: Each service should have one clear purpose
- **Loose Coupling**: Services should be independent
- **High Cohesion**: Related functionality should be grouped together
- **API First**: Design APIs before implementation
- **Database per Service**: Each service should own its data

### Adding New Services

1. **Create Service Directory**: `services/new-service/`
2. **Follow Structure**: Copy structure from existing services
3. **Add Dockerfile**: Container configuration
4. **Update Docker Compose**: Add service to development environment
5. **Add Tests**: Comprehensive test coverage
6. **Update Documentation**: API docs and README

### Database Changes

1. **Create Migration**: Use Alembic for schema changes
2. **Backward Compatible**: Ensure migrations don't break existing code
3. **Test Migration**: Test both up and down migrations
4. **Update Models**: Keep SQLAlchemy models in sync

## 📚 Documentation

### Types of Documentation

- **API Documentation**: Automatically generated from code
- **User Documentation**: How to use the system
- **Developer Documentation**: How to contribute and extend
- **Architecture Documentation**: System design and decisions

### Writing Guidelines

- **Clear and Concise**: Use simple, direct language
- **Examples**: Include code examples and use cases
- **Up to Date**: Keep documentation current with code changes
- **Accessible**: Consider different skill levels

## 🚀 Release Process

### Versioning

We use [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

- [ ] All tests pass
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated
- [ ] Version numbers are bumped
- [ ] Release notes are prepared
- [ ] Deployment is tested

## 🤝 Community

### Communication

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Pull Requests**: For code contributions

### Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors. Please be respectful and professional in all interactions.

### Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- GitHub contributors page

## ❓ Getting Help

### For Contributors

- **Documentation**: Check this file and README.md
- **Issues**: Search existing issues for similar problems
- **Discussions**: Use GitHub Discussions for questions
- **Code**: Look at existing code for patterns and examples

### For Users

- **Documentation**: Check README.md and API docs
- **Issues**: Create an issue for bugs or feature requests
- **Discussions**: Use GitHub Discussions for usage questions

## 📄 License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to the Inventory Management System! 🎉