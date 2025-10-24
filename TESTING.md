# Testing Guide

This guide covers all aspects of testing the Architecture Diagram Generator system.

## Table of Contents

- [Overview](#overview)
- [Backend Testing](#backend-testing)
- [Frontend Testing](#frontend-testing)
- [Integration Testing](#integration-testing)
- [CI/CD Pipeline](#cicd-pipeline)
- [Coverage Reports](#coverage-reports)
- [Writing Tests](#writing-tests)

## Overview

The project uses comprehensive testing at multiple levels:

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test API endpoints and service interactions
- **End-to-End Tests**: Test complete user workflows (via CI/CD)
- **Coverage**: Aim for >80% code coverage

### Test Technology Stack

**Backend:**
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Coverage reporting
- `pytest-mock` - Mocking utilities

**Frontend:**
- `vitest` - Fast Vite-native testing framework
- `@testing-library/react` - React component testing
- `@testing-library/user-event` - User interaction simulation
- `@testing-library/jest-dom` - DOM matchers

## Backend Testing

### Running Backend Tests

```bash
# Navigate to backend directory
cd backend

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_conversation_analyzer.py

# Run tests by marker
pytest -m unit              # Unit tests only
pytest -m integration       # Integration tests only

# Run with coverage
pytest --cov=backend --cov-report=html --cov-report=term-missing

# Run specific test class
pytest tests/test_models.py::TestConversationModel

# Run specific test method
pytest tests/test_models.py::TestConversationModel::test_create_conversation
```

### Backend Test Structure

```
backend/tests/
├── conftest.py                     # Shared fixtures and configuration
├── test_conversation_analyzer.py    # AI conversation analysis tests
├── test_diagram_generators.py       # PlantUML/Draw.io generator tests
├── test_api_endpoints.py            # API integration tests
├── test_services.py                 # Service layer tests
└── test_models.py                   # Database model tests
```

### Backend Test Examples

#### Unit Test Example
```python
import pytest
from backend.ai.conversation_analyzer import ConversationAnalyzer

@pytest.mark.unit
@pytest.mark.asyncio
async def test_analyze_technical_message(analyzer):
    """Test analyzing a technical message"""
    result = await analyzer.analyze_message(
        message="We need an API gateway with PostgreSQL",
        context=[]
    )

    assert result.is_technical is True
    assert result.confidence_score > 0.7
```

#### Integration Test Example
```python
@pytest.mark.integration
def test_create_conversation(client):
    """Test creating a conversation via API"""
    response = client.post(
        "/api/v1/conversations/",
        json={"platform": "web"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["platform"] == "web"
```

### Fixtures

Common fixtures available in `conftest.py`:

- `db` - Database session for tests
- `client` - FastAPI test client
- `sample_conversation_data` - Sample conversation data
- `sample_message_data` - Sample message data
- `sample_technical_messages` - List of technical messages
- `sample_architecture_extraction` - Sample architecture data
- `mock_llm_response` - Mocked LLM response

### Mocking LLM Calls

Tests mock LLM API calls to avoid actual API usage:

```python
from unittest.mock import Mock, patch

@pytest.mark.asyncio
async def test_with_mocked_llm(analyzer):
    """Test with mocked LLM response"""
    mock_response = Mock()
    mock_response.content = '{"is_technical": true, "confidence_score": 0.85}'

    with patch.object(analyzer.llm, 'ainvoke', return_value=mock_response):
        result = await analyzer.analyze_message("Test", [])
        assert result.is_technical is True
```

## Frontend Testing

### Running Frontend Tests

```bash
# Navigate to frontend directory
cd frontend

# Run all tests
npm test

# Run in watch mode (default)
npm test

# Run tests with UI
npm run test:ui

# Run with coverage
npm run test:coverage

# Run specific test file
npm test -- src/tests/components/ChatInterface.test.tsx

# Update snapshots
npm test -- -u
```

### Frontend Test Structure

```
frontend/src/tests/
├── setup.ts                        # Test setup and global config
├── components/
│   └── ChatInterface.test.tsx      # Component tests
├── services/
│   └── api.test.ts                 # API service tests
└── hooks/
    └── useWebSocket.test.ts        # Custom hook tests
```

### Frontend Test Examples

#### Component Test Example
```typescript
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ChatInterface } from '../../components/ChatInterface'

describe('ChatInterface', () => {
  it('renders chat interface', () => {
    render(
      <ChatInterface
        conversationId={1}
        messages={[]}
        onMessageSent={vi.fn()}
        onDiagramGenerationStarted={vi.fn()}
      />
    )

    expect(screen.getByPlaceholderText(/type your message/i)).toBeInTheDocument()
  })
})
```

#### User Interaction Test
```typescript
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

it('allows user to type message', async () => {
  render(<ChatInterface {...props} />)

  const input = screen.getByPlaceholderText(/type your message/i)
  await userEvent.type(input, 'New message')

  expect(input).toHaveValue('New message')
})
```

#### Service Test Example
```typescript
import { describe, it, expect, vi } from 'vitest'
import axios from 'axios'
import { messagesApi } from '../../services/api'

vi.mock('axios')

describe('messagesApi', () => {
  it('creates a message', async () => {
    const mockMessage = { id: 1, content: 'Test' }

    vi.mocked(axios.create).mockReturnValue({
      post: vi.fn().mockResolvedValue({ data: mockMessage }),
    } as any)

    const result = await messagesApi.create({ content: 'Test', user_id: '1' })
    expect(result).toEqual(mockMessage)
  })
})
```

## Integration Testing

### Docker Compose Integration Tests

Run full system integration tests:

```bash
# Start all services
docker-compose up -d

# Wait for services to be ready
sleep 10

# Run integration tests
docker-compose exec backend pytest tests/test_api_endpoints.py -v -m integration

# Stop services
docker-compose down -v
```

### Manual Integration Testing

1. **Start Services:**
   ```bash
   docker-compose up -d
   ```

2. **Test Health Endpoint:**
   ```bash
   curl http://localhost:8000/health
   ```

3. **Test Creating Conversation:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/conversations/ \
     -H "Content-Type: application/json" \
     -d '{"platform": "web"}'
   ```

4. **Test Creating Message:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/messages/ \
     -H "Content-Type: application/json" \
     -d '{
       "content": "We need an API gateway with PostgreSQL",
       "user_id": "test-user",
       "platform": "web"
     }'
   ```

5. **Access Frontend:**
   ```bash
   open http://localhost:3000
   ```

## CI/CD Pipeline

### GitHub Actions Workflows

The project includes automated testing via GitHub Actions:

**CI Workflow** (`.github/workflows/ci.yml`):
- Runs on every push and PR
- Executes backend unit tests
- Executes frontend tests
- Builds Docker images
- Runs integration tests
- Performs security scanning
- Uploads coverage reports

**Deploy Workflow** (`.github/workflows/deploy.yml`):
- Deploys to staging on main branch
- Requires manual approval for production
- Builds and pushes Docker images
- Deploys to servers via SSH

### Running CI Locally

You can run CI checks locally before pushing:

```bash
# Backend tests
cd backend
pytest --cov=backend --cov-report=term-missing

# Frontend tests
cd frontend
npm run test:coverage

# Linting
cd backend
black --check .
flake8 .

cd frontend
npm run lint
npx tsc --noEmit

# Build Docker images
docker build -t backend:test ./backend
docker build -t frontend:test ./frontend
```

### CI Pipeline Stages

```
1. Backend Tests
   ├── Set up Python 3.11
   ├── Install dependencies
   ├── Run pytest with coverage
   └── Upload coverage to Codecov

2. Frontend Tests
   ├── Set up Node.js 18
   ├── Install dependencies
   ├── Run linter
   ├── Run vitest with coverage
   └── Upload coverage to Codecov

3. Build Backend
   ├── Set up Docker Buildx
   └── Build backend Docker image

4. Build Frontend
   ├── Set up Docker Buildx
   └── Build frontend Docker image

5. Integration Tests
   ├── Start services with docker-compose
   ├── Wait for health checks
   ├── Run integration test suite
   └── Stop services

6. Lint and Type Check
   ├── Run black (Python formatter)
   ├── Run flake8 (Python linter)
   └── Run TypeScript type check

7. Security Scan
   └── Run Trivy vulnerability scanner
```

## Coverage Reports

### Backend Coverage

```bash
cd backend

# Generate HTML coverage report
pytest --cov=backend --cov-report=html

# Open report
open htmlcov/index.html

# Generate XML for CI
pytest --cov=backend --cov-report=xml

# Show missing lines
pytest --cov=backend --cov-report=term-missing
```

### Frontend Coverage

```bash
cd frontend

# Generate coverage report
npm run test:coverage

# Open HTML report
open coverage/index.html
```

### Coverage Goals

- **Overall:** >80% code coverage
- **Critical Paths:** >90% (AI analysis, diagram generation)
- **API Endpoints:** >85%
- **Services:** >80%
- **Models:** >75%
- **Frontend Components:** >70%

### Viewing Coverage in CI

Coverage reports are uploaded to Codecov:
- View at: https://codecov.io/gh/your-org/architecture-diagrams
- PRs show coverage diff
- Badges available for README

## Writing Tests

### Best Practices

1. **Follow AAA Pattern:**
   ```python
   def test_example():
       # Arrange
       data = create_test_data()

       # Act
       result = perform_action(data)

       # Assert
       assert result == expected
   ```

2. **Use Descriptive Names:**
   ```python
   # Good
   def test_technical_message_detection_with_high_confidence():
       ...

   # Bad
   def test_1():
       ...
   ```

3. **Test One Thing:**
   ```python
   # Good - tests one behavior
   def test_create_conversation_returns_id():
       conversation = create_conversation()
       assert conversation.id is not None

   # Bad - tests multiple things
   def test_conversation():
       conversation = create_conversation()
       assert conversation.id is not None
       assert conversation.platform == "web"
       message = add_message()
       assert message.id is not None
   ```

4. **Use Fixtures for Setup:**
   ```python
   @pytest.fixture
   def conversation(db):
       return create_conversation(db, platform="web")

   def test_add_message(conversation, db):
       message = add_message(db, conversation.id, "Test")
       assert message.conversation_id == conversation.id
   ```

5. **Mock External Dependencies:**
   ```python
   @patch('backend.ai.conversation_analyzer.ChatAnthropic')
   def test_analyzer(mock_llm):
       analyzer = ConversationAnalyzer()
       # Test without calling actual LLM API
   ```

### Adding New Tests

#### Backend Test

1. Create test file in `backend/tests/`:
   ```python
   # test_new_feature.py
   import pytest

   @pytest.mark.unit
   class TestNewFeature:
       def test_basic_functionality(self):
           # Test implementation
           pass
   ```

2. Run the test:
   ```bash
   pytest tests/test_new_feature.py -v
   ```

#### Frontend Test

1. Create test file in `frontend/src/tests/`:
   ```typescript
   // NewComponent.test.tsx
   import { describe, it, expect } from 'vitest'
   import { render, screen } from '@testing-library/react'
   import { NewComponent } from '../../components/NewComponent'

   describe('NewComponent', () => {
     it('renders correctly', () => {
       render(<NewComponent />)
       expect(screen.getByText('Expected text')).toBeInTheDocument()
     })
   })
   ```

2. Run the test:
   ```bash
   npm test -- NewComponent.test.tsx
   ```

## Troubleshooting Tests

### Backend Issues

**Issue: Database connection errors**
```bash
# Ensure PostgreSQL is running
docker-compose up -d postgres

# Check DATABASE_URL in .env or use in-memory SQLite for tests
```

**Issue: Import errors**
```bash
# Ensure you're in the backend directory
cd backend

# Install dependencies
pip install -r requirements.txt
```

**Issue: Async test failures**
```python
# Ensure async tests use @pytest.mark.asyncio
@pytest.mark.asyncio
async def test_async_function():
    result = await async_operation()
    assert result is not None
```

### Frontend Issues

**Issue: Module not found**
```bash
# Reinstall dependencies
cd frontend
rm -rf node_modules
npm install
```

**Issue: TypeScript errors in tests**
```typescript
// Add proper types
import type { Message } from '../../types'

const mockMessage: Message = {
  // ... proper typing
}
```

**Issue: Component not rendering**
```typescript
// Check if component needs providers
import { BrowserRouter } from 'react-router-dom'

render(
  <BrowserRouter>
    <YourComponent />
  </BrowserRouter>
)
```

## Pre-commit Checks

Run these before committing:

```bash
# Backend
cd backend
black .
flake8 .
pytest

# Frontend
cd frontend
npm run lint
npm test
npx tsc --noEmit

# Both
docker-compose build
```

## Continuous Improvement

- Review coverage reports weekly
- Add tests for bug fixes
- Maintain >80% coverage
- Update tests when refactoring
- Document complex test scenarios

---

For more information:
- Backend testing: `backend/tests/README.md`
- Frontend testing: `frontend/src/tests/README.md`
- CI/CD: `.github/workflows/README.md`
