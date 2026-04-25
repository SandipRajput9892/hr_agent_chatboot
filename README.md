# HR AI Agent

An AI-powered HR assistant built with FastAPI that handles policy Q&A, leave management, and employee information through a conversational interface.

## Features

- **Policy Q&A** — Ask questions about company HR policies; answers are retrieved from uploaded PDF documents via RAG (ChromaDB + cosine similarity search)
- **Leave Management** — Submit, track, and approve/reject leave requests with automatic balance deduction and restoration
- **Employee Info** — Look up employee profiles and leave balances
- **Web Search** — Real-time DuckDuckGo search for current information
- **Session Continuity** — Cookie-based sessions with 20-message history per user

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI + Uvicorn |
| LLM | Groq (`llama-3.3-70b-versatile`) |
| Vector Store | ChromaDB (cosine similarity) |
| Database | PostgreSQL + SQLAlchemy ORM |
| PDF Parsing | PyMuPDF |
| Web Search | DuckDuckGo Search |
| Config | Pydantic Settings + python-dotenv |

## Project Structure

```
hr-ai-agent/
├── app/
│   ├── main.py                 # App entry point, CORS, router registration
│   ├── api/
│   │   ├── routes.py           # Public endpoints (chat, upload-pdf, health)
│   │   └── admin.py            # Admin CRUD (employees, leave requests)
│   ├── agents/
│   │   └── hr_agent.py         # Groq agent with tool-calling loop (max 10 iterations)
│   ├── db/
│   │   ├── database.py         # SQLAlchemy engine & session
│   │   ├── models.py           # Employee, LeaveBalance, LeaveRequest models
│   │   ├── vector_store.py     # ChromaDB client & upsert/query operations
│   │   └── embeddings.py       # Embedding function config
│   ├── services/
│   │   └── chat_service.py     # Session management & message processing
│   ├── tools/
│   │   ├── rag_tool.py         # Policy search via vector store
│   │   ├── llm_tool.py         # Employee & leave DB queries
│   │   ├── calculator.py       # Working day calculation (Mon–Fri)
│   │   └── web_search_tool.py  # DuckDuckGo integration with retry
│   ├── utils/
│   │   └── prompt_builder.py   # System prompt construction
│   └── core/
│       ├── config.py           # Pydantic settings
│       └── logger.py           # Structured logging setup
├── scripts/
│   └── ingest.py               # Load sample HR policies into ChromaDB
├── tests/
│   └── test_rag.py
├── chroma_db/                  # ChromaDB persistent storage
├── .env
└── requirements.txt
```

## Setup

### Prerequisites

- Python 3.8+
- PostgreSQL
- Groq API key (get one at [console.groq.com](https://console.groq.com))

### Installation

```bash
git clone <repo-url>
cd hr-ai-agent
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=gsk_xxxxxxxxxxxxx
MODEL_NAME=llama-3.3-70b-versatile
DATABASE_URL=postgresql://hr_user:admin123@localhost:5432/hr_agent_db
```

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROQ_API_KEY` | Yes | — | Groq API authentication |
| `MODEL_NAME` | No | `llama-3.3-70b-versatile` | LLM model identifier |
| `DATABASE_URL` | Yes | — | PostgreSQL connection string |
| `GEMINI_API_KEY` | No | None | Optional Google Generative AI key |
| `CHROMA_DB_PATH` | No | `./chroma_db` | ChromaDB storage directory |
| `MAX_TOKENS` | No | `2048` | Max tokens per LLM response |
| `MAX_ITERATIONS` | No | `10` | Max tool-calling iterations per chat turn |
| `TOP_K_RESULTS` | No | `3` | Documents retrieved per policy search |

### Database Setup

Tables are created automatically on startup. You only need to create the database and user:

```bash
psql -U postgres -c "CREATE USER hr_user WITH PASSWORD 'admin123';"
psql -U postgres -c "CREATE DATABASE hr_agent_db OWNER hr_user;"
```

### Ingest HR Policies

Load the built-in sample policies into ChromaDB (run once after setup):

```bash
python -m scripts.ingest
```

This seeds 12 policy documents covering annual/sick/casual/maternity/paternity leave, WFH, code of conduct, compensation, benefits, and performance reviews.

### Run the Server

```bash
# Development (auto-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

API docs: `http://localhost:8000/docs`

## API Reference

### Public Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/health` | Health check — returns model name and timestamp |
| `POST` | `/api/v1/chat` | Send a message to the HR agent |
| `POST` | `/api/v1/upload-pdf` | Upload and ingest an HR policy PDF |

**Chat request:**
```json
{
  "message": "How many casual leaves do I have?",
  "employee_id": "EMP001"
}
```

**Chat response:**
```json
{
  "response": "You have 4 casual leave days remaining.",
  "session_id": "uuid",
  "employee_id": "EMP001",
  "timestamp": "2026-04-25T10:00:00Z"
}
```

### Admin Endpoints (`/api/v1/admin`)

**Employees**

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/employees` | Add a new employee |
| `GET` | `/employees` | List all active employees |
| `DELETE` | `/employees/{employee_id}` | Deactivate an employee (soft delete) |

**Leave Balances**

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/employees/{employee_id}/leave-balance` | Get leave balance |
| `PUT` | `/employees/{employee_id}/leave-balance` | Update leave balance |

**Leave Requests**

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/leave-requests?status=pending\|approved\|rejected\|all` | List leave requests |
| `PUT` | `/leave-requests/{request_id}` | Approve or reject a request |

## Agent Tools

The agent selects and calls these tools automatically during a conversation:

| Tool | Description |
|------|-------------|
| `search_hr_policy` | Semantic search over policy documents in ChromaDB |
| `get_employee_info` | Fetch employee profile from the database |
| `get_leave_balance` | Get current annual/sick/casual leave balance |
| `submit_leave_request` | Submit a leave request with balance validation |
| `get_leave_requests` | Retrieve an employee's leave history |
| `calculate_working_days` | Count Mon–Fri working days between two dates |
| `web_search` | DuckDuckGo search for real-time information |

## Leave Policy Defaults

| Type | Days | Notes |
|------|------|-------|
| Annual | 12–18/year | Based on tenure |
| Sick | 10/year | Medical certificate required for >3 consecutive days |
| Casual | 5/year | Max 2 consecutive days; non-encashable |
| Maternity | 26 weeks | First 2 children |
| Paternity | 15 days | — |

## Running Tests

```bash
pytest tests/ -v
```
