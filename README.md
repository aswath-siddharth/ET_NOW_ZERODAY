# ET AI Concierge

A sophisticated **multi-agent AI system** for financial intelligence, market analysis, and personalized investment guidance powered by LangGraph and FastAPI. Built for Economic Times (ET) users with seamless web, voice, and mobile experiences.

## 🎯 Project Overview

**ET AI Concierge** is an enterprise-grade AI platform that combines:
- **6-Agent LangGraph Orchestration**: Specialized agents for market intelligence, editorial content, user profiling, marketplace intermediation, behavioral monitoring, and compliance
- **Hybrid RAG System**: Combines vector search (Qdrant) + lexical search (Elasticsearch) + LLM-based reranking for intelligent context retrieval
- **Voice Intelligence**: End-to-end voice pipeline with STT (Groq Whisper), LLM processing, and TTS (Google Cloud / Edge TTS)
- **Behavioral Profiling**: Real-time sentiment analysis, intent detection, and paywall management
- **Compliance & Monitoring**: SEBI-compliant disclaimers, PII detection, sentiment filtering, and audit logging

### Key Capabilities
- **Conversational AI**: Web/voice chat interface with streaming responses and RAG-powered content
- **Voice Briefing**: AI-generated audio market updates based on user interests (90-sec dynamic briefs)
- **Market Intelligence**: Real-time stock quotes, portfolio analysis, news feeds (Finnhub, NewsAPI, ET RSS)
- **User Onboarding**: 9-question Xray profiling → 5 financial personas → product recommendations
- **Marketplace Transactions**: Loan underwriting, EMI calculators, insurance quotes, ELSS comparison
- **Behavioral Triggers**: Paywall hits, learning gaps → personalized upsell/cross-sell offers
- **Compliance Layer**: SEBI disclaimers, PII anonymization, audit trail, HITL escalation

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

1. **Web Input** → Frontend captures user intent via chat
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
- `onboarding/page.tsx` - LLM-driven Financial X-Ray (9 questions with button options)

**API Routes (Proxies to Backend):**
- `api/auth/[...nextauth]/route.ts` - NextAuth callbacks
- `api/chat/route.ts` - Chat endpoint (with LLM synthesis)
- `api/voice-briefing/route.ts` - Voice briefing endpoint

**UI Features:**
- Streaming chat responses with markdown rendering
- Voice recording & playback for audio input/output
- **Onboarding:** Displays clickable button options (no text input needed)
- Progress tracking (Question X of 9) with animated progress bar
- Conversation history with sender context (user vs assistant)

### **Backend Orchestrator (FastAPI)**

**Entry Point:** `orchestrator.py`

**LLM Configuration:**
- **Primary:** OpenRouter StepFun (`stepfun/step-3.5-flash:free`) - Cost-effective, reasoning-capable
- **Fallback:** Groq Llama 3.3 70B (`llama-3.3-70b-versatile`) - Ultra-low latency (50-500ms)
- **Final Fallback:** Static questions if both LLMs fail

**URL:** `https://openrouter.ai/api/v1/chat/completions`

**Endpoints:**
```
POST   /api/chat          # Chat interface
GET    /api/onboarding    # Profiling questions
POST   /api/onboarding    # Save profile answers
GET    /api/user          # Fetch user profile
POST   /api/user          # Update profile
```

### LLM-Driven Financial X-Ray (Onboarding)

The onboarding system (`profiling_agent.py` - `run_xray_step()`) uses LLMs to dynamically generate questions:

**Flow:**
```
User starts onboarding
  ↓
Backend initializes conversation with warm greeting
  ↓
Calls run_xray_step(conversation_history, question_number=0)
  ↓
OpenRouter generates Q1 (or Groq/static fallback if it fails)
  ↓
User answers → Stored in conversation history
  ↓
Calls run_xray_step(conversation_history, question_number=1)
  ↓
LLM ADAPTS Q2 based on Q1 answer (context-aware) ← KEY FEATURE
  ↓
... repeat 9 times with dynamic adaptation ...
  ↓
After Q9: LLM generates summary + JSON profile with persona
  ↓
Backend extracts: persona, risk_score, interests, income_type, age_group, etc.
  ↓
Profile saved to database, user redirected to dashboard
```

**Key Features:**
- **Conversation History** - Full history maintained per user for context
- **Dynamic Adaptation** - Each question adapts based on previous answers
- **LLM Fallback Chain** - OpenRouter → Groq → Static questions
- **JSON Profile Extraction** - LLM outputs structured profile at end
- **UI Options** - Each question has predefined button options for frontend

### Multi-Agent System (LangGraph)

The orchestrator uses 6 specialized agents working together in a LangGraph state machine:

| Agent | File | Responsibility | Triggers |
|-------|------|-----------------|----------|
| **Agent 0: Orchestrator** | `orchestrator.py` | Main coordinator, intent routing, response synthesis | Every user message |
| **Agent 1: Intent Router** | `intent_router.py` | Detects intent type (inform/transact/learn/discover) | Passive, runs in every flow |
| **Agent 2: Editorial** | `editorial_agent.py` | Content retrieval via RAG, article recommendations | Intent: LEARN |
| **Agent 3: Market Intel** | `market_intelligence_agent.py` | Real-time quotes, portfolio analysis, trends | Intent: INFORM, DISCOVER |
| **Agent 4: Marketplace** | `marketplace_agent.py` | ELSS funds, insurance, loans, product recs | Intent: TRANSACT |
| **Agent 5: Profiling** | `profiling_agent.py` | Xray onboarding, persona mapping, risk scoring | New users |
| **Agent 6: Behavioral Monitor** | `behavioral_monitor.py` | Paywall tracking, compliance, upsell triggers | Passive, periodic |

**LangGraph State Flow:**
```
Input Message
    ↓
[Intent Detection] → Determine intent type
    ↓
[Route Decision] → Pick best agent(s)
    ↓
[Agent(s) Execute] → Specialized processing (RAG, APIs, etc.)
    ↓
[Compliance Check] → PII, sentiment, disclaimers
    ↓
[Response Synthesis] → Combine outputs into coherent response
    ↓
[Logging] → Save to chat_history + audit_log
    ↓
Output to User
```

**Agent Inter-communication:**
- Share state via `ConciergeState` (LangGraph)
- Send messages via async tasks
- Comply wrapper applies to all outputs
- Behavioral monitor tracks patterns

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
    WEB, MOBILE

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
    modality: ModalityType  # web, mobile
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

## 📋 Complete API Endpoints Reference

### Authentication Endpoints

```
POST   /api/auth/signin                # Sign in with credentials
POST   /api/auth/signout               # Sign out (clear session)
POST   /api/auth/register              # Create new account
POST   /api/auth/callback/google       # Google OAuth callback
GET    /api/auth/session               # Get current session
```

### Chat & Conversation

```
POST   /api/chat                       # Send message, get streaming response
GET    /api/chat/history               # Fetch conversation history
GET    /api/chat/history/{msg_id}      # Get specific message details
DELETE /api/chat/history/{msg_id}      # Delete a message
DELETE /api/chat/history               # Clear all chat history
```

### Onboarding & Personalization (LLM-Driven X-Ray)

```
GET    /api/onboarding/start           # Start 9-question X-Ray (returns Q1)
POST   /api/onboarding/answer          # Submit answer, get next question (Q2-Q9)
GET    /api/profile                    # Get user profile after onboarding
PUT    /api/profile                    # Update profile
```

### User Profile

```
GET    /api/profile                    # Get user profile
PUT    /api/profile                    # Update profile
GET    /api/profile/interests          # Get interests
PUT    /api/profile/interests          # Update interests
GET    /api/profile/recommendations    # Personalized products
```

### Market Data

```
GET    /api/markets/quote?symbol=RELIANCE      # Real-time quote
GET    /api/markets/quotes?symbols=RELIANCE,INFY  # Batch quotes
GET    /api/markets/news?query=tech&limit=10   # News articles
GET    /api/markets/portfolio/analysis         # Portfolio analysis
GET    /api/markets/technical?symbol=RELIANCE  # Technical indicators
GET    /api/markets/trending?sector=tech       # Trending stocks
```

### Marketplace

```
GET    /api/marketplace/elss?amount=100000&horizon=long  # ELSS funds
GET    /api/marketplace/insurance?age=30&income_band=5-10L  # Insurance
POST   /api/marketplace/loan                   # Calculate loan EMI
POST   /api/marketplace/loan-compare           # Compare lenders
GET    /api/marketplace/featured               # Featured products
GET    /api/marketplace/{product_id}           # Product details
```

### Voice & Audio

```
GET    /api/voice-briefing?topics=tech,banking  # Generate audio brief
POST   /api/voice-briefing/feedback            # Submit feedback
GET    /api/voice-briefing/history             # Premium: Audio history
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

### Onboarding Endpoints (LLM-Driven Financial X-Ray)

The onboarding system uses **LLM-driven question generation** (OpenRouter primary, Groq fallback) with dynamic adaptation based on user answers. After 9 questions, the LLM extracts a financial profile and assigns a persona.

**GET** `/api/onboarding/start`

Initializes onboarding and returns the first question.

Response (Question 1):
```json
{
  "step": 0,
  "question": "Let's start simple — are you currently salaried, self-employed, or a business owner?",
  "options": ["salaried", "self-employed", "business owner"],
  "is_complete": false
}
```

**POST** `/api/onboarding/answer`

Submits an answer and returns the next question (or final profile on Q9).

Request:
```json
{
  "step": 0,
  "answer": "salaried"
}
```

Response (Question 2):
```json
{
  "step": 1,
  "question": "Which age bracket are you in — 20s, 30s, 40s, or 50+?",
  "options": ["20s", "30s", "40s", "50+"],
  "is_complete": false
}
```

Response (After Q9 - Final Profile):
```json
{
  "step": 9,
  "question": "Your Financial X-Ray is complete! We've mapped your financial persona.",
  "options": [],
  "is_complete": true,
  "persona": "PERSONA_YOUNG_PROFESSIONAL",
  "recommended_tools": [
    {"name": "ET Wealth SIP Guide", "description": "Recommended for Young Professional"},
    {"name": "Young Mind Program", "description": "Recommended for Young Professional"}
  ]
}
```

**9 X-Ray Questions (in order):**
1. Income type (salaried, self-employed, business owner)
2. Age group (20s, 30s, 40s, 50+)
3. Emergency fund (yes, no)
4. Home ownership (renting, owning)
5. Risk tolerance (1-10 scale)
6. Interest sectors (Tech, Pharma, Infrastructure, Banking, Auto, Real Estate, FMCG)
7. Investment horizon (1-3 years, 3-5 years, 5-10 years, 10+ years)
8. Trading style (active trader, SIP investor, both)
9. Primary goal (saving, growing, protecting, buying)

**Personas Assigned:**
- `PERSONA_CONSERVATIVE_SAVER` - Low risk, capital preservation focus
- `PERSONA_ACTIVE_TRADER` - High risk, active market participation
- `PERSONA_YOUNG_PROFESSIONAL` - Early career, moderate-high risk, wealth building
- `PERSONA_CORPORATE_EXECUTIVE` - Established, asset protection focus
- `PERSONA_HOME_BUYER` - Primary goal is real estate acquisition/planning



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

### Check Backend Services

```bash
# Swagger UI
curl http://localhost:8000/docs

# OpenAPI spec
curl http://localhost:8000/openapi.json

# Test chat (with mock token)
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer demo-token" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "session_id": "test-session"}'
```

---

## 🎙️ Voice Pipeline

The end-to-end voice system enables conversational AI with spoken input and output:

### Voice Briefing Architecture

**Flow:**
1. **Topic Extraction** - Get user interests from chat history or profile
2. **Data Retrieval** - RAG hybrid search for market trends + news
3. **Script Generation** - LLM creates ~90-second conversational script
4. **Speech Synthesis** - TTS converts text → audio (MP3)
5. **Streaming** - Frontend plays audio via HTML5 player

**Implementation:** `packages/voice/voice_pipeline.py` and `voice_briefing.py`

### Voice Endpoints

**GET** `/api/voice-briefing?topics=tech,banking`

- Generates personalized audio brief (90 seconds)
- Topics default to user interests if not specified
- Returns: audio/mpeg stream

**Modality:** Web, voice, or mobile

### TTS Configuration

**Primary:** Google Cloud Text-to-Speech
- Voice: `en-IN-Standard-A` (Indian English)
- Format: MP3, 24kHz

**Fallback:** Microsoft Edge TTS
- Voice: `en-IN-NeerjaNeural`
- Free tier, no authentication required

### Example Flow

```
User clicks "Voice Briefing" button
  ↓
Frontend fetches GET /api/voice-briefing
  ↓
Backend:
  1. Extract topics: ["tech", "banking"]
  2. RAG search: Get top 5 articles
  3. LLM generates script: "Today in tech markets..."
  4. TTS synthesizes: "Today in tech markets..." → audio bytes
  5. Streams MP3 back to frontend
  ↓
Frontend: HTML5 player plays audio
```

---

## 🔒 Security & Compliance

### Authentication

- **NextAuth.js** - Session management (browser cookies)
- **JWT Backend Token** - Signed HS256, passed in Authorization header
- **Database** - User credentials stored with bcrypt hashing

### Compliance

- **SEBI Disclaimers** - Applied to all investment advice
- **PII Detection** - Masks email, phone, SSN, card numbers
- **Audit Logging** - All interactions logged to PostgreSQL
- **Behavioral Monitoring** - Tracks usage for paywall & recommendations
- **Rate Limiting** - Recommended at API gateway / proxy level

### Data Privacy

- User data stored in PostgreSQL (encrypted at rest in production)
- Chat history retained for 180 days (configurable)
- No sharing with third parties except for LLM inference
- GDPR/India Privacy Act compliance required

---

## 📄 Configuration Reference

### Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `AUTH_SECRET` | NextAuth signing key | **(required)** |
| `OPENROUTER_API_KEY` | OpenRouter LLM API (PRIMARY) | **(required)** |
| `GROQ_API_KEY` | Groq LLM + Whisper (FALLBACK) | **(required)** |
| `DATABASE_URL` | PostgreSQL connection | `postgresql://user:password@localhost:5432/et_concierge` |
| `REDIS_URL` | Redis cache | `redis://localhost:6379/0` |
| `QDRANT_URL` | Vector DB | `http://localhost:6333` |
| `ELASTICSEARCH_URL` | Search index | `http://localhost:9200` |
| `NEO4J_URI` | Graph DB | `bolt://localhost:7687` |
| `FINNHUB_API_KEY` | Stock quotes | (optional) |
| `NEWSAPI_API_KEY` | News feeds | (optional) |
| `LANGSMITH_API_KEY` | LangChain observability | (optional) |
| `SENTRY_DSN` | Error tracking | (optional) |


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
# Test chat with backend
python tests/test_chat.py

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

### Frontend (`apps/web/package.json`)

```
Core: react@19.2, next@16.2, typescript@5, tailwindcss@4
UI: @radix-ui/*, framer-motion, recharts, react-markdown, lucide-react
Auth: next-auth@5
```

### Backend (`packages/agents/requirements.txt`)

```
Framework: fastapi, uvicorn, langgraph, langchain
LLM: groq, openrouter
Search: sentence-transformers, qdrant-client, elasticsearch, pgvector
DB: psycopg2-binary, redis, neo4j
APIs: yfinance, finnhub-python, newsapi, duckduckgo-search
Utils: pydantic, pandas, python-dotenv, langsmith, sentry-sdk
```

### RAG (`packages/rag/requirements.txt`)

```
Search: qdrant-client, elasticsearch, sentence-transformers
AI: langchain, llama-index (optional)
Web: beautifulsoup4, requests
Tasks: apscheduler, python-dotenv
```

---

## 🐛 Troubleshooting

### Common Issues & Diagnostics

**PostgreSQL Connection Issues**
```bash
# Check if running
docker ps | grep postgres

# View logs for errors
docker logs <postgres_container_id>

# Test connection
psql -U user -d et_concierge -h localhost -c "SELECT 1"

# Restart if needed
docker-compose restart postgres
```

**Qdrant Vector DB Not Responding**
```bash
# Health check
curl http://localhost:6333/health

# View collections
curl http://localhost:6333/collections

# Check container logs
docker logs <qdrant_container_id>

# Restart
docker-compose restart qdrant
```

**Elasticsearch Search Index Down**
```bash
# Cluster health
curl http://localhost:9200/_cluster/health

# List indices
curl http://localhost:9200/_cat/indices

# Check logs
docker logs <elasticsearch_container_id>

# Restart
docker-compose restart elasticsearch
```

**LLM API Errors (OpenRouter/Groq)**
- Verify keys: `echo $OPENROUTER_API_KEY` and `echo $GROQ_API_KEY`
- Check account limits and billing in OpenRouter/Groq console
- Test directly: `python -c "from groq import Groq; Groq().models.list()"`
- View backend logs: `docker logs et-concierge-backend -f`

**RAG Ingestion Failures**
```bash
# Verify all services running
docker-compose ps

# Check embeddings model
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Re-ingest articles
python packages/rag/ingestion/ingest.py --clear --verbose

# View ingestion logs
tail -f /tmp/rag_ingestion.log
```

**Chat Returns No Response**
- Check user profile exists: `psql -c "SELECT * FROM users WHERE email = 'your@email.com'"`
- Verify intent detection in FastAPI logs
- Test RAG separately: `python packages/rag/retrieval/hybrid_search.py --query "test"`
- Check LLM API keys and quotas

**Voice Briefing Returns 503**
- Verify TTS service: `python -c "from edge_tts import Text; print('OK')"`
- Check GCP credentials if using Google Cloud: `cat $GCP_CREDENTIALS_JSON | jq .`
- Ensure user profile has interests: `psql -c "SELECT interests FROM user_profiles LIMIT 1"`
- Verify LLM for script generation available

**Frontend Cannot Connect to Backend**
- Backend running: `curl http://localhost:8000/docs`
- Check BACKEND_URL env var in frontend
- CORS issue: Open DevTools Network tab, check response headers
- JWT token invalid: Verify `AUTH_SECRET` is same on frontend & backend
- Test endpoint directly: `curl -X POST http://localhost:8000/api/chat -H "Authorization: Bearer token"`

**Authentication Failing**
- Verify user exists: `psql -c "SELECT email FROM users LIMIT 5"`
- Check AUTH_SECRET set: `echo $AUTH_SECRET`
- JWT decode test: `python -c "import jwt; jwt.decode('token', 'secret', algorithms=['HS256'])"`
- Clear browser cookies and try again

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

