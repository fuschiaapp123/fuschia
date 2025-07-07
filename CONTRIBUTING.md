# Contributing to Fuschia

Thank you for your interest in contributing to Fuschia! This document provides guidelines and instructions for contributing to the project.

## 🎯 Getting Started

### Prerequisites
- Read and understand our [Code of Conduct](CODE_OF_CONDUCT.md)
- Familiarize yourself with the [README](README.md) and project architecture
- Set up your development environment following the installation guide

### Development Setup
1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/fuschia-alfa.git`
3. Run the setup script: `./setup.sh`
4. Create a feature branch: `git checkout -b feature/your-feature-name`

## 🔧 Development Guidelines

### Code Style

#### Backend (Python)
- Follow PEP 8 style guidelines
- Use type hints for all function parameters and return values
- Maximum line length: 88 characters
- Use docstrings for all public functions and classes

```python
async def create_knowledge_node(
    node_data: KnowledgeNodeCreate, 
    user_id: str
) -> KnowledgeNode:
    \"\"\"
    Create a new knowledge node in the graph database.
    
    Args:
        node_data: The node creation data
        user_id: ID of the user creating the node
        
    Returns:
        The created knowledge node
        
    Raises:
        ValidationError: If node data is invalid
    \"\"\"
```

#### Frontend (TypeScript)
- Use TypeScript for all new code
- Follow React best practices and hooks conventions
- Use functional components with hooks
- Prefer composition over inheritance

```typescript
interface Props {
  title: string;
  onSave: (data: FormData) => void;
  isLoading?: boolean;
}

export const MyComponent: React.FC<Props> = ({ 
  title, 
  onSave, 
  isLoading = false 
}) => {
  // Component implementation
};
```

### Commit Message Format
Use conventional commits:
```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(knowledge): add graph visualization component
fix(auth): resolve JWT token expiration issue
docs(api): update authentication endpoints
```

## 🧪 Testing

### Backend Testing
```bash
cd backend
source venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_knowledge_service.py
```

### Frontend Testing
```bash
cd frontend

# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run tests with coverage
npm test -- --coverage
```

### Integration Testing
```bash
# Start test environment
docker-compose -f docker-compose.test.yml up -d

# Run integration tests
pytest tests/integration/
```

## 📝 Documentation

### Code Documentation
- Document all public APIs
- Include examples in docstrings
- Update README for new features
- Add inline comments for complex logic

### API Documentation
- All endpoints must have OpenAPI documentation
- Include request/response examples
- Document error responses
- Test documentation with Swagger UI

## 🐛 Bug Reports

### Before Submitting
- Check existing issues to avoid duplicates
- Test with the latest version
- Gather relevant system information

### Bug Report Template
```markdown
**Bug Description**
A clear description of the bug.

**Steps to Reproduce**
1. Go to '...'
2. Click on '...'
3. See error

**Expected Behavior**
What you expected to happen.

**Actual Behavior**
What actually happened.

**Environment**
- OS: [e.g., macOS 12.0]
- Browser: [e.g., Chrome 95]
- Node.js version: [e.g., 18.0]
- Python version: [e.g., 3.9]

**Screenshots**
If applicable, add screenshots.

**Additional Context**
Any other relevant information.
```

## 💡 Feature Requests

### Before Submitting
- Check if the feature already exists
- Ensure it aligns with project goals
- Consider if it should be a plugin instead

### Feature Request Template
```markdown
**Feature Summary**
Brief description of the feature.

**Problem Statement**
What problem does this solve?

**Proposed Solution**
Detailed description of the proposed solution.

**Alternatives Considered**
Other solutions you considered.

**Additional Context**
Mockups, examples, or related issues.
```

## 🔄 Pull Request Process

### Before Creating a PR
1. Ensure your branch is up to date with main
2. Run all tests and ensure they pass
3. Run linting and fix any issues
4. Update documentation if needed
5. Add or update tests for new functionality

### PR Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Tests added/updated and passing
- [ ] Documentation updated
- [ ] No merge conflicts
- [ ] PR description is clear and complete

### PR Template
```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Screenshots
If applicable, add screenshots.

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Tests added/updated
- [ ] Documentation updated
```

### Review Process
1. Automated checks must pass
2. At least one maintainer review required
3. Address review feedback
4. Maintainer will merge when approved

## 🏗️ Architecture Guidelines

### Backend Architecture
- Follow Clean Architecture principles
- Separate concerns: API, Business Logic, Data Access
- Use dependency injection
- Handle errors gracefully
- Log important events

### Frontend Architecture
- Use component-based architecture
- Implement proper state management
- Follow React best practices
- Optimize for performance
- Ensure accessibility

### Database Design
- Design efficient graph schemas
- Use appropriate indexes
- Consider query performance
- Document relationship patterns

## 🔒 Security Guidelines

### Secure Coding
- Validate all inputs
- Use parameterized queries
- Implement proper authentication
- Handle sensitive data carefully
- Keep dependencies updated

### Security Testing
- Test authentication flows
- Validate authorization rules
- Check for injection vulnerabilities
- Test error handling
- Review logs for sensitive data

## 🚀 Release Process

### Version Numbering
Follow Semantic Versioning (SemVer):
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes (backward compatible)

### Release Checklist
- [ ] All tests passing
- [ ] Documentation updated
- [ ] CHANGELOG updated
- [ ] Version bumped
- [ ] Release notes prepared
- [ ] Deployment tested

## 📞 Getting Help

### Communication Channels
- **GitHub Discussions**: General questions and discussions
- **GitHub Issues**: Bug reports and feature requests
- **Discord**: Real-time chat with the community
- **Email**: security@fuschia.io for security issues

### Mentorship
New contributors can request mentorship for:
- Understanding the codebase
- Learning development practices
- Getting help with first contributions

## 🎉 Recognition

### Contributors
All contributors are recognized in:
- README contributors section
- Release notes
- Annual contributor report

### Rewards
- Contributor badges
- Early access to new features
- Invitation to contributor events
- Swag for significant contributions

## 📋 Contributor License Agreement

By contributing to Fuschia, you agree that:
- Your contributions are your original work
- You grant us rights to use your contributions
- Your contributions are provided under the MIT license

---

Thank you for contributing to Fuschia! Together, we're building the future of intelligent automation. 🚀