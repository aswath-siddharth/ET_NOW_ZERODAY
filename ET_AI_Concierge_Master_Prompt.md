# ET AI Concierge — Master Engineering Prompt (Zero-Cost Hackathon Edition)
### Complete Build Specification with Tech Stack

---

## 0. Project Identity

**Product name:** ET AI Concierge — "Your Financial Life Navigator"
**Platform target:** Web (Next.js), Mobile (React Native / Expo), Voice (Daily.co + Whisper + Edge TTS)
**Architecture style:** Multi-Agent System (MAS) with Orchestrator-Worker pattern
**Primary language:** TypeScript (frontend + API layer), Python (agent backend)
**Deadline context:** ET GenAI Hackathon 2026 — Phase 2 prototype by March 29, 2026
**Repo naming convention:** `TeamName_TeamLeader_Jazzee2025`

---

## 1. Problem Statement to Encode in Every Agent

The Economic Times ecosystem spans ET Prime (editorial analysis), ET Markets (trading tools), ETMasterclass (learning), and a financial services Marketplace. Despite the depth, the average user discovers less than 10% of available value — the "Discovery Paradox." Every agent you build must be wired with one directive: **bridge the gap between what the user knows exists and what they actually need.**

---

## 2. Full Tech Stack (Zero-Cost Canonical Reference)

### 2.1 Backend — Agent Runtime

| Concern | Tool | Why (Zero Cost Justification) |
|---|---|---|
| Agent orchestration | **LangGraph (Python)** | Free, open-source stateful multi-agent workflows; native checkpointing. |
| LLM (Brain) | **Groq API (Llama 3.3 70B)** | Generous free tier; ultra-fast inference (<1s response) perfect for agent chaining. |
| Agent memory (persistent) | **Mem0 (Open Source)** | `pip install mem0ai` uses local SQLite/ChromaDB. Same API as cloud, completely free. |
| Short-term session state | **Redis (Local)** | Run locally via Docker. 0ms latency, zero cost. |
| Durable user profiles | **PostgreSQL (Local)** | Run locally via Docker. Replaces expensive managed Supabase for the hackathon. |
| Task queue | **Celery + Redis** | Async background jobs; runs fully locally. |
| API gateway | **FastAPI** | Free, async-native, auto-generates OpenAPI schema. |

### 2.2 Retrieval — RAG Pipeline (Fully Localized)

| Concern | Tool | Why (Zero Cost Justification) |
|---|---|---|
| Vector store | **Qdrant (Local Docker)** | Open-source; runs locally. Ensures DPDP Act compliance automatically. |
| Lexical search | **BM25 (Elasticsearch)** | Exact entity matching. Run locally via Docker. |
| Hybrid fusion | **Reciprocal Rank Fusion (RRF)** | Mathematical algorithm (no API cost) to merge vector + lexical results. |
| Reranker | **BAAI/bge-reranker-base** | HuggingFace CrossEncoder. Runs locally. Matches Cohere's performance for free. |
| Knowledge graph | **Neo4j Community Edition** | GraphRAG. Run locally via Docker instead of Aura cloud. |
| Embedding model | **BAAI/bge-large-en-v1.5** | HuggingFace local model. Top of the open-source leaderboard; 0 API costs. |
| Document ingestion | **LlamaIndex** | Free Python ETL pipeline for parsing ET articles into chunks. |

### 2.3 Voice Stack

| Concern | Tool | Why (Zero Cost Justification) |
|---|---|---|
| STT (Speech-to-Text) | **Groq Whisper API** | Free tier available. Highly accurate for Indian accents and English-Hindi mix. |
| TTS (Text-to-Speech) | **Edge TTS (Python)** | Free wrapper around Azure's read-aloud. Excellent Indian voices (`en-IN-NeerjaNeural`). |
| Real-time audio transport| **Daily.co** | Free tier includes 10,000 minutes/month. Perfect for hackathon dev and demos. |
| Voice pipeline orchestration | **FastAPI WebSockets** | Connect STT -> LangGraph -> TTS streaming locally to bypass expensive LiveKit Cloud. |

### 2.4 Frontend

| Concern | Tool | Why |
|---|---|---|
| Web app | **Next.js 14 (App Router)** | SSR for SEO; streaming UI with React Server Components; API routes co-located |
| Mobile app | **React Native + Expo** | Shared component library with web; Expo Router for deep links |
| UI component system | **shadcn/ui + Tailwind CSS** | Accessible, unstyled primitives; fast hackathon iteration |
| Real-time UI updates | **Server-Sent Events (SSE)** | Stream agent token output to chat UI without WebSocket complexity |
| Voice UI | **Daily.co React hooks** | `useDaily()` for mic/speaker controls; handles browser permissions cleanly |
| State management | **Zustand** | Lightweight; no boilerplate; works identically on web and RN |
| Charts / market data viz | **Recharts** | React-native-compatible; sufficient for portfolio and market dashboards |

### 2.5 Data Sources & External APIs

| Data | Source | Notes |
|---|---|---|
| Real-time market data | **Finnhub API** | Free tier provides sufficient US/Global stock quotes for testing logic. |
| ET Prime content | **ET internal RAG corpus** | Ingest via LlamaIndex; refresh every 15 min |
| Mutual fund NAVs | **AMFI API** (free, official) | Real NAV data; no third-party dependency |
| RBI policy / rates | **RBI public RSS + scraper** | Monetary policy, repo rate, regulatory circulars |
| Home loan rates | **Partner bank simulators** | SBI, HDFC, Kotak — mock APIs for hackathon; schema matches real APIs |
| Weather (cross-sell triggers) | **OpenWeatherMap API** | Free tier is more than enough for location-based context |
| User location | **Browser Geolocation API** | Smart city + regional offer personalization |

### 2.6 Observability & Compliance

| Concern | Tool | Why |
|---|---|---|
| Agent tracing | **LangSmith** | Native LangGraph integration; free developer tier available. |
| Error tracking | **Sentry** | Frontend + backend; free developer tier. |
| Compliance audit log | **Custom Postgres table** | Every AI recommendation logged: agent ID, timestamp, reasoning, user ID |
| HITL escalation | **Zendesk webhook** | Trigger human handoff on high-stakes actions |
| Secrets management | **Doppler** | No `.env` files in repo; inject at runtime (Free tier) |

### 2.7 Infrastructure

| Concern | Tool |
|---|---|
| Local dev environment | `docker-compose up -d` — entire backend stack runs locally (Postgres, Redis, Qdrant, Elastic, Neo4j) |

---

## 3. System Architecture — Five Agents

Build exactly these five agents under one LangGraph orchestrator. Each is a LangGraph `StateGraph` node.

---

### Agent 0 — The Orchestrator (Concierge Agent)

**Role:** Brain of the system. Receives every user message, manages global conversation state, routes to worker agents, synthesizes responses.

**Implementation:**
```python
# tools available to orchestrator
tools = [
    route_to_profiling_agent,
    route_to_editorial_agent,
    route_to_market_intelligence_agent,
    route_to_marketplace_agent,
    route_to_behavioral_monitor,
    get_user_profile,          # reads from local Mem0 + Postgres
    update_user_profile,       # writes back to local Mem0
    detect_sentiment,          # frustrated / confident / curious / anxious
    detect_intent,             # inform / transact / learn / discover
]
```

**System prompt to encode:**

```
You are the ET AI Concierge — a Financial Life Navigator for The Economic Times ecosystem.
Your job is not to answer questions. Your job is to understand the user's complete financial life
and proactively guide them toward the ET tools, stories, courses, and financial products that
will genuinely help them.

Every message you receive, do three things before responding:
1. Check the user's stored profile (goals, risk tolerance, interests, persona).
2. Detect sentiment: frustrated / anxious / curious / confident.
3. Detect intent: inform / transact / learn / discover.

Then route to the right worker agent. Never answer from your own knowledge alone.
Always ground your response in real ET content or real market data.

When you synthesize the final response:
- Be conversational, not corporate.
- Never give generic advice. Always cite a specific ET tool, story, or product.
- If the user seems anxious, lower jargon density and increase reassurance.
- If the user is an active trader, be precise and data-dense.
```

**State schema:**

```typescript
interface ConciergeState {
  userId: string;
  sessionId: string;
  conversationHistory: Message[];
  userProfile: UserProfile;       // loaded from Mem0 on session start
  activeAgents: string[];         // which workers are currently running
  pendingRecommendations: Recommendation[];
  modalityContext: 'voice' | 'web' | 'mobile';
  complianceFlags: ComplianceFlag[];
}
```

---

### Agent 1 — Profiling Agent (ET Welcome Concierge)

**Role:** Onboards new users in under 3 minutes. Converts a first-time visitor into a high-fidelity financial persona. Writes the result to Mem0 and Postgres.

**Trigger:** First session OR profile completeness score < 60%.

**Conversation flow to implement:**

```
Step 1 — Warm open (30 seconds)
  "Welcome to ET. I'm your personal Financial Navigator.
   Before I connect you to the right parts of our ecosystem,
   I'd love to understand your financial world. May I ask you
   a few quick questions? Takes about 2 minutes."

Step 2 — Nine core profiling questions (implement as a state machine)
  Q1 (income bracket): "Are you currently salaried, self-employed, or a business owner?"
  Q2 (age group): "Which age bracket are you in — 20s, 30s, 40s, or 50+?"
  Q3 (emergency fund): "Do you have 3–6 months of expenses saved as an emergency fund?"
  Q4 (home ownership): "Are you currently renting, or do you own your home?"
  Q5 (risk tolerance — scaling): "On a scale of 1 to 10, how comfortable are you
      with short-term portfolio losses in exchange for long-term growth?"
  Q6 (primary interest — swing): "Which sectors do you follow most closely?
      For example — Tech, Pharma, Infrastructure, or Banking?"
  Q7 (investment horizon): "Are you primarily thinking about the next 1–3 years,
      or are you building wealth for 10+ years?"
  Q8 (active trader check): "Do you actively trade stocks, or are you more
      of a long-term SIP investor?"
  Q9 (current pain): "What's the one financial goal you're most focused on
      right now — saving, growing, protecting, or buying something big?"

Step 3 — Map to persona (one of five)
  PERSONA_CONSERVATIVE_SAVER    → ET Wealth, NPS, FD guides
  PERSONA_ACTIVE_TRADER         → Alpha Trades, Stock Reports Plus, Technical Charts
  PERSONA_YOUNG_PROFESSIONAL    → Young Mind program, SIP guides, ETMasterclass
  PERSONA_CORPORATE_EXECUTIVE   → ET Prime Corporate Governance, Strategic Leadership class
  PERSONA_HOME_BUYER            → Loan Marketplace, EMI calculators, RBI rate news

Step 4 — Deliver personalized onboarding path
  Present the top 3 ET tools/content items most relevant to their persona.
  Explain briefly why each one matters for their specific situation.
  Save full profile to Mem0 with tags for the Behavioral Monitor.
```

**Output written to Mem0 (Local OSS Version):**

```python
mem0_client.add(
    messages=[{"role": "system", "content": f"User profile: {json.dumps(profile)}"}],
    user_id=user_id,
    metadata={
        "persona": persona,
        "risk_score": risk_score,          # 1–10
        "interests": sectors_of_interest,
        "goals": primary_goal,
        "onboarding_complete": True,
        "profile_version": 1
    }
)
```

---

### Agent 2 — Editorial Agent

**Role:** Surfaces the right ET Prime / ET Wealth content for any user query or behavioral signal. Uses the fully local RAG pipeline.

**Tools:**

```python
tools = [
    hybrid_rag_search,          # vector (Qdrant) + BM25 (Elastic) over ET Prime corpus
    graph_rag_entity_search,    # Neo4j: find related entities/articles
    local_cross_encoder_rerank, # rerank top-20 results to top-3 using bge-reranker
    get_user_interests,         # pull from Mem0 to personalize search
    check_paywall_status,       # determine if user has ET Prime subscription
    generate_article_summary,   # 3-sentence summary of retrieved article
]
```

**RAG pipeline implementation (Zero Cost):**

```python
async def editorial_rag_pipeline(query: str, user_profile: UserProfile) -> list[Article]:
    # Step 1: Hybrid retrieval
    query_vector = local_embedding_model.encode(query) # Using BAAI/bge-large-en-v1.5
    
    vector_results = await qdrant_client.search(
        collection_name="et_prime_articles",
        query_vector=query_vector,
        limit=10,
        query_filter=Filter(must=[
            FieldCondition(key="sector", match=MatchAny(any=user_profile.interests))
        ])
    )
    lexical_results = await elasticsearch_client.search(
        index="et_prime_articles",
        body={"query": {"multi_match": {"query": query, "fields": ["title^2", "body", "tags"]}}}
    )

    # Step 2: Reciprocal Rank Fusion
    fused = reciprocal_rank_fusion([vector_results, lexical_results], k=60)

    # Step 3: Graph expansion — find related entities
    entities = extract_entities(query)   # NER on query
    graph_related = await neo4j_client.run(
        "MATCH (e:Entity {name: $entity})-[:RELATED_TO*1..2]-(a:Article) RETURN a LIMIT 5",
        entity=entities[0] if entities else ""
    )
    fused.extend(graph_related)

    # Step 4: Rerank locally
    reranked = await local_cross_encoder.predict(
        query=query,
        documents=[r.text for r in fused],
        model="BAAI/bge-reranker-base",
        top_n=3
    )

    return reranked
```

---

### Agent 3 — Market Intelligence Agent

**Role:** Real-time market data, technical signals, portfolio analysis, and "Big Bull" portfolio tracking via ET Markets.

**Tools:**

```python
tools = [
    finnhub_get_quote,              # real-time stock/index prices (free tier)
    finnhub_get_news,               # market news feed
    finnhub_get_recommendation,     # analyst buy/sell recommendations
    amfi_get_nav,                   # mutual fund NAV (official AMFI API)
    rbi_get_repo_rate,              # current repo rate from RBI feed
    calculate_portfolio_drift,      # compare current vs target allocation
    get_alpha_trades_signals,       # ET Markets Alpha Trades (mock for hackathon)
    run_technical_screener,         # RSI, Golden Cross, Candlestick patterns
    get_big_bull_portfolio,         # Rakesh Jhunjhunwala / other tracked portfolios
]
```

---

### Agent 4 — Marketplace Agent

**Role:** Financial product intermediation. Acts as a fiduciary, not a salesperson. Matches users to loans, cards, insurance, and investment products from partner institutions.

**Tools:**

```python
tools = [
    calculate_emi,                      # home/car/personal loan EMI
    check_loan_eligibility,             # credit score + employer → approval probability
    compare_loan_rates,                 # SBI vs HDFC vs Kotak current rates
    get_credit_card_rewards_analysis,   # Times Black ICICI vs SBI Cashback vs RuPay
    compare_insurance_plans,            # Niva Bupa health plans by age/coverage
    calculate_nps_returns,              # NPS tier I/II projected returns
    get_fd_rates,                       # highest FD rates across partner banks
    check_rbi_rate_cycle,               # current monetary policy stance
    extract_document_data,              # parse uploaded salary slips / bank statements
    pre_fill_application_form,          # reduce form friction; uses extracted data
    escalate_to_human,                  # HITL for high-stakes decisions
]
```

---

### Agent 5 — Behavioral Monitor Agent

**Role:** Passive, always-on agent. Tracks user behavior signals across the session and fires proactive cross-sell recommendations to the Orchestrator.

**Behavioral triggers to implement:**

```python
BEHAVIORAL_TRIGGERS = [
    {
        "name": "PAYWALL_HIT_3X",
        "condition": lambda s: s.paywall_hits >= 3,
        "action": "offer_et_prime_discounted",
        "message": "You've hit the ET Prime limit 3 times today. Get 1+1 year for ₹999.",
        "deeplink": "https://buy.indiatimes.com/ET/plans"
    },
    {
        "name": "MASTERCLASS_NO_TOOL",
        "condition": lambda s: s.time_on_page["technical-analysis-masterclass"] > 120
                               and not s.has_used["candlestick-screener"],
        "action": "bridge_learning_to_tool",
        "message": "You've been exploring the Technical Analysis class. Ready to try it live? "
                   "The Candlestick Screener on ET Markets lets you apply exactly this.",
        "deeplink": "https://economictimes.indiatimes.com/markets/stocks/recos"
    },
    {
        "name": "CAREER_TRANSITION",
        "condition": lambda s: "educational loan" in s.recent_queries
                               and "investment" in s.recent_queries,
        "action": "suggest_psychology_of_money",
        "message": "Looks like you're navigating a career transition. The Psychology of Money "
                   "masterclass has helped thousands of young professionals build wealth early.",
    },
    {
        "name": "ANNIVERSARY_UPSELL",
        "condition": lambda s: s.days_since_product_signup in [365, 730],
        "action": "suggest_insurance_review",
        "message": "It's been a year since you joined. A quick insurance review could "
                   "save you ₹8,000–₹12,000 annually on premiums.",
    },
    {
        "name": "TAX_SEARCH_INTENT",
        "condition": lambda s: any(q in s.recent_queries for q in
                                   ["save tax", "80C", "tax deduction", "ELSS"]),
        "action": "route_to_et_wealth_tax",
        "message": "I found an ET Wealth guide on maximizing your 80C limit "
                   "and the NPS calculator to see your exact tax saving.",
    },
]
```

---

## 4. Multi-Modal Handoff — Voice ↔ Web ↔ Mobile

This is the single most impressive feature to demo. Implement it completely.

**Architecture:**

```
User starts on voice (driving)
  → Groq Whisper STT transcribes
  → LangGraph processes via Llama 3.3, updates session in local Redis
  → Edge TTS speaks response
  → Session ID stored in local Mem0 with full context

User opens web app 30 minutes later
  → Frontend calls GET /api/session/resume?userId=X
  → Local Redis returns active session context
  → Web UI renders conversation history
  → "Welcome back. You were asking about home loans earlier. 
     Here's the SBI vs HDFC comparison I mentioned."
  → Full context, zero repetition
```

**Session resume API endpoint:**

```python
@app.get("/api/session/resume")
async def resume_session(user_id: str, modality: str):
    # Pull from Local Redis (recent session) or Local Mem0 (historical)
    recent = await redis_client.get(f"session:{user_id}:latest")
    if recent:
        session = SessionState(**json.loads(recent))
        # Generate a transition message using Groq Llama 3.3
        transition_msg = await orchestrator.generate_transition_message(
            session=session,
            new_modality=modality,
            time_gap_minutes=session.minutes_since_last_interaction
        )
        return {"session": session, "transition_message": transition_msg}
    # Fall back to full profile from local Mem0
    profile = await mem0_client.get_all(user_id=user_id)
    return {"profile": profile, "is_new_session": True}
```

---

## 5. Compliance Implementation

Every response from the system must pass through this compliance wrapper before being delivered to the user.

```python
class ComplianceWrapper:
    def wrap(self, agent_response: AgentResponse, user: UserProfile) -> AgentResponse:

        # 1. SEBI: Disclose AI usage on investment recommendations
        if agent_response.contains_investment_advice:
            agent_response.append_disclaimer(
                "This recommendation is generated by AI and is for informational purposes only. "
                "It does not constitute registered investment advice under SEBI IA Regulations 2024. "
                "Please consult a SEBI-registered advisor before investing."
            )

        # 2. RBI FREE-AI: Log every recommendation for audit trail
        audit_logger.log({
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user.id,
            "agent_id": agent_response.agent_id,
            "recommendation_type": agent_response.type,
            "reasoning": agent_response.reasoning_trace,
            "model_used": "llama-3.3-70b-versatile",
            "data_sources": agent_response.sources,
        })

        # 3. Check HITL triggers before returning
        if self.requires_human_oversight(agent_response):
            return self.escalate_to_human(agent_response, user)

        return agent_response
```

**Audit log schema (Local Postgres):**

```sql
CREATE TABLE ai_audit_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    user_id         UUID NOT NULL,
    session_id      UUID NOT NULL,
    agent_id        VARCHAR(50) NOT NULL,
    intent          VARCHAR(100),
    recommendation  JSONB,
    sources         JSONB,           -- ET articles, APIs used
    reasoning_trace TEXT,            -- LangSmith trace ID
    model_version   VARCHAR(50),
    confidence      FLOAT,
    hitl_triggered  BOOLEAN DEFAULT FALSE,
    disclaimer_shown BOOLEAN DEFAULT FALSE
);
```

---

## 6. Frontend Component Map

Build these screens. Nothing more for the hackathon.

```
/                       → Landing + voice onboarding entry point
/onboarding             → ET Welcome Concierge (Profiling Agent UI)
/dashboard              → Personalized home: top 3 tools, morning briefing, portfolio snapshot
/chat                   → Main Financial Life Navigator chat interface (streaming SSE)
/markets                → Market Intelligence Agent UI: indices, portfolio, technical signals
/marketplace            → Marketplace Agent UI: loan/card/insurance comparison
/profile                → User persona, risk score, goals (read/edit)
```

---

## 7. Demo Script for Judges

Build your hackathon demo around this exact 4-minute narrative:

```
[0:00 – 0:45] — Voice onboarding
  Show voice interface. User speaks: "I'm a 28-year-old software engineer.
  I want to start investing but I don't know where."
  Profiling Agent asks 3 follow-up questions via Edge TTS voice.
  Result: PERSONA_YOUNG_PROFESSIONAL mapped. Onboarding path displayed.

[0:45 – 1:30] — Financial Life Navigator in action
  User types: "I've been hearing a lot about gold. Is it a good time to buy?"
  Show context-sensitive response: ET Prime article on GIFT City gold volumes
  PLUS real-time MCX Gold price from Finnhub PLUS SGB recommendation from Marketplace Agent.
  Three agents fired in parallel. One coherent answer.

[1:30 – 2:15] — Cross-sell engine trigger
  Click the paywall 3 times on ET Prime stories.
  Watch the Behavioral Monitor fire: discounted 1+1 ET Prime offer appears.
  Show the audit log in LangSmith — every agent step visible.

[2:15 – 3:00] — Multi-modal handoff
  "I was talking to ET Concierge on voice earlier about a home loan."
  Switch to web. Show session resume with transition message.
  Full loan comparison table: SBI vs HDFC vs Kotak, ranked by approval probability.

[3:00 – 3:45] — HITL escalation
  User says: "I want to apply for the SBI home loan right now."
  Show HITL trigger: "Connecting you to a specialist."
  Show Zendesk ticket created with full conversation context pre-filled.

[3:45 – 4:00] — Impact metrics slide
  25% projected cross-sell revenue increase
  68% reduction in loan application abandonment
  300% increase in ecosystem feature discovery
  From 10% discovery rate to full ecosystem utilization
```

---

## 8. Repo Structure

```
et-ai-concierge/
├── apps/
│   ├── web/                    # Next.js 14 app
│   │   ├── app/
│   │   │   ├── (dashboard)/
│   │   │   ├── (onboarding)/
│   │   │   ├── api/
│   │   │   │   ├── chat/route.ts
│   │   │   │   ├── session/route.ts
│   │   │   │   └── voice/route.ts
│   │   └── components/
│   └── mobile/                 # React Native + Expo
│       ├── app/
│       └── components/
├── packages/
│   ├── agents/                 # Python — all LangGraph agents
│   │   ├── orchestrator.py
│   │   ├── profiling_agent.py
│   │   ├── editorial_agent.py
│   │   ├── market_intelligence_agent.py
│   │   ├── marketplace_agent.py
│   │   ├── behavioral_monitor.py
│   │   └── compliance_wrapper.py
│   ├── rag/                    # RAG pipeline
│   │   ├── ingestion/
│   │   ├── retrieval/
│   │   └── reranking/
│   ├── voice/                  # Daily.co + Whisper + Edge TTS
│   └── shared/                 # TypeScript types shared across web/mobile
├── infra/
│   ├── docker-compose.yml      # local dev: Postgres, Redis, Qdrant, Elastic, Neo4j
│   └── aws/                    # production CDK stack (optional for hackathon)
├── scripts/
│   ├── ingest_et_prime.py      # seed RAG corpus
│   └── seed_personas.py        # seed test user profiles
└── docs/
    ├── architecture.md
    └── compliance.md
```

---

## 9. Environment Variables (via Doppler)

```bash
# LLM & STT (Free Tier APIs)
GROQ_API_KEY=your_free_groq_key

# Voice Transport (Free Tier)
DAILY_API_KEY=your_free_daily_key

# Memory & State (Local - No API Keys Needed)
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=postgresql://user:password@localhost:5432/et_concierge

# Vector & Search (Local Docker)
QDRANT_URL=http://localhost:6333
ELASTICSEARCH_URL=http://localhost:9200

# Knowledge Graph (Local Docker)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=local_password

# External Data (Free Tiers)
FINNHUB_API_KEY=your_free_finnhub_key
OPENWEATHERMAP_API_KEY=your_free_weather_key

# Observability
LANGSMITH_API_KEY=your_free_langsmith_key
SENTRY_DSN=your_free_sentry_dsn

# Compliance
ZENDESK_API_KEY=your_free_zendesk_key
ZENDESK_SUBDOMAIN=your_free_zendesk_subdomain
```

---

## 10. Hackathon Submission Checklist

- [ ] GitHub repo named `TeamName_TeamLeader_Jazzee2025`
- [ ] `docker-compose.yml` included and fully working for local DBs/Vector stores
- [ ] All five agents implemented in LangGraph utilizing Groq/Llama 3.3
- [ ] Voice interface built using Whisper + Edge TTS
- [ ] Profiling Agent completes in < 3 minutes
- [ ] Local RAG pipeline retrieves ET Prime mock data successfully
- [ ] Multi-modal handoff working end-to-end
- [ ] Pitch video (YouTube, unlisted) — 4-minute demo script showing the features working
- [ ] PDF document: problem statement, architecture diagram, impact metrics
- [ ] AI tool declaration included
- [ ] Submission via Unstop platform before March 29, 2026
