# Contributing to Vectory

Thank you for your interest in contributing to Vectory!

## Reporting Bugs

- Use GitHub issues
- Include detailed steps to reproduce
- Provide environment details (OS, Python version, Docker version)
- Include error messages and logs

## Suggesting Features

- Use GitHub issues with "enhancement" label
- Describe the use case
- Explain why it would be useful
- Consider implementation complexity

## Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Write/update tests
5. Ensure tests pass: `pytest` (backend), `npm test` (frontend)
6. Format code: `black .` and `ruff check .` (backend)
7. Commit using Conventional Commits: `git commit -m "feat: add amazing feature"`
8. Push: `git push origin feature/amazing-feature`
9. Open a Pull Request

## Commit Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting)
- `refactor:` - Code refactoring
- `test:` - Test updates
- `chore:` - Maintenance tasks
- `perf:` - Performance improvements

## Code Style

**Python:**
- Use Black for formatting
- Use Ruff for linting
- Type hints required
- Docstrings for all public functions
- Follow PEP 8

**TypeScript:**
- Use Prettier for formatting
- ESLint for linting
- Strict mode enabled
- Meaningful variable names

## Testing

- Write tests for new features
- Ensure >80% code coverage
- Use descriptive test names
- Test edge cases
- Backend: `pytest tests/`
- Frontend: `npm test`

## Development Setup

```bash
# Clone your fork
git clone https://github.com/your-username/vectory.git
cd vectory

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install

# Start services
docker-compose up -d postgres redis minio
```

## Documentation

- Update API docs for endpoint changes
- Add docstrings to new functions
- Update README for major features
- Create examples for new capabilities

## Questions?

Open an issue with the "question" label or join our community discussions.

Thank you for contributing!
