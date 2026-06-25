# LLM Cost Autopilot

An intelligent LLM routing layer that sits in front of multiple providers, analyzes each request's complexity, and routes it to the cheapest model capable of handling it; without sacrificing quality.

**Baseline result: 66% cost reduction on 30-request load test vs all-GPT-4o routing.**

**Final result: 62.3% cost reduction on 513 real requests — $2.07 saved vs all-GPT-4o routing.**

## Final Load Test Results (513 prompts)

| Metric | Value |
|--------|-------|
| Total requests | 513 |
| Actual cost | $1.2531 |
| Hypothetical all-GPT-4o cost | $3.3277 |
| Total saved | $2.0746 |
| Cost reduction | 62.3% |
| Tier classification accuracy | 77.2% |
| Failed requests | 0 |

### Model Distribution
| Model | Requests | % of Traffic |
|-------|----------|-------------|
| GPT-4o Mini | 212 | 41.3% |
| Llama 3.2 (Local) | 145 | 28.3% |
| GPT-4o | 99 | 19.3% |
| Claude Sonnet | 57 | 11.1% |
---

## What it does

Most apps send every prompt to the same model regardless of complexity. A question like "what is the capital of France?" costs the same as a multi-step reasoning task. That's wasteful.

LLM Cost Autopilot fixes that by:

1. Classifying each incoming prompt into a complexity tier (simple / moderate / complex)
2. Routing it to the cheapest model that can handle that tier
3. Verifying quality async using GPT-4o as a judge
4. Auto-escalating to a higher tier if the cheap model underperforms
5. Logging every decision so you can see exactly where money is saved

---

## Stack

- **Router:** FastAPI (async)
- **Providers:** OpenAI (GPT-4o, GPT-4o Mini), Anthropic (Claude Sonnet, Claude Haiku), Ollama (Llama 3.2 local)
- **Classifier:** Scikit-learn (logistic regression + random forest)
- **Quality Verification:** LLM-as-judge using GPT-4o
- **Logging:** SQLite + structured JSON
- **Dashboard:** Streamlit
- **Containerization:** Docker + docker-compose

---

## Architecture

```
Incoming Request
      │
      ▼
Complexity Classifier (scikit-learn)
      │
      ├── Tier 1 (simple)   → Llama 3.2 (free, local)
      ├── Tier 2 (moderate) → GPT-4o Mini or Claude Haiku
      └── Tier 3 (complex)  → Claude Sonnet or GPT-4o
                                    │
                                    ▼
                            Response to Caller
                                    │
                                    ▼
                    Async Quality Verifier (GPT-4o judge)
                                    │
                            Log + escalate if needed
```

---

## Day 1 Baseline Results

30 requests across 3 models, same prompts:

| Model | Total Cost | Avg Latency | Success |
|-------|-----------|-------------|---------|
| GPT-4o | $0.017990 | 4676ms | 10/10 |
| GPT-4o Mini | $0.000756 | 5766ms | 10/10 |
| Llama 3.2 (Local) | $0.000000 | 25560ms | 10/10 |

- **Actual cost (mixed routing):** $0.018746
- **Hypothetical all-GPT-4o cost:** $0.054830
- **Savings:** $0.036084 (~66%)

---

## Project Structure

```
llm-cost-autopilot/
├── backend/
│   ├── app.py                    # FastAPI main app
│   ├── router.py                 # Core routing logic
│   ├── classifier.py             # Complexity classifier
│   ├── verifier.py               # Async quality verifier
│   ├── providers/
│   │   ├── base.py               # Unified provider interface
│   │   ├── openai_provider.py
│   │   ├── anthropic_provider.py
│   │   └── ollama_provider.py
│   ├── models/
│   │   ├── registry.py           # ModelConfig dataclass + pricing
│   │   └── routing_config.yaml   # Tier-to-model mapping
│   ├── db/
│   │   ├── database.py           # SQLite setup
│   │   └── logger.py             # Request logging
│   ├── dashboard/
│   │   └── app.py                # Streamlit dashboard
│   ├── data/
│   │   ├── training_prompts.json # 200+ labeled prompts
│   │   └── classifier.pkl        # Trained model
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Setup

**1. Clone and create virtual environment**
```bash
git clone https://github.com/vaibhav-badoliasoft/llm-cost-autopilot.git
cd llm-cost-autopilot
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

**2. Install dependencies**
```bash
cd backend
pip install -r requirements.txt
```

**3. Configure environment**
```bash
copy .env.example .env
# Add your OPENAI_API_KEY and ANTHROPIC_API_KEY
```

**4. Start Ollama**
```bash
ollama serve
ollama pull llama3.2
```

**5. Run Day 1 test**
```bash
python test_day1.py
```

---

## Build Progress

- [x] Step1: Provider abstraction + model registry
- [x] Step2: Complexity classifier
- [x] Step 3: FastAPI router
- [x] Step 4: Async quality verifier
- [x] Step 5: SQLite logging + cost tracking
- [x] Step 6: Streamlit dashboard
- [x] Step 7: Docker + final eval

---

## Author

Vaibhav Saini: [GitHub](https://github.com/vsaini06) · [Portfolio](https://vaibhavsaini-portfolio.vercel.app/)