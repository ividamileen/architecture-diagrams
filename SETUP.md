# Setup Guide

This guide provides detailed instructions for setting up the Architecture Diagram Generator.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Quick Start with Docker](#quick-start-with-docker)
- [Development Setup](#development-setup)
- [Teams Bot Setup](#teams-bot-setup)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required
- **Docker** (20.10+) and **Docker Compose** (2.0+)
- **API Key**: Either Anthropic or OpenAI API key
  - Get Anthropic key: https://console.anthropic.com/
  - Get OpenAI key: https://platform.openai.com/

### Optional (for Teams Bot)
- **Azure Account** for Bot Service registration
- **Microsoft Teams** admin access

## Quick Start with Docker

### 1. Clone and Configure

```bash
# Clone repository
git clone <repository-url>
cd architecture-diagrams

# Copy environment template
cp backend/.env.example backend/.env
```

### 2. Configure Environment Variables

Edit `backend/.env`:

```env
# Required: Choose ONE provider and add key
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx  # Recommended
# OR
OPENAI_API_KEY=sk-xxxxx

LLM_PROVIDER=anthropic  # or 'openai'

# Database (works with Docker Compose defaults)
DATABASE_URL=postgresql://user:password@postgres:5432/architecture_diagrams
SECRET_KEY=change-this-to-secure-random-string
```

### 3. Start Services

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend
```

### 4. Access Application

- **Web App**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Development Setup

For local development without Docker:

### Backend Setup

```bash
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your settings

# Start database services
docker-compose up -d postgres redis

# Run migrations
alembic upgrade head

# Start development server
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Access at: http://localhost:3000

## Teams Bot Setup

### Step 1: Register Bot in Azure

1. Go to **Azure Portal** → **Bot Services**
2. Click **Create** → **Bot Channels Registration**
3. Fill in details:
   - **Bot handle**: Choose unique name
   - **Subscription**: Select subscription
   - **Resource group**: Create or select
   - **Pricing tier**: F0 (free) for development
4. Click **Create** and wait for deployment

### Step 2: Get Credentials

1. Go to your bot resource
2. Navigate to **Configuration** → **Settings**
3. Copy:
   - **Microsoft App ID** (this is `TEAMS_APP_ID`)
   - Click **Manage** next to App ID
   - Create **New client secret** (this is `TEAMS_APP_PASSWORD`)
   - Save both values

### Step 3: Configure Bot Endpoint

1. In Bot Channels Registration settings:
2. Set **Messaging endpoint** to: `https://your-domain.com/api/messages`
   - For local development with ngrok: `https://xxx.ngrok.io/api/messages`

### Step 4: Configure Environment

Add to `backend/.env`:

```env
TEAMS_APP_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
TEAMS_APP_PASSWORD=your-client-secret-value
TEAMS_TENANT_ID=your-tenant-id  # Optional
```

### Step 5: Create Teams App Manifest

Create `teams-manifest.json`:

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/teams/v1.16/MicrosoftTeams.schema.json",
  "manifestVersion": "1.16",
  "version": "1.0.0",
  "id": "YOUR_APP_ID_HERE",
  "packageName": "com.example.architecturediagrambot",
  "developer": {
    "name": "Your Company",
    "websiteUrl": "https://example.com",
    "privacyUrl": "https://example.com/privacy",
    "termsOfUseUrl": "https://example.com/terms"
  },
  "name": {
    "short": "DiagramBot",
    "full": "Architecture Diagram Generator Bot"
  },
  "description": {
    "short": "AI-powered architecture diagram generator",
    "full": "Automatically detects technical conversations and generates editable architecture diagrams"
  },
  "icons": {
    "outline": "outline.png",
    "color": "color.png"
  },
  "accentColor": "#0EA5E9",
  "bots": [
    {
      "botId": "YOUR_BOT_ID_HERE",
      "scopes": ["team", "personal", "groupchat"],
      "supportsFiles": false,
      "isNotificationOnly": false,
      "commandLists": [
        {
          "scopes": ["team", "personal", "groupchat"],
          "commands": [
            {
              "title": "status",
              "description": "Show current detection status"
            },
            {
              "title": "generate",
              "description": "Force diagram generation"
            },
            {
              "title": "help",
              "description": "Show help message"
            }
          ]
        }
      ]
    }
  ],
  "permissions": ["identity", "messageTeamMembers"],
  "validDomains": ["*.ngrok.io", "your-domain.com"]
}
```

### Step 6: Deploy Bot

```bash
# Using Docker Compose
docker-compose up -d teams-bot

# Or run directly
python -m backend.bot.teams_app
```

### Step 7: Upload to Teams

1. Zip the manifest and icons:
   ```bash
   zip teams-app.zip teams-manifest.json outline.png color.png
   ```

2. In Teams:
   - Go to **Apps** → **Manage your apps**
   - Click **Upload an app** → **Upload a custom app**
   - Select `teams-app.zip`
   - Add bot to a team or channel

### Step 8: Test Bot

In Teams channel:
```
@DiagramBot help
```

## Local Development with ngrok

For Teams bot development, expose local server:

```bash
# Install ngrok
brew install ngrok  # macOS
# or download from https://ngrok.com/

# Start backend
docker-compose up backend

# Expose port
ngrok http 3978

# Copy HTTPS URL (e.g., https://xxx.ngrok.io)
# Update bot endpoint in Azure Portal
```

## Database Migrations

### Create Migration

```bash
cd backend
alembic revision --autogenerate -m "Description of changes"
```

### Apply Migrations

```bash
# Upgrade to latest
alembic upgrade head

# Downgrade one version
alembic downgrade -1

# View migration history
alembic history
```

## Production Deployment

### 1. Environment Setup

```env
# Production settings
API_RELOAD=false
DATABASE_URL=postgresql://user:password@prod-db:5432/architecture_diagrams
SECRET_KEY=<generate-secure-64-char-string>

# Use production LLM settings
LLM_MODEL=claude-3-5-sonnet-20241022
TECHNICAL_CONFIDENCE_THRESHOLD=0.7
```

### 2. Build Production Images

```bash
docker-compose -f docker-compose.yml build
```

### 3. Deploy

```bash
docker-compose up -d
```

### 4. Set Up HTTPS

Use nginx or traefik as reverse proxy:

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/v1/messages/ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Verification Checklist

After setup, verify:

- [ ] Backend health check responds: `curl http://localhost:8000/health`
- [ ] Frontend loads: Open http://localhost:3000
- [ ] Database connected: Check backend logs for "Database tables created"
- [ ] Can send messages in web app
- [ ] Technical messages detected with confidence scores
- [ ] Diagrams generated after 3+ technical messages
- [ ] Can edit diagrams in code view
- [ ] Can download PNG/PlantUML/Draw.io files
- [ ] (Teams) Bot responds to `@DiagramBot help`
- [ ] (Teams) Bot detects conversations and generates diagrams

## Common Issues

### Port Conflicts

```bash
# Check what's using ports
lsof -i :8000
lsof -i :3000
lsof -i :5432

# Stop conflicting services or change ports in docker-compose.yml
```

### Database Issues

```bash
# Reset database
docker-compose down -v
docker-compose up -d postgres
```

### Permission Issues

```bash
# Fix diagram storage permissions
sudo chmod -R 777 diagrams/

# Or in Docker
docker-compose exec backend chmod -R 777 /app/diagrams
```

### PlantUML Not Working

```bash
# Install PlantUML manually
wget -O /usr/local/bin/plantuml.jar \
  https://github.com/plantuml/plantuml/releases/download/v1.2023.13/plantuml-1.2023.13.jar

# Test PlantUML
java -jar /usr/local/bin/plantuml.jar -version
```

## Getting Help

If you encounter issues:

1. Check logs: `docker-compose logs -f [service]`
2. Verify environment variables: `docker-compose config`
3. Review troubleshooting section in README.md
4. Open an issue on GitHub with:
   - Error messages
   - Steps to reproduce
   - Environment details (OS, Docker version, etc.)
