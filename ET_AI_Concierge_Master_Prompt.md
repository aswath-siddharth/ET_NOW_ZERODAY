# ET AI Concierge — Master Engineering Prompt
### Complete Build Specification with Tech Stack

---

## 0. Project Identity

**Product name:** ET AI Concierge — "Your Financial Life Navigator"
**Platform target:** Web (Next.js), Mobile (React Native / Expo), Voice (Daily.co + Deepgram + ElevenLabs)
**Architecture style:** Multi-Agent System (MAS) with Orchestrator-Worker pattern
**Primary language:** TypeScript (frontend + API layer), Python (agent backend)
**Deadline context:** ET GenAI Hackathon 2026 — Phase 2 prototype by March 29, 2026
**Repo naming convention:** `TeamName_TeamLeader_Jazzee2025`

---

## 1. Problem Statement to Encode in Every Agent

The Economic Times ecosystem spans ET Prime (editorial analysis), ET Markets (trading tools), ETMasterclass (learning), and a financial services Marketplace. Despite the depth, the average user discovers less than 10% of available value — the "Discovery Paradox." Every agent you build must be wired with one directive: **bridge the gap between what the user knows exists and what they actually need.**

---

## 2. Full Tech Stack (Canonical Reference)

### 2.1 Backend — Agent Runtime

| Concern | Tool | Why |
|---|---|---|
| Agent orchestration | **LangGraph (Python)** | Stateful, graph-based multi-agent workflows; native checkpointing |
| LLM | **Claude Sonnet 4.5** (`claude-sonnet-4-5-20251001`) | Best tool-use accuracy; already used in Artifact layer; no model-switching overhead |
| Agent memory (persistent) | **Mem0** | Cross-session user profile memory; financial goals persist between logins |
| Short-term session state | **Redis (Upstash)** | Ephemeral in-flight conversation state; sub-1ms reads |
| Durable user profiles | **Supabase (PostgreSQL)** | User personas, risk scores, goal states, onboarding results |
| Task queue | **Celery + Redis** | Async background jobs: portfolio drift checks, proactive nudges |
| API gateway | **FastAPI** | All agent tool endpoints; async-native; OpenAPI schema auto-generation |

### 2.2 Retrieval — RAG Pipeline

| Concern | Tool | Why |
|---|---|---|
| Vector store | **Qdrant** (self-hosted) | Open-source; data stays on Indian servers (DPDP Act compliance) |
| Lexical search | **BM25 (Elasticsearch)** | Exact ticker/entity matching ("MRF", "Nifty 50") |
| Hybrid fusion | **Reciprocal Rank Fusion (RRF)** | Merges vector + lexical result sets without score normalization complexity |
| Reranker | **Cohere Rerank v3** | Cross-encoder precision on financial text; significant generation quality lift |
| Knowledge graph | **Neo4j Aura** | GraphRAG: entity relationships (policy → sector → stock → outcome) |
| Embedding model | **text-embedding-3-large (OpenAI)** | 3072-dim; best financial text clustering in benchmarks |
| Document ingestion | **LlamaIndex** | Chunk ETL pipeline for ET Prime articles, PDFs, market reports |

### 2.3 Voice Stack

| Concern | Tool | Why |
|---|---|---|
| STT | **Deepgram Nova-3** | 54.2% lower WER on noisy audio; <300ms latency; Hindi-English code-switch support |
| TTS | **ElevenLabs Expressive Mode** | Emotionally intelligent voice; adapts tone to financial context (calm vs. urgent) |
| Real-time audio transport | **Daily.co** | Cleaner React + React Native SDK than LiveKit; built-in room state; cross-platform |
| Voice pipeline orchestration | **LiveKit Agents SDK** | Thin wrapper connecting Deepgram → LangGraph → ElevenLabs in <500ms E2E |

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
| Real-time market data | **Finnhub API** | Nifty 50, Sensex, MCX Gold, stock quotes |
| ET Prime content | **ET internal RAG corpus** | Ingest via LlamaIndex; refresh every 15 min |
| Mutual fund NAVs | **AMFI API** (free, official) | Real NAV data; no third-party dependency |
| RBI policy / rates | **RBI public RSS + scraper** | Monetary policy, repo rate, regulatory circulars |
| Home loan rates | **Partner bank simulators** | SBI, HDFC, Kotak — mock APIs for hackathon; schema matches real APIs |
| Weather (cross-sell triggers) | **OpenWeatherMap API** | Location-based contextual offers |
| User location | **Browser Geolocation API** | Smart city + regional offer personalization |

### 2.6 Observability & Compliance

| Concern | Tool | Why |
|---|---|---|
| Agent tracing | **LangSmith** | Native LangGraph integration; every agent step logged with input/output |
| Error tracking | **Sentry** | Frontend + backend; session replays for demo debugging |
| Compliance audit log | **Custom Postgres table** | Every AI recommendation logged: agent ID, timestamp, reasoning, user ID |
| HITL escalation | **Zendesk webhook** | Trigger human handoff on high-stakes actions (large fund transfers, claim disputes) |
| Bias monitoring | **Arize AI (free tier)** | Drift detection on recommendation distribution |
| Secrets management | **Doppler** | No `.env` files in repo; inject at runtime |

### 2.7 Infrastructure

| Concern | Tool |
|---|---|
| Containerization | Docker + Docker Compose |
| Cloud (primary) | AWS Mumbai region (ap-south-1) — data localization |
| Serverless functions | AWS Lambda (Python) for background agents |
| CDN | CloudFront |
| CI/CD | GitHub Actions |
| Local dev | `docker-compose up` — entire stack runs locally |

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
    get_user_profile,          # reads from Mem0 + Supabase
    update_user_profile,       # writes back to Mem0
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

**Role:** Onboards new users in under 3 minutes. Converts a first-time visitor into a high-fidelity financial persona. Writes the result to Mem0 and Supabase.

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

**Persona → product mapping table (encode as JSON in agent config):**
```json
{
  "PERSONA_CONSERVATIVE_SAVER": {
    "primary_tools": ["ET Wealth Edition", "NPS Calculator", "FD Rate Tracker"],
    "et_prime_sections": ["Personal Finance", "Tax Saving"],
    "masterclass": null,
    "marketplace_products": ["Fixed Deposits", "NPS", "Health Insurance"]
  },
  "PERSONA_ACTIVE_TRADER": {
    "primary_tools": ["Alpha Trades", "Stock Reports Plus", "Candlestick Screener", "RSI Screener"],
    "et_prime_sections": ["Markets", "Tech", "Corporate Governance"],
    "masterclass": "Technical Analysis Masterclass",
    "marketplace_products": ["Demat Account", "Margin Loans"]
  },
  "PERSONA_YOUNG_PROFESSIONAL": {
    "primary_tools": ["ET Wealth SIP Guide", "Young Mind Program", "AI for Business Leaders"],
    "et_prime_sections": ["Startups", "Tech", "Career"],
    "masterclass": "Young Mind Entrepreneurship Program",
    "marketplace_products": ["SIP platforms", "Term Insurance", "Credit Card"]
  },
  "PERSONA_CORPORATE_EXECUTIVE": {
    "primary_tools": ["ET Prime", "Wealth Edition", "Today's ePaper"],
    "et_prime_sections": ["Corporate Governance", "Aviation", "Auto", "Pharma"],
    "masterclass": "Strategic Leadership Masterclass",
    "marketplace_products": ["Premium Credit Cards", "Portfolio Management Services"]
  },
  "PERSONA_HOME_BUYER": {
    "primary_tools": ["Home Loan EMI Calculator", "Loan Marketplace", "RBI Rate Tracker"],
    "et_prime_sections": ["Real Estate", "Digital Real Estate", "Infrastructure"],
    "masterclass": "Build Passive Income with Mutual Funds",
    "marketplace_products": ["Home Loans (SBI, HDFC, Kotak)", "Home Insurance"]
  }
}
```

**Output written to Mem0:**
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

**Role:** Surfaces the right ET Prime / ET Wealth content for any user query or behavioral signal. Uses the full RAG pipeline.

**Tools:**
```python
tools = [
    hybrid_rag_search,          # vector + BM25 over ET Prime corpus
    graph_rag_entity_search,    # Neo4j: find related entities/articles
    cohere_rerank,              # rerank top-20 results to top-3
    get_user_interests,         # pull from Mem0 to personalize search
    check_paywall_status,       # determine if user has ET Prime subscription
    generate_article_summary,   # 3-sentence summary of retrieved article
]
```

**RAG pipeline implementation:**
```python
async def editorial_rag_pipeline(query: str, user_profile: UserProfile) -> list[Article]:
    # Step 1: Hybrid retrieval
    vector_results = await qdrant_client.search(
        collection_name="et_prime_articles",
        query_vector=embed(query),
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

    # Step 4: Rerank
    reranked = await cohere_client.rerank(
        query=query,
        documents=[r.text for r in fused],
        model="rerank-english-v3.0",
        top_n=3
    )

    return reranked
```

**Context-sensitive intent routing:**
```python
# Same query, different outputs by persona
if user_profile.persona == "PERSONA_ACTIVE_TRADER":
    # "Tell me about gold" → real-time MCX Gold price + technical analysis article
    return await market_intelligence_agent.get_gold_technical(user_id)
elif user_profile.persona == "PERSONA_CORPORATE_EXECUTIVE":
    # "Tell me about gold" → ET Prime exclusive on GIFT City gold volumes
    return await editorial_rag_pipeline("gold GIFT City volumes plunging", user_profile)
elif user_profile.persona == "PERSONA_CONSERVATIVE_SAVER":
    # "Tell me about gold" → sovereign gold bonds comparison vs physical gold
    return await editorial_rag_pipeline("sovereign gold bond vs physical gold returns", user_profile)
```

**Paywall handling:**
```python
if not user.has_et_prime_subscription:
    response.append({
        "type": "paywall_nudge",
        "message": "This exclusive analysis is from ET Prime.",
        "cta": "You've read 3 premium stories today. Get full access for ₹199/month.",
        "deeplink": "https://buy.indiatimes.com/ET/plans",
        "trigger": "USAGE_LIMIT_REACHED"   # signals Cross-Sell Engine
    })
```

---

### Agent 3 — Market Intelligence Agent

**Role:** Real-time market data, technical signals, portfolio analysis, and "Big Bull" portfolio tracking via ET Markets.

**Tools:**
```python
tools = [
    finnhub_get_quote,              # real-time stock/index prices
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

**Portfolio drift detection:**
```python
def calculate_portfolio_drift(
    current_allocation: dict,   # {"equity": 0.72, "debt": 0.18, "gold": 0.10}
    target_allocation: dict,    # {"equity": 0.60, "debt": 0.30, "gold": 0.10}
    threshold: float = 0.05
) -> DriftReport:
    drifts = {
        asset: abs(current_allocation[asset] - target_allocation[asset])
        for asset in current_allocation
    }
    max_drift = max(drifts.values())
    requires_rebalance = max_drift > threshold

    if requires_rebalance:
        return DriftReport(
            alert=True,
            message=f"Your equity allocation has drifted {max_drift*100:.1f}% above target.",
            suggestion="Consider rebalancing by increasing your debt allocation.",
            et_tool_deeplink="https://economictimes.indiatimes.com/markets/portfolio",
            et_prime_article=editorial_agent.search("portfolio rebalancing strategy 2025")
        )
```

**Morning briefing parallel fan-out (LangGraph pattern):**
```python
# Orchestrator spawns these simultaneously — results gathered and synthesized
async def morning_briefing(user_id: str) -> Briefing:
    results = await asyncio.gather(
        market_intelligence_agent.get_index_summary(),    # Nifty/Sensex overnight moves
        editorial_agent.get_top_stories(user_id),         # personalized ET Prime top 3
        market_intelligence_agent.get_portfolio_update(user_id),  # portfolio vs yesterday
        get_weather_for_location(user_id),                # location-based context
    )
    return orchestrator.synthesize_briefing(results, user_id)
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

**Zero-trust data handling (encode in every tool that touches PII):**
```python
class PrivacyFilter:
    """Strip PII before any LLM call. Only minimum necessary data to the model."""
    ALLOWED_FIELDS_FOR_LLM = ["credit_score_band", "loan_amount", "tenure_months",
                               "income_band", "employer_type", "age_group"]

    def sanitize_for_llm(self, user_data: dict) -> dict:
        return {k: v for k, v in user_data.items() if k in self.ALLOWED_FIELDS_FOR_LLM}
```

**Loan recommendation with personalized ranking:**
```python
async def get_loan_recommendations(user: UserProfile, loan_amount: int, tenure: int):
    all_offers = await compare_loan_rates(loan_amount, tenure)

    # Rank by approval probability first, then by rate
    ranked = sorted(
        all_offers,
        key=lambda x: (
            -calculate_approval_probability(user, x),   # higher probability first
            x.interest_rate                              # then lower rate
        )
    )

    # Consultative framing — guided, not sold
    return {
        "top_pick": ranked[0],
        "reasoning": f"Based on your credit profile and employer type, "
                     f"{ranked[0].bank} has a ~{ranked[0].approval_probability}% "
                     f"approval likelihood for you at {ranked[0].rate}% p.a.",
        "alternatives": ranked[1:3],
        "et_article": await editorial_agent.search("home loan tips first-time buyer 2025"),
        "escalate_available": True
    }
```

**HITL escalation trigger:**
```python
HITL_TRIGGERS = [
    lambda action: action.type == "FUND_TRANSFER" and action.amount > 100000,
    lambda action: action.type == "INSURANCE_CLAIM",
    lambda action: action.type == "LOAN_APPLICATION_SUBMIT",
    lambda action: user.sentiment == "FRUSTRATED" and action.type == "COMPLAINT",
]

async def execute_with_hitl_check(action: AgentAction, user: UserProfile):
    if any(trigger(action) for trigger in HITL_TRIGGERS):
        await zendesk_webhook.create_ticket(
            subject=f"HITL Required: {action.type}",
            user_id=user.id,
            conversation_context=action.conversation_summary,
            priority="high"
        )
        return HumanHandoffResponse(
            message="I'm connecting you with a specialist who can help with this directly.",
            estimated_wait="< 2 minutes",
            ticket_id=ticket.id
        )
    return await execute_action(action)
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
    {
        "name": "YOUNG_MIND_HEAVY_USER",
        "condition": lambda s: s.page_views["young-mind"] >= 5
                               and not s.enrolled_in["young-mind-program"],
        "action": "offer_young_mind_enrollment",
        "message": "You've been exploring the Young Mind content a lot. "
                   "The full program opens 8 live mentorship sessions with founders.",
    },
]
```

---

## 4. Multi-Modal Handoff — Voice ↔ Web ↔ Mobile

This is the single most impressive feature to demo. Implement it completely.

**Architecture:**
```
User starts on voice (driving)
  → Deepgram STT transcribes
  → LangGraph processes, updates session in Redis
  → ElevenLabs speaks response
  → Session ID stored in Mem0 with full context

User opens web app 30 minutes later
  → Frontend calls GET /api/session/resume?userId=X
  → Redis returns active session context
  → Web UI renders conversation history
  → "Welcome back. You were asking about home loans earlier. 
     Here's the SBI vs HDFC comparison I mentioned."
  → Full context, zero repetition
```

**Session resume API endpoint:**
```python
@app.get("/api/session/resume")
async def resume_session(user_id: str, modality: str):
    # Pull from Redis (recent session) or Mem0 (historical)
    recent = await redis_client.get(f"session:{user_id}:latest")
    if recent:
        session = SessionState(**json.loads(recent))
        # Generate a transition message
        transition_msg = await orchestrator.generate_transition_message(
            session=session,
            new_modality=modality,
            time_gap_minutes=session.minutes_since_last_interaction
        )
        return {"session": session, "transition_message": transition_msg}
    # Fall back to full profile from Mem0
    profile = await mem0_client.get_all(user_id=user_id)
    return {"profile": profile, "is_new_session": True}
```

**Frontend session resume component (Next.js):**
```tsx
// app/dashboard/page.tsx
export default async function Dashboard() {
  const session = await resumeSession(userId, 'web');

  return (
    <div>
      {session.transition_message && (
        <TransitionBanner message={session.transition_message} />
        // "Welcome back. Continuing from your voice conversation —
        //  here's the home loan comparison you asked about."
      )}
      <ConciergeChat initialMessages={session.conversation_history} />
    </div>
  );
}
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
            "model_used": "claude-sonnet-4-5",
            "data_sources": agent_response.sources,
        })

        # 3. Check HITL triggers before returning
        if self.requires_human_oversight(agent_response):
            return self.escalate_to_human(agent_response, user)

        return agent_response

    def requires_human_oversight(self, response: AgentResponse) -> bool:
        HIGH_STAKES_TYPES = ["LOAN_APPLICATION", "INSURANCE_CLAIM", "LARGE_TRANSFER"]
        return response.type in HIGH_STAKES_TYPES or response.confidence_score < 0.7
```

**Audit log schema (Postgres):**
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

**Chat UI — streaming implementation (Next.js + SSE):**
```tsx
// components/ConciergeChat.tsx
export function ConciergeChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);

  const sendMessage = async (userMessage: string) => {
    setIsStreaming(true);
    const response = await fetch('/api/chat', {
      method: 'POST',
      body: JSON.stringify({ message: userMessage, sessionId }),
    });

    const reader = response.body!.getReader();
    let agentMessage = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = new TextDecoder().decode(value);
      agentMessage += chunk;
      setMessages(prev => updateLastMessage(prev, agentMessage)); // live token streaming
    }
    setIsStreaming(false);
  };

  return (
    <div className="flex flex-col h-full">
      <MessageList messages={messages} />
      {isStreaming && <TypingIndicator agentName="ET Concierge" />}
      <VoiceOrTextInput onSend={sendMessage} />
    </div>
  );
}
```

---

## 7. Demo Script for Judges

Build your hackathon demo around this exact 4-minute narrative:

```
[0:00 – 0:45] — Voice onboarding
  Show voice interface. User speaks: "I'm a 28-year-old software engineer.
  I want to start investing but I don't know where."
  Profiling Agent asks 3 follow-up questions via ElevenLabs voice.
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
│   ├── voice/                  # Daily.co + Deepgram + ElevenLabs
│   └── shared/                 # TypeScript types shared across web/mobile
├── infra/
│   ├── docker-compose.yml      # local dev: all services
│   └── aws/                    # production CDK stack
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
# LLM
ANTHROPIC_API_KEY=

# Voice
DEEPGRAM_API_KEY=
ELEVENLABS_API_KEY=
DAILY_API_KEY=

# Memory & State
MEM0_API_KEY=
UPSTASH_REDIS_URL=
UPSTASH_REDIS_TOKEN=
SUPABASE_URL=
SUPABASE_SERVICE_KEY=

# Vector & Search
QDRANT_URL=
QDRANT_API_KEY=
ELASTICSEARCH_URL=
COHERE_API_KEY=

# Knowledge Graph
NEO4J_URI=
NEO4J_USER=
NEO4J_PASSWORD=

# Market Data
FINNHUB_API_KEY=
OPENWEATHERMAP_API_KEY=

# Observability
LANGSMITH_API_KEY=
SENTRY_DSN=

# Compliance
ZENDESK_API_KEY=
ZENDESK_SUBDOMAIN=
```

---

## 10. Hackathon Submission Checklist

- [ ] GitHub repo named `TeamName_TeamLeader_Jazzee2025`
- [ ] All five agents implemented and wired in LangGraph
- [ ] Voice → Web multi-modal handoff working end-to-end
- [ ] Profiling Agent completes in < 3 minutes (time it)
- [ ] Compliance wrapper on every agent response
- [ ] Audit log table populated during demo
- [ ] LangSmith trace visible during demo (open in second tab)
- [ ] HITL escalation triggered at least once in demo
- [ ] Behavioral Monitor fires at least 2 cross-sell triggers in demo
- [ ] Pitch video (YouTube, unlisted) — 4-minute demo script above
- [ ] PDF document: problem statement, architecture diagram, impact metrics
- [ ] AI tool declaration included (list all GenAI tools used in ideation)
- [ ] Submission via Unstop platform before March 29, 2026

---

*Built for the ET GenAI Hackathon 2026. Every Indian deserves a personal guide to their financial life.*
