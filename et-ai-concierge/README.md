# ET AI Concierge

An intelligent AI-powered financial concierge application built with multi-agent orchestration, advanced NLP, and real-time market data integration. The ET AI Concierge provides personalized financial insights, investment recommendations, and market analysis powered by Economic Times' resources and AI agents.

## 🚀 Features

### Core Features
- **Multi-Agent AI System**: Specialized agents for profiling, portfolio analysis, market intelligence, editorial content, and marketplace recommendations
- **Real-Time Chat Interface**: Conversational AI with markdown support and rich text formatting
- **Financial X-Ray**: Comprehensive financial profiling based on user behavior and goals
- **Smart Link Handling**: Hyperlinks styled in blue and open in new tabs for better UX
- **User Authentication**: Secure authentication with NextAuth.js
- **Personalized Recommendations**: AI-driven insights tailored to user personas and goals

### AI Agents
1. **Profiling Agent** - Financial X-Ray analysis and persona detection
2. **Editorial Agent** - Content recommendations from ET Prime
3. **Market Intelligence Agent** - Market trends and stock insights
4. **Marketplace Agent** - Product and service recommendations
5. **Behavioral Monitor** - User behavior tracking and engagement optimization
6. **Intent Router** - Intelligent message routing to appropriate agents
7. **Orchestrator** - Coordination and multi-agent workflow management

### Financial Tools & Resources
- **82+ ET Resources**: Links to guides, calculators, masterclasses, and tools
- **Financial Calculators**: NPS, Home Loan EMI, Tax Planning
- **Market Data**: Stock screeners, IPO hub, crypto tracker
- **Learning**: Masterclasses in technical analysis, wealth building, investment strategies
- **Wealth Planning**: Goal planner, insurance, loans, real estate

## 🏗️ Architecture

### Tech Stack

**Frontend**
- Next.js 16 (React 19)
- TypeScript
- Tailwind CSS
- Framer Motion (animations)
- NextAuth.js (authentication)
- React Markdown (rich text rendering)

**Backend**
- FastAPI
- FastAPI WebSockets
- LangChain & LangGraph (AI orchestration)
- Groq API (LLM inference)
- Mem0 (memory management)
- Edge TTS (text-to-speech)

**Data & Infrastructure**
- PostgreSQL + pgvector (embeddings)
- Redis (caching & sessions)
- Qdrant (vector search)
- Elasticsearch (full-text search)
- Neo4j (knowledge graphs)

**APIs & Services**
- Finnhub (stock market data)
- NewsAPI (news aggregation)
- DuckDuckGo (web search)
- yfinance (financial data)
- Groq LLM (language model)

### Project Structure

```
et-ai-concierge/
├── apps/
│   └── web/                    # Next.js frontend
│       ├── src/
│       │   ├── app/           # Next.js app directory
│       │   ├── components/    # React components
│       │   │   ├── FloatingConcierge.tsx
│       │   │   ├── providers.tsx
│       │   │   └── ui/        # UI components
│       │   ├── auth.ts        # Authentication config
│       │   ├── middleware.ts  # Auth middleware
│       │   └── lib/           # Utilities
│       └── public/
├── packages/
│   ├── agents/                # Python AI agents
│   │   ├── orchestrator.py    # Agent orchestration
│   │   ├── profiling_agent.py
│   │   ├── editorial_agent.py
│   │   ├── market_intelligence_agent.py
│   │   ├── marketplace_agent.py
│   │   ├── behavioral_monitor.py
│   │   ├── intent_router.py
│   │   ├── compliance_wrapper.py
│   │   ├── rag_engine.py      # RAG pipeline
│   │   ├── config.py
│   │   ├── database.py
│   │   └── data/
│   │       └── seed_content.json
│   ├── rag/                   # RAG system
│   │   ├── ingestion/         # Data ingestion
│   │   ├── retrieval/         # Hybrid search
│   │   └── reranking/         # Result reranking
│   └── voice/                 # Voice pipeline
├── scripts/                   # Setup & utilities
│   ├── ingest_et_prime.py
│   ├── seed_personas.py
│   └── init_db.sql
└── docker-compose.yml         # Infrastructure setup
```

## 🛠️ Setup & Installation

### Prerequisites
- Node.js 18+
- Python 3.11+
- Docker & Docker Compose
- Git

### Environment Variables

Create `.env` in the root directory:

```env
# Frontend
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
NEXTAUTH_SECRET=your-secret-key
NEXTAUTH_URL=http://localhost:3000

# Backend
GROQ_API_KEY=your-groq-api-key
FINNHUB_API_KEY=your-finnhub-api-key
NEWSAPI_KEY=your-newsapi-key
DATABASE_URL=postgresql://user:password@localhost:5432/et_concierge
REDIS_URL=redis://localhost:6379
QDRANT_URL=http://localhost:6333
ELASTICSEARCH_URL=http://localhost:9200
NEO4J_URL=bolt://localhost:7687
```

### Quick Start

1. **Clone the repository**
```bash
git clone https://github.com/your-repo/et-ai-concierge.git
cd et-ai-concierge
```

2. **Start infrastructure with Docker Compose**
```bash
docker-compose up -d
```

3. **Install and run frontend**
```bash
cd apps/web
npm install
npm run dev
```

4. **Install and run backend** (in new terminal)
```bash
cd packages/agents
pip install -r requirements.txt
python -m uvicorn orchestrator:app --reload --host 0.0.0.0 --port 8000
```

5. **Access the application**
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs
- Floating Concierge: Available on all pages (bottom-right corner)

## 📚 API Reference

### Chat Endpoint
```
POST /api/chat
Content-Type: application/json

{
  "user_id": "string",
  "session_id": "string",
  "message": "string",
  "modality": "web"
}

Response:
{
  "message": "string",
  "agent_used": "string",
  "recommendations": [],
  "disclaimers": []
}
```

### X-Ray Endpoint
```
POST /api/chat/xray
Content-Type: application/json

{
  "user_id": "string",
  "profile": {...}
}
```

## 🧠 AI Agent Workflows

### Financial X-Ray Flow
1. User completes onboarding questionnaire
2. **Profiling Agent** analyzes responses
3. Persona classification (Conservative, Active Trader, Young Professional, etc.)
4. Generates personalized recommendations
5. Triggers marketplace product suggestions

### Chat Flow
1. User sends message
2. **Intent Router** determines intent (inform, transact, learn, discover)
3. Routes to appropriate agent based on:
   - User persona
   - Sentiment analysis (anxious, frustrated, curious, confident)
   - Query intent
4. Agent generates response with:
   - Core answer
   - ET resource links
   - Compliance disclaimers
5. Response rendered with styled links opening in new tabs

### Content Recommendation Flow
1. **Editorial Agent** receives query
2. Searches RAG pipeline (embeddings + BM25 hybrid search)
3. Applies paywall checks (ET Prime exclusive content)
4. Reranks results by relevance
5. Returns curated articles with links

## 🎯 User Personas

1. **Conservative Saver** - Focus on tax saving, NPS, FDs
2. **Active Trader** - Stock analysis, technical analysis, crypto
3. **Young Professional** - SIP, startups, career growth
4. **Corporate Executive** - Portfolio management, wealth planning
5. **Home Buyer** - Loan comparisons, EMI calculators, property investment

## 🔗 ET Resources Mapping

The application includes 82+ ET resource links organized by category:

- **Markets & Data** (14 items): Stock screeners, IPO hub, market data
- **Wealth & Personal Finance** (17 items): Goal planner, calculators, insurance
- **Mutual Funds** (4 items): Strategies, screeners, ELSS
- **Masterclasses & Courses** (9 items): Technical analysis, passive income, leadership
- **News & Categories** (5 items): Politics, tech, industry
- **Opinion & Editorial** (4 items): Editorial, commentary, insights
- **Learning & Education** (10 items): Guides, investment strategies
- **Lifestyle & Special Sections** (6 items): ET Prime, Panache, NRI
- **AI & Careers** (2 items): AI insights, careers
- **Other** (2 items): ePaper, ET Intelligence

## 📊 UI/UX Features

### Link Styling
- **Color**: Blue (`text-blue-500`)
- **Hover**: Darker blue (`hover:text-blue-700`)
- **Behavior**: Open in new tab (`target="_blank"`)
- **Availability**: Applied in both main chat and floating concierge

### Components
- **FloatingConcierge**: Persistent chat widget on all pages
- **Chat Page**: Full-screen chat interface with sidebar
- **Dashboard**: User analytics and portfolio overview
- **Profile**: User preferences and settings

## 🔐 Security

- **Authentication**: NextAuth.js with secure session management
- **Authorization**: Role-based access to features
- **Compliance**: Financial advice disclaimers in responses
- **Data Protection**: HIPAA-compliant data handling
- **API Security**: JWT token validation
- **Environment Variables**: All secrets managed via .env

## 📈 Performance

- **Caching**: Redis for session and query caching
- **Vector Search**: Qdrant for fast semantic similarity
- **Full-Text Search**: Elasticsearch for indexed content
- **Lazy Loading**: Frontend components load on demand
- **WebSocket Support**: Real-time chat updates

## 🧪 Testing

```bash
# Frontend tests
cd apps/web
npm test

# Backend tests
cd packages/agents
pytest

# Integration tests
npm run test:integration
```

## 🚢 Deployment

### Docker Build
```bash
docker build -f packages/agents/Dockerfile -t et-concierge-backend .
docker build -f apps/web/Dockerfile -t et-concierge-frontend .
```

### Docker Run
```bash
docker-compose up -d
```

## 📝 Database Migrations

```bash
cd packages/agents
python scripts/init_db.sql
python scripts/seed_personas.py
```

## 🐛 Troubleshooting

### 404 Links
If ET resource links return 404 errors:
1. Check `orchestrator.py` → `ET_RESOURCES_MAPPING`
2. Verify URLs exist on economictimes.indiatimes.com
3. Update with correct URLs
4. Restart backend service

### Chat Not Responding
1. Verify backend is running: `http://localhost:8000/docs`
2. Check Groq API key is valid
3. Verify database connectivity: PostgreSQL, Redis running
4. Check browser console for errors

### Vector Search Not Working
1. Ensure Qdrant is running: `http://localhost:6333`
2. Run: `python scripts/ingest_et_prime.py` to populate embeddings
3. Check embedding model is loaded

## 📚 Documentation

- [AGENTS.md](apps/web/AGENTS.md) - AI agent specifications
- [CLAUDE.md](apps/web/CLAUDE.md) - Claude AI integration guide
- Architecture diagrams in `/docs`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is proprietary and confidential. All rights reserved by Economic Times.

## 📞 Support

For issues and questions:
- Create an issue on GitHub
- Contact: support@economictimes.com
- Documentation: https://docs.economictimes.com/concierge

## 🎯 Roadmap

- [ ] Voice input/output integration
- [ ] Advanced portfolio analytics
- [ ] Compliance scoring
- [ ] Multi-language support
- [ ] Mobile app (iOS/Android)
- [ ] Advanced behavioral targeting
- [ ] Real-time portfolio tracking
- [ ] Integration with trading platforms

---

**Built with ❤️ by the Economic Times AI team**

Last updated: March 25, 2026
