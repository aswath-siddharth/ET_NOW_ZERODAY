# ET AI Concierge

A sophisticated **multi-agent AI system** for financial intelligence, market analysis, and personalized investment guidance powered by LangGraph and FastAPI. Built for Economic Times (ET) users with seamless voice, web, and mobile experiences.

## 🎯 Project Overview

**ET AI Concierge** is an enterprise-grade AI platform that combines:
- **Multi-Agent Orchestration**: LangGraph-powered agent framework with specialized agents for market intelligence, editorial content, user profiling, and marketplace transactions
- **Retrieval-Augmented Generation (RAG)**: Hybrid search across Qdrant vector DB and Elasticsearch for intelligent content retrieval
- **Compliance & Behavioral Monitoring**: Real-time compliance checks and behavioral profiling for regulatory adherence
- **Voice Intelligence**: Voice-to-voice interaction via Groq Whisper (STT) and Edge TTS (TTS)
- **Personalization Engine**: Dynamic user profiling with 5 persona types and progressive onboarding
- **Real-Time Market Data**: Integration with Finnhub, Yahoo Finance, and custom data feeds

### Key Capabilities
- **Chat Interface**: Web-based conversational AI with streaming responses
- **Voice Briefing**: Audio-based market updates and personalized content
- **Market Intelligence**: Real-time quotes, portfolio analysis, technical signals
- **Content Marketplace**: ELSS funds, insurance products, ET Premium content
- **User Profiling**: Xray questionnaire, persona mapping, risk scoring
- **Compliance Wrapper**: PII detection, sentiment analysis, response filtering

---

## 📁 Project Structure

```
ET_NOW_ZERODAY/
├── README.md                          # This file
├── et-ai-concierge/                   # Main monorepo
│   ├── docker-compose.yml             # Infrastructure stack
│   ├── apps/
│   │   └── web/                       # Next.js frontend
│   │       ├── package.json
│   │       ├── src/
│   │       │   ├── app/               # Next.js App Router
│   │       │   │   ├── page.tsx       # Home page
│   │       │   │   ├── layout.tsx     # Root layout
│   │       │   │   ├── api/           # API routes (proxies to backend)
│   │       │   │   │   ├── chat/
│   │       │   │   │   ├── voice-briefing/
│   │       │   │   │   └── auth/[...nextauth]/
│   │       │   │   ├── auth/          # Login page
│   │       │   │   ├── chat/          # Chat interface
│   │       │   │   ├── dashboard/     # User dashboard
│   │       │   │   ├── markets/       # Market data views
│   │       │   │   ├── marketplace/   # ELSS/Insurance marketplace
│   │       │   │   ├── profile/       # User profile editor
│   │       │   │   └── onboarding/    # Xray onboarding flow
│   │       │   ├── components/        # React components
│   │       │   │   ├── FloatingConcierge.tsx
│   │       │   │   ├── VoiceBriefingButton.tsx
│   │       │   │   └── ui/            # Radix UI components
│   │       │   └── lib/
│   │       │       └── utils.ts
│   │       ├── auth.ts                # NextAuth configuration & JWT minting
│   │       ├── middleware.ts          # Request auth middleware
│   │       └── next.config.ts         # Next.js configuration
│   ├── packages/
│   │   ├── agents/                    # Backend Python monolith
│   │   │   ├── orchestrator.py        # Agent 0: Main brain (FastAPI entry point)
│   │   │   ├── editorial_agent.py     # Agent 2: Content via RAG
│   │   │   ├── market_intelligence_agent.py  # Agent 3: Market data
│   │   │   ├── marketplace_agent.py   # Agent 4: ELSS/Insurance/Products
│   │   │   ├── profiling_agent.py     # Agent 5: User onboarding & profiling
│   │   │   ├── behavioral_monitor.py  # Agent 6: Compliance & behavior tracking
│   │   │   ├── intent_router.py       # Intent detection & upsell routing
│   │   │   ├── compliance_wrapper.py  # PII detection, sentiment filtering
│   │   │   ├── state.py               # Pydantic models & enums
│   │   │   ├── config.py              # Centralized settings (env vars)
│   │   │   ├── database.py            # PostgreSQL operations
│   │   │   ├── auth.py                # JWT validation
│   │   │   ├── rag_engine.py          # RAG query interface
│   │   │   ├── requirements.txt       # Python dependencies
│   │   │   ├── Dockerfile            # Container image
│   │   │   └── data/
│   │   │       └── seed_content.json  # Mock articles for fallback
│   │   ├── rag/                       # Retrieval-Augmented Generation
│   │   │   ├── requirements.txt
│   │   │   ├── ingestion/
│   │   │   │   ├── ingest.py          # ETL pipeline entry point
│   │   │   │   ├── et_scraper.py      # ET website scraper
│   │   │   │   ├── news_scheduler.py  # Scheduled ingestion jobs
│   │   │   │   └── __init__.py
│   │   │   ├── retrieval/
│   │   │   │   ├── hybrid_search.py   # Qdrant + Elasticsearch search
│   │   │   │   └── __init__.py
│   │   │   └── reranking/
│   │   │       ├── reranker.py        # LLM-based result reranking
│   │   │       └── __init__.py
│   │   └── voice/                     # Voice AI Pipeline
│   │       └── voice_pipeline.py      # WebSocket STT/TTS handler
│   └── scripts/
│       ├── init_db.sql                # PostgreSQL schema initialization
│       ├── ingest_et_prime.py         # One-off ingestion script
│       └── seed_personas.py           # Populate mock personas
├── .gitignore
└── .env.example
```

---

## 🏗️ Architecture

### System Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                       │
│  ├─ Web App (Chat, Markets, Dashboard, Profile)            │
│  ├─ Voice UI (Audio recording / playback)                  │
│  └─ Auth (NextAuth.js with JWT backend token minting)      │
└────────────────┬────────────────────────────────────────────┘
                 │ (HTTP/REST + WebSocket)
                 │
┌─────────────────┴────────────────────────────────────────────┐
│              API Gateway / Proxy Layer                       │
│         (Next.js API routes forward to FastAPI)             │
└────────────────┬────────────────────────────────────────────┘
                 │
┌─────────────────┴─────────────────────────────────────────────────────┐
│                  Backend Orchestrator (FastAPI)                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Agent 0: LangGraph Orchestrator (Main Router)              │   │
│  │  ├─ Receives user message / audio                           │   │
│  │  ├─ Detects intent & intent routing                         │   │
│  │  ├─ Manages multi-turn conversation state                   │   │
│  │  └─ Synthesizes agent responses                             │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌──────────────────────────┬───────────────────────────────────┐   │
│  │  Specialized Agents      │  Supporting Services              │   │
│  ├──────────────────────────┼───────────────────────────────────┤   │
│  │ Agent 2: Editorial       │  Intent Router                    │   │
│  │ (Content via RAG)        │  (Detect learn/transact/discover) │   │
│  │                          │                                   │   │
│  │ Agent 3: Market Intel    │  Compliance Wrapper              │   │
│  │ (Real-time data)         │  (PII, sentiment, filtering)     │   │
│  │                          │                                   │   │
│  │ Agent 4: Marketplace     │  Behavioral Monitor              │   │
│  │ (ELSS/Insurance/Products)│  (Tracking, paywall hits)        │   │
│  │                          │                                   │   │
│  │ Agent 5: Profiling       │  RAG Engine Interface            │   │
│  │ (Xray, personas)         │  (Retrieve + generate)           │   │
│  │                          │                                   │   │
│  │ Agent 6: Behavioral      │  LLM Clients                     │   │
│  │ (Monitoring/Compliance)  │  (OpenRouter + Groq fallback)    │   │
│  └──────────────────────────┴───────────────────────────────────┘   │
└────────┬──────────────────────────────────────────────────────────────┘
         │
    ┌────┴──────────────────────────────────────────────────────┐
    │              Persistence & Data Layer                     │
    │                                                            │
    │  ┌──────────────────────────┐  ┌──────────────────────┐  │
    │  │  PostgreSQL (et_concierge)│  │  Redis (Cache)       │  │
    │  │  ├─ Users                │  │  ├─ Sessions         │  │
    │  │  ├─ Chat history         │  │  └─ Temporary state  │  │
    │  │  ├─ Audit logs           │  └──────────────────────┘  │
    │  │  └─ Personas             │                             │
    │  └──────────────────────────┘  ┌──────────────────────┐  │
    │                                 │  Qdrant (Vector DB) │  │
    │  ┌──────────────────────────┐  │  ├─ Article embeds   │  │
    │  │ Elasticsearch (Indexed)  │  │  └─ Query vectors    │  │
    │  │ ├─ Full-text search      │  └──────────────────────┘  │
    │  │ └─ Articles, metadata    │                             │
    │  └──────────────────────────┘  ┌──────────────────────┐  │
    │                                 │  Neo4j (Graph DB)   │  │
    │                                 │  └─ Entity relations │  │
    │                                 └──────────────────────┘  │
    └────────────────────────────────────────────────────────────┘
         │
    ┌────┴──────────────────────────────────────────────┐
    │         External Services                         │
    │                                                    │
    │  ├─ Finnhub (Real-time quotes)                   │
    │  ├─ Yahoo Finance (Historical data)              │
    │  ├─ NewsAPI (News feeds)                         │
    │  ├─ DDGS (Web search fallback)                   │
    │  ├─ Groq (LLM + Whisper STT)                     │
    │  ├─ Edge TTS (Text-to-speech)                    │
    │  ├─ Google Cloud TTS (Alternative)               │
    │  └─ LangSmith (Observability)                    │
    └─────────────────────────────────────────────────┘
```

### Data Flow

1. **Web/Voice Input** → Frontend captures user intent via chat or audio
2. **Authentication** → NextAuth verifies session, mints JWT for backend
3. **Orchestrator** → Receives request, detects intent, routes to specialized agents
4. **Agent Processing** → Specialized agents query databases, APIs, or RAG engine
5. **Compliance** → Response wrapped for PII detection, sentiment filtering
6. **Response Synthesis** → Orchestrator merges agent outputs into coherent response
7. **Voice Output** → TTS synthesizes audio if requested
8. **Logging** → Audit trail, chat history, and behavioral signals stored

---

## 🔧 Core Components

### **Frontend (Next.js)**

**Technology Stack:**
- React 19.2
- Next.js 16.2 (App Router)
- TypeScript 5
- Tailwind CSS 4 + PostCSS
- Radix UI (accessible components)
- NextAuth.js 5 (authentication)
- Framer Motion (animations)
- Recharts (data visualization)

**Key Pages:**
- `page.tsx` - Home/landing
- `chat/page.tsx` - Main chat interface
- `auth/page.tsx` - Login flow
- `dashboard/page.tsx` - User dashboard with stats
- `markets/page.tsx` - Market data & portfolio view
- `marketplace/page.tsx` - ELSS/Insurance products
- `profile/page.tsx` - User settings & preferences
- `onboarding/page.tsx` - Xray questionnaire flow

**API Routes (Proxies to Backend):**
- `api/auth/[...nextauth]/route.ts` - NextAuth callbacks
- `api/chat/route.ts` - Chat endpoint
- `api/voice-briefing/route.ts` - Voice interaction
- `api/xray/route.ts` - Onboarding

### **Backend Orchestrator (FastAPI)**

**Entry Point:** `orchestrator.py`

**LLM Configuration:**
- **Primary:** OpenRouter StepFun (free tier, cost-effective)
- **Fallback:** Groq Llama 3.3 70B (low-latency fallback)

**Endpoints:**
```
POST   /api/chat          # Chat interface
POST   /api/voice-briefing # Voice interaction
GET    /api/onboarding    # Profiling questions
POST   /api/onboarding    # Save profile answers
WS     /ws/voice          # WebSocket for voice pipeline
GET    /api/user          # Fetch user profile
POST   /api/user          # Update profile
```

### **Multi-Agent System**

| Agent | Role | Responsibilities |
|-------|------|------------------|
| **Agent 0: Orchestrator** | Main brain | Route intents, manage state, synthesize responses |
| **Agent 2: Editorial** | Content | Retrieve ET Prime/Wealth articles via RAG or mock DB |
| **Agent 3: Market Intel** | Market data | Real-time quotes, portfolio analysis, trends |
| **Agent 4: Marketplace** | E-commerce | ELSS funds, insurance products, recommendations |
| **Agent 5: Profiling** | User data | Xray onboarding, persona mapping, risk scoring |
| **Agent 6: Behavioral** | Compliance | Paywall tracking, sentiment monitoring, compliance logs |

**Agent Communication:**
- Agents communicate via async tasks in LangGraph
- Shared state (ConciergeState) passed between agents
- Compliance wrapper applies to all outgoing responses

### **RAG Pipeline**

**Components:**

1. **Ingestion** (`packages/rag/ingestion/`)
   - `et_scraper.py` - Scrape ET website for articles
   - `ingest.py` - Parse & embed via sentence-transformers
   - `news_scheduler.py` - Periodic ingestion jobs

2. **Retrieval** (`packages/rag/retrieval/`)
   - `hybrid_search.py` - Query Qdrant (vector) + Elasticsearch (full-text)
   - User persona context for personalized retrieval

3. **Reranking** (`packages/rag/reranking/`)
   - `reranker.py` - LLM-based re-ranking of top results

**Fallback:** Mock articles in `seed_content.json` if RAG unavailable

### **Voice Pipeline**

**Architecture:**
```
Client Audio → Groq Whisper (STT) → Orchestrator → Edge TTS → Audio Response
```

**WebSocket Handler:** `voice_pipeline.py`
- Receive audio bytes from client
- Transcribe via Groq's Whisper model
- Process through orchestrator
- Synthesize response via Edge TTS
- Stream audio back to client

### **Compliance & Monitoring**

**Compliance Wrapper** (`compliance_wrapper.py`):
- Detect PII (email, phone, SSN, card numbers)
- Filter sensitive outputs
- Apply sentiment analysis

**Behavioral Monitor** (`behavioral_monitor.py`):
- Track paywall hits (upsell journey)
- Query analytics
- Audit logging
- User engagement metrics

---

## 🗄️ Data Models

### Core Pydantic Models (`state.py`)

```python
# Enums
class PersonaType:
    CONSERVATIVE_SAVER = "PERSONA_CONSERVATIVE_SAVER"
    ACTIVE_TRADER = "PERSONA_ACTIVE_TRADER"
    YOUNG_PROFESSIONAL = "PERSONA_YOUNG_PROFESSIONAL"
    CORPORATE_EXECUTIVE = "PERSONA_CORPORATE_EXECUTIVE"
    HOME_BUYER = "PERSONA_HOME_BUYER"

class SentimentType:
    FRUSTRATED, ANXIOUS, CURIOUS, CONFIDENT

class IntentType:
    INFORM, TRANSACT, LEARN, DISCOVER

class ModalityType:
    VOICE, WEB, MOBILE

# Core Models
class Message:
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: str
    agent_id: Optional[str]

class UserProfile:
    id: str
    persona: Optional[PersonaType]
    risk_score: int  # 1-10
    interests: List[str]
    goals: List[str]
    income_type: str  # salaried / self-employed / business
    age_group: str  # 20s, 30s, 40s, 50+
    has_emergency_fund: bool
    home_ownership: str  # renting / owning
    investment_horizon: str  # short-term / long-term
    is_active_trader: bool
    primary_goal: str  # saving / growing / protecting / buying
    has_tax_investments: bool
    has_insurance: bool
    onboarding_complete: bool
    has_et_prime_subscription: bool
    profile_completeness: float  # 0-1

class Recommendation:
    type: str  # article, tool, product, course
    title: str
    description: str
    deeplink: Optional[str]
    source_agent: str
    confidence: float

class ChatRequest:
    message: str
    session_id: str
    modality: ModalityType  # web, voice, mobile
    context: Optional[Dict[str, Any]]

class AgentResponse:
    agent_id: str
    response_text: str
    reasoning: Optional[str]
    recommendations: List[Recommendation]
    sentiment: Optional[SentimentType]
    should_upsell: bool
```

### PostgreSQL Schema

Key tables (initialized in `scripts/init_db.sql`):
- `users` - User accounts & auth
- `user_profiles` - Extended user metadata
- `chat_messages` - Conversation history
- `personas` - Persona definitions
- `audit_logs` - Compliance & security logging

### Vector DB (Qdrant)

Collections:
- `articles` - Article embeddings (768-dim, sentence-transformers)
- `queries` - User query patterns for personalization

### Search Index (Elasticsearch)

Index: `articles`
- Mapping: title, content, summary, author, published_date, tags, paywall

---

## 🚀 Getting Started

### Prerequisites

- Node.js 18+ (for Next.js)
- Python 3.11+ (for FastAPI backend)
- Docker & Docker Compose
- Git

### Local Development Setup

#### 1. Clone & Install Dependencies

```bash
cd et-ai-concierge

# Frontend
cd apps/web
npm install
cd ../..

# Backend
cd packages/agents
pip install -r requirements.txt
cd ../..

# RAG
cd packages/rag
pip install -r requirements.txt
cd ../..
```

#### 2. Start Infrastructure

```bash
docker-compose up -d
```

This starts:
- PostgreSQL (port 5432)
- Redis (port 6379)
- Qdrant (port 6333)
- Elasticsearch (port 9200)
- Neo4j (port 7687, 7474)

#### 3. Initialize Database

```bash
# Run migration
psql -U user -d et_concierge -h localhost < scripts/init_db.sql

# Seed personas
python scripts/seed_personas.py
```

#### 4. Environment Configuration

Create `.env` in project root:

```bash
# Auth
AUTH_SECRET=your_random_secret_here

# LLM APIs
OPENROUTER_API_KEY=your_openrouter_key
GROQ_API_KEY=your_groq_key

# External APIs
FINNHUB_API_KEY=your_finnhub_key
NEWSAPI_API_KEY=your_newsapi_key

# Observability
LANGSMITH_API_KEY=your_langsmith_key
SENTRY_DSN=your_sentry_dsn

# Database URLs (Docker defaults)
DATABASE_URL=postgresql://user:password@localhost:5432/et_concierge
REDIS_URL=redis://localhost:6379/0
QDRANT_URL=http://localhost:6333
ELASTICSEARCH_URL=http://localhost:9200
NEO4J_URI=bolt://localhost:7687
NEO4J_PASSWORD=local_password
```

#### 5. Run Frontend

```bash
cd apps/web
npm run dev
# Open http://localhost:3000
```

#### 6. Run Backend

```bash
cd packages/agents
uvicorn orchestrator:app --reload --port 8000
# Open http://localhost:8000/docs for Swagger UI
```

#### 7. Ingest Content (Optional)

```bash
python scripts/ingest_et_prime.py
```

---

## 📋 API Documentation

### Chat Endpoint

**POST** `/api/chat`

Request:
```json
{
  "message": "What are the best ELSS funds for a 25-year-old?",
  "session_id": "user-123-session-456",
  "modality": "web",
  "context": {
    "portfolio_value": 500000,
    "risk_tolerance": "moderate"
  }
}
```

Response:
```json
{
  "message_id": "msg-789",
  "response": "Based on your profile, I recommend...",
  "agent_id": "agent_4_marketplace",
  "recommendations": [
    {
      "type": "product",
      "title": "Axis Long Term Equity Growth Fund",
      "deeplink": "et://elss/axis-lteg",
      "confidence": 0.92
    }
  ],
  "sentiment": "curious",
  "should_upsell": false
}
```

### Onboarding Endpoint

**GET** `/api/onboarding?step=1`

Response:
```json
{
  "step": 1,
  "question": "What is your primary financial goal?",
  "options": ["Saving", "Growing wealth", "Protecting assets", "Buying home"],
  "type": "multiple_choice"
}
```

**POST** `/api/onboarding`

Request:
```json
{
  "user_id": "user-123",
  "answers": {
    "primary_goal": "Growing wealth",
    "age_group": "20s",
    "income_type": "salaried",
    "home_ownership": "renting",
    "investment_horizon": "long-term"
  }
}
```

### Voice Briefing Endpoint

**WS** `/ws/voice`

Binary WebSocket for audio streaming:
1. Client sends audio bytes
2. Server transcribes (Whisper)
3. Server processes through orchestrator
4. Server synthesizes response (Edge TTS)
5. Server streams audio bytes back

---

## 📊 Database Queries & Health Checks

### Test PostgreSQL Connection

```bash
psql -U user -d et_concierge -h localhost -c "SELECT version();"
```

### Check Qdrant

```bash
curl http://localhost:6333/health
```

### Check Elasticsearch

```bash
curl http://localhost:9200/_cluster/health
```

### Test Backend

```bash
curl http://localhost:8000/docs  # Swagger UI
curl http://localhost:8000/health  # Health check (if implemented)
```

---

## 🔐 Authentication & Security

### NextAuth.js Flow

1. **Login Page** → User enters credentials
2. **NextAuth Provider** → Validates against backend OAuth/JWT
3. **JWT Mint** → Frontend calls `mintBackendToken()` to get JWT for backend
4. **Backend Token** → Passed in `Authorization: Bearer <token>` header
5. **JWT Validation** → Backend validates token with `get_current_user(token)`

### Compliance & Security

- **PII Detection** → Compliance wrapper detects sensitive data
- **Sentiment Analysis** → Monitor user emotional state
- **Audit Logging** → All interactions logged to PostgreSQL
- **Rate Limiting** → Recommended at API gateway level
- **CORS** → Configured in FastAPI (`CORSMiddleware`)

---

## 📄 Configuration Reference

### Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `AUTH_SECRET` | NextAuth signing key | (required) |
| `OPENROUTER_API_KEY` | OpenRouter LLM API | (required) |
| `GROQ_API_KEY` | Groq LLM + Whisper | (required) |
| `DATABASE_URL` | PostgreSQL connection | `postgresql://user:password@localhost:5432/et_concierge` |
| `REDIS_URL` | Redis cache | `redis://localhost:6379/0` |
| `QDRANT_URL` | Vector DB | `http://localhost:6333` |
| `ELASTICSEARCH_URL` | Search index | `http://localhost:9200` |
| `NEO4J_URI` | Graph DB | `bolt://localhost:7687` |
| `FINNHUB_API_KEY` | Stock quotes | (optional) |
| `NEWSAPI_API_KEY` | News feeds | (optional) |
| `LANGSMITH_API_KEY` | LangChain observability | (optional) |
| `SENTRY_DSN` | Error tracking | (optional) |
| `EDGE_TTS_VOICE` | Text-to-speech voice | `en-IN-NeerjaNeural` |

### Config Validation

All settings loaded from environment variables via `packages/agents/config.py`:

```python
from config import settings
print(settings.OPENROUTER_API_KEY)  # Access config
```

---

## 🧪 Testing

### Unit Tests

Create `test_*.py` files in package directories:

```bash
# Run all tests
pytest packages/agents/test_*.py -v

# Run specific test
pytest packages/agents/test_orchestrator.py::test_chat_endpoint -v
```

### Integration Tests

Test end-to-end flows:

```bash
# Test chat with voice
python tests/test_voice_pipeline.py

# Test RAG retrieval
python tests/test_rag_retrieval.py
```

### Load Testing

```bash
# Using locust
locust -f tests/load_test.py --host=http://localhost:3000
```

---

## 📈 Deployment

### Production Checklist

- [ ] Environment variables configured for production
- [ ] Database migrations run on fresh DB
- [ ] Secrets stored in secure vault (not .env files)
- [ ] Rate limiting enabled at API gateway
- [ ] HTTPS enabled
- [ ] CORS configured for production domain
- [ ] Monitoring & alerting set up (Sentry, New Relic, etc.)
- [ ] Database backups scheduled
- [ ] Cache invalidation strategy defined

### Docker Build & Deploy

```bash
# Build backend image
cd packages/agents
docker build -t et-concierge-backend:latest .

# Build frontend (optional, can use Vercel)
cd apps/web
docker build -t et-concierge-web:latest .

# Push to registry
docker push et-concierge-backend:latest
docker push et-concierge-web:latest

# Deploy to Kubernetes / Docker Swarm / ECS
# (See deployment configs in separate repo/docs)
```

### Cloud Deployment Options

- **Frontend:** Vercel, Netlify, CloudFlare Pages
- **Backend:** AWS (ECS/Lambda), Google Cloud Run, Azure Container Instances
- **Database:** AWS RDS (PostgreSQL), Google Cloud SQL
- **Cache:** AWS ElastiCache, Azure Cache for Redis
- **Observability:** DataDog, New Relic, Sentry

---

## 📚 Dependencies

### Frontend (package.json)

```
React 19.2, Next.js 16.2, TypeScript 5, Tailwind CSS 4
Radix UI, NextAuth.js, Framer Motion, Recharts
React Markdown, LucideReact
```

### Backend (requirements.txt)

```
FastAPI, Uvicorn, LangGraph, LangChain, Groq
Sentence Transformers, pgvector, Qdrant Client
Elasticsearch, Neo4j, Redis, PostgreSQL (psycopg2)
YFinance, FinnHub, NewsAPI, DDGS
Edge TTS, Google Cloud TTS, Pydantic
```

### RAG (requirements.txt)

```
Qdrant Client, Elasticsearch, Neo4j
LLama Index, Sentence Transformers, LangChain
Python DotEnv
```

---

## 🐛 Troubleshooting

### Common Issues

**PostgreSQL connection refused:**
```bash
# Check container running
docker ps | grep postgres

# View logs
docker logs <container_id>

# Restart
docker-compose down && docker-compose up -d
```

**Qdrant not responding:**
```bash
# Check Qdrant health
curl http://localhost:6333/health

# Verify container
docker logs <qdrant_container_id>
```

**LLM API errors:**
- Verify API keys in `.env`
- Check OpenRouter/Groq account limits
- See FastAPI logs for detailed errors

**RAG ingestion failing:**
- Check PostgreSQL/Qdrant connectivity
- Verify sentence-transformers model downloaded
- Run: `python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"`

**Voice not working:**
- Verify Groq API key
- Check Edge TTS voice name (`settings.EDGE_TTS_VOICE`)
- Test audio format (WAV expected)

---

## 📝 Contributing Guidelines

1. **Branch naming:** `feature/description`, `bugfix/issue-name`, `docs/update-readme`
2. **Commits:** Clear, descriptive messages with ticket refs
3. **PRs:** Include description, testing notes, screenshots/demo videos
4. **Code style:**
   - Python: PEP 8, Black formatter
   - TypeScript/React: ESLint config
   - Git pre-commit hooks recommended

### Code Organization

- **Backend:** Organized by agent responsibility (e.g., `market_intelligence_agent.py`)
- **Frontend:** Component/page-based structure with shared `components/ui/`
- **Shared types:** `state.py` for core models
- **Config:** Centralized in `config.py`

---

## 📄 License & Compliance

- Ensure all scraped content respects website ToS
- Ensure compliance with financial regulatory requirements (SEBI guidelines for India)
- Implement proper KYC/AML checks for transactional features
- Monitor PII handling per GDPR/India Privacy Act

---

## 📞 Support & Contact

For questions or issues:
- Check the troubleshooting section above
- Review agent-specific documentation in agent files
- Create an issue in the repository
- Contact the development team

---

## 🎯 Future Roadmap

- Mobile app (React Native)
- Advanced technical analysis indicators
- Portfolio optimization algorithms
- GPT-4 Turbo integration for advanced reasoning
- Multi-language support
- AI-powered tax planning
- Investment community features (discussion forums)
- Integration with ET Prime paywall system

---

**Last Updated:** March 28, 2026  
**Version:** 1.0

