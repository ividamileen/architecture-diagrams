# AI-Powered Architecture Diagram Generator

An intelligent system that automatically detects technical conversations and generates editable architecture diagrams. Works as both a standalone web application and a Microsoft Teams bot.

## Features

- 🤖 **AI-Powered Detection**: Automatically identifies technical and architectural discussions
- 📊 **Dual Format Support**: Generates diagrams in both PlantUML and Draw.io formats
- 🖼️ **PNG Export**: Automatic PNG rendering for easy sharing
- ✏️ **Live Editing**: Monaco editor for direct code editing with syntax highlighting
- 🗣️ **Natural Language Modifications**: Request diagram changes using plain English
- 💬 **Real-time Chat**: WebSocket-based chat interface with technical confidence indicators
- 🤝 **Teams Integration**: Full Microsoft Teams bot with adaptive cards
- 📦 **Easy Deployment**: Docker Compose setup for quick deployment

## Architecture

```
┌─────────────────┐     ┌─────────────────┐
│  Web Frontend   │     │  Teams Bot      │
│  (React + TS)   │     │  (Python)       │
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     │
              ┌──────▼──────┐
              │   FastAPI   │
              │   Backend   │
              └──────┬──────┘
                     │
        ┏━━━━━━━━━━━━┻━━━━━━━━━━━━┓
        ┃                          ┃
   ┌────▼────┐              ┌──────▼──────┐
   │  LLM    │              │  PostgreSQL │
   │  (GPT/  │              │   + Redis   │
   │ Claude) │              └─────────────┘
   └─────────┘
```

## Tech Stack

### Backend
- **Python 3.11+** with FastAPI
- **LangChain** for conversation analysis
- **OpenAI / Anthropic** for LLM processing
- **PostgreSQL** for data persistence
- **Redis** for caching
- **PlantUML** for diagram generation
- **Bot Framework SDK** for Teams integration

### Frontend
- **React 18** with TypeScript
- **TailwindCSS** for styling
- **Monaco Editor** for code editing
- **WebSocket** for real-time updates
- **Vite** for build tooling

## Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenAI or Anthropic API key
- (Optional) Microsoft Teams app credentials for bot integration

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd architecture-diagrams
   ```

2. **Set up environment variables**
   ```bash
   cp backend/.env.example backend/.env
   ```

3. **Configure your API keys in `backend/.env`**
   ```env
   # Required
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   # OR
   OPENAI_API_KEY=your_openai_api_key_here

   # Choose provider
   LLM_PROVIDER=anthropic  # or 'openai'

   # Database (default values work with docker-compose)
   DATABASE_URL=postgresql://user:password@postgres:5432/architecture_diagrams
   SECRET_KEY=your-secret-key-change-in-production

   # Optional: Teams Bot (only if using Teams integration)
   TEAMS_APP_ID=your_teams_app_id
   TEAMS_APP_PASSWORD=your_teams_app_password
   ```

4. **Start the services**
   ```bash
   docker-compose up -d
   ```

5. **Access the application**
   - Web App: http://localhost:3000
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Development Setup (Without Docker)

1. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt

   # Set up database
   alembic upgrade head

   # Run the server
   uvicorn backend.main:app --reload
   ```

2. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Database Setup**
   ```bash
   # Start PostgreSQL and Redis
   docker-compose up -d postgres redis
   ```

## Usage

### Web Application

1. **Start a Conversation**: Open the web app and start typing messages in the chat interface.

2. **Technical Detection**: As you discuss technical topics, the system will automatically:
   - Analyze each message for technical content
   - Display confidence scores
   - Highlight technical messages

3. **Diagram Generation**: After 3+ high-confidence technical messages, the system will:
   - Automatically generate an architecture diagram
   - Display it in the right panel
   - Provide both PlantUML and Draw.io versions

4. **Edit Diagrams**:
   - Switch to "Code" view to edit PlantUML or Draw.io code directly
   - Use Monaco editor with syntax highlighting
   - Save to regenerate PNG preview

5. **Natural Language Modifications**:
   - Type modifications like "Add Redis cache between API and database"
   - System will update the diagram accordingly
   - Creates new version while preserving history

### Microsoft Teams Bot

#### Setup Teams Bot

1. **Register your bot** in Azure Bot Service
2. **Configure credentials** in `.env`:
   ```env
   TEAMS_APP_ID=your_app_id
   TEAMS_APP_PASSWORD=your_app_password
   ```

3. **Start the bot service**:
   ```bash
   docker-compose up teams-bot
   ```

4. **Add bot to Teams** using your app manifest

#### Using the Teams Bot

**Available Commands**:
- `@DiagramBot status` - Show current detection status
- `@DiagramBot generate` - Force diagram generation
- `@DiagramBot modify [description]` - Request modifications
- `@DiagramBot help` - Show help message

**Automatic Features**:
- Monitors channel conversations in real-time
- Detects technical discussions automatically
- Posts adaptive cards when diagrams are generated
- Provides links to view/edit diagrams in web app

**Example Interaction**:
```
User 1: We need to build a new API gateway
User 2: It should route to our auth service and user service
User 3: And connect to PostgreSQL for session storage

DiagramBot: 🎨 I've detected an architecture discussion! Generating diagram...

[Adaptive Card with diagram preview and action buttons]
```

## API Documentation

### REST API Endpoints

#### Conversations
- `POST /api/v1/conversations/` - Create conversation
- `GET /api/v1/conversations/{id}` - Get conversation

#### Messages
- `POST /api/v1/messages/` - Send message
- `GET /api/v1/messages/conversation/{id}` - Get messages
- `GET /api/v1/messages/conversation/{id}/technical` - Get technical messages

#### Diagrams
- `POST /api/v1/diagrams/generate` - Generate diagram
- `GET /api/v1/diagrams/{id}` - Get diagram
- `GET /api/v1/diagrams/conversation/{id}` - Get all diagrams for conversation
- `POST /api/v1/diagrams/modify` - Modify diagram
- `PUT /api/v1/diagrams/{id}/code` - Update diagram code
- `GET /api/v1/diagrams/{id}/png` - Download PNG
- `GET /api/v1/diagrams/{id}/plantuml` - Get PlantUML code
- `GET /api/v1/diagrams/{id}/drawio` - Get Draw.io XML

#### WebSocket
- `WS /api/v1/messages/ws/{conversation_id}` - Real-time updates

Full API documentation available at: http://localhost:8000/docs

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `ANTHROPIC_API_KEY` | Anthropic API key | Required (if using Anthropic) |
| `OPENAI_API_KEY` | OpenAI API key | Required (if using OpenAI) |
| `LLM_PROVIDER` | LLM provider (anthropic/openai) | `anthropic` |
| `LLM_MODEL` | Model name | `claude-3-5-sonnet-20241022` |
| `TECHNICAL_CONFIDENCE_THRESHOLD` | Threshold for technical detection | `0.7` |
| `CONVERSATION_CONTEXT_WINDOW_SIZE` | Max messages to analyze | `50` |
| `CONVERSATION_TIME_WINDOW_MINUTES` | Time window for analysis | `10` |
| `TEAMS_APP_ID` | Teams bot app ID | Optional |
| `TEAMS_APP_PASSWORD` | Teams bot password | Optional |

### Customizing Detection

Adjust technical detection sensitivity in `backend/ai/conversation_analyzer.py`:

```python
# Modify confidence threshold
settings.TECHNICAL_CONFIDENCE_THRESHOLD = 0.6  # More sensitive

# Adjust context window
settings.CONVERSATION_CONTEXT_WINDOW_SIZE = 100  # More context
```

## Project Structure

```
architecture-diagrams/
├── backend/
│   ├── api/
│   │   ├── models/          # Database models and schemas
│   │   ├── routes/          # API endpoints
│   │   └── services/        # Business logic
│   ├── ai/
│   │   ├── conversation_analyzer.py  # Technical detection
│   │   └── diagram_modifier.py      # Natural language modifications
│   ├── bot/
│   │   ├── teams_bot.py     # Teams bot logic
│   │   └── teams_app.py     # Bot server
│   ├── diagram_generator/
│   │   ├── plantuml.py      # PlantUML generation
│   │   ├── drawio.py        # Draw.io generation
│   │   └── renderer.py      # PNG rendering
│   ├── main.py              # FastAPI application
│   └── config.py            # Configuration
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services
│   │   ├── hooks/          # Custom hooks
│   │   └── types/          # TypeScript types
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml
└── README.md
```

## Testing

This project includes comprehensive testing at multiple levels with >80% code coverage.

### Quick Start

**Backend Tests:**
```bash
cd backend
pytest -v --cov=backend --cov-report=term-missing
```

**Frontend Tests:**
```bash
cd frontend
npm run test:coverage
```

**Integration Tests:**
```bash
docker-compose up -d
docker-compose exec backend pytest tests/test_api_endpoints.py -v -m integration
```

### Test Coverage

- **Backend:** Unit tests, integration tests, service tests, model tests
- **Frontend:** Component tests, hook tests, service tests
- **CI/CD:** Automated testing via GitHub Actions on every push/PR
- **Coverage Reports:** Available via Codecov and local HTML reports

### Documentation

For comprehensive testing documentation, see **[TESTING.md](TESTING.md)** which includes:
- Running tests locally
- Writing new tests
- Test structure and organization
- Mocking strategies
- CI/CD pipeline details
- Coverage reporting
- Troubleshooting guide

## Deployment

### Production Deployment

1. **Update environment variables** for production
2. **Set secure secrets**:
   ```env
   SECRET_KEY=<generate-secure-random-key>
   DATABASE_URL=<production-database-url>
   ```

3. **Build and deploy**:
   ```bash
   docker-compose -f docker-compose.yml up -d --build
   ```

4. **Set up reverse proxy** (nginx/traefik) for HTTPS

### Cloud Deployment

The application can be deployed to:
- **AWS**: ECS/EKS with RDS and ElastiCache
- **Azure**: Container Apps with Azure Database for PostgreSQL
- **GCP**: Cloud Run with Cloud SQL
- **Heroku**: Using containers

## Troubleshooting

### Common Issues

**1. PlantUML rendering fails**
```bash
# Install Java and PlantUML
apt-get install default-jre graphviz
wget https://github.com/plantuml/plantuml/releases/download/v1.2023.13/plantuml-1.2023.13.jar
```

**2. Database connection errors**
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# View logs
docker-compose logs postgres
```

**3. WebSocket connection fails**
- Check CORS configuration in `backend/config.py`
- Ensure frontend proxy is configured correctly in `frontend/vite.config.ts`

**4. Teams bot not responding**
- Verify `TEAMS_APP_ID` and `TEAMS_APP_PASSWORD` are correct
- Check bot endpoint is accessible from Teams
- Review bot logs: `docker-compose logs teams-bot`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- GitHub Issues: [Create an issue]
- Documentation: [View docs]

## Roadmap

### Current Version (MVP)
- ✅ Web application with chat interface
- ✅ PlantUML and Draw.io generation
- ✅ Natural language modifications
- ✅ Microsoft Teams bot
- ✅ Real-time WebSocket updates

### Future Enhancements
- [ ] Slack integration
- [ ] Additional diagram types (sequence, data flow, infrastructure)
- [ ] Collaborative editing
- [ ] Diagram versioning UI
- [ ] Voice transcription integration
- [ ] Export to Visio/Lucidchart
- [ ] Template library
- [ ] AI-powered diagram optimization

## Acknowledgments

- PlantUML for diagram generation
- LangChain for LLM orchestration
- FastAPI for backend framework
- React and TailwindCSS for frontend
- Microsoft Bot Framework for Teams integration
