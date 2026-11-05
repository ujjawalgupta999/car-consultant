# AMULATE SUMMER HACKATHON 2026: DEPLOYMENT SPECIFICATION
## AI-Powered Car Rental and Purchase Consultant

---

## 1. Overview
The application supports two primary deployment topologies:
1. **Containerized Production (Docker & Docker Compose)**: Multi-container setup with frontend, backend, and MongoDB.
2. **Local Development (Split Process)**: Standalone Vite dev server + FastAPI ASGI server, with automatic JSON fallback if MongoDB is not started.

---

## 2. Docker Architecture

### 2.1 Services Overview (`docker-compose.yml`)

| Service | Image / Build | Port | Internal Role |
|---------|---------------|------|---------------|
| `backend` | `./backend/Dockerfile` | `8000:8000` | FastAPI ASGI Server, MCP Server, Orchestration |
| `frontend` | `./frontend/Dockerfile` | `3000:80` | Nginx serving built React/Vite assets & reverse proxying `/api` |
| `mongodb` | `mongo:7.0` | `27017:27017` | Persistent vehicle, session, and booking storage |

### 2.2 Health Checks
- Backend health check: `GET http://localhost:8000/health` (checks status and marketplace listing count).
- Frontend health check: `GET http://localhost:80/` (checks web server response).
- MongoDB health check: `mongosh --eval "db.adminCommand('ping')"`

---

## 3. Environment Variables Configuration

### 3.1 Backend Configuration (`.env`)
```bash
# Application Mode
ENVIRONMENT=development
AGENT_MODE=mock              # 'mock' (default, deterministic offline) or 'openai'
STORAGE_BACKEND=auto         # 'auto' tries MongoDB then falls back to JSON, or 'mongodb', 'json'

# Networking
PORT=8000
HOST=0.0.0.0
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Database
MONGODB_URI=mongodb://mongodb:27017/car_consultant

# Optional AI Credentials (leave empty for deterministic mock mode)
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o

# Optional Observability (leave empty to disable)
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_HOST=https://cloud.langfuse.com
```

### 3.2 Frontend Configuration (`.env`)
```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_TITLE="Amulate AI Car Consultant"
```

---

## 4. Run Commands

### 4.1 Running with Docker Compose
```bash
# Build and start all services in detached mode
docker compose up --build -d

# Check running container status
docker compose ps

# View backend logs
docker compose logs -f backend

# Stop services
docker compose down
```

### 4.2 Running Locally Without Docker
1. **Backend**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Or `venv\Scripts\activate` on Windows
   pip install -r requirements.txt
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Frontend**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   Access frontend at `http://localhost:5173`.

