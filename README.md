# AI Product Research Assistant

A production-ready AI agent for product research, pricing analysis, and market trends. Built with Gemini 2.5 Flash, LangChain, ChromaDB, and FastAPI.

## Setup Instructions

### 1. Prerequisites
- Docker & Docker Compose
- Google AI Studio API Key (Gemini)
- Serper Dev API Key (Google Search)

### 2. Environment Setup
Create a `.env` file based on `.env.example` and fill in your API keys:
```bash
GOOGLE_API_KEY=your_gemini_api_key
SERPER_API_KEY=your_serper_api_key
```

### 3. Installation
Build the Docker container:

```bash
docker-compose build
```

---

## Run the Application

Start the services (API and Database):

```bash
docker-compose up
```

- The API will be available at: `http://localhost:8000`
- API Documentation (Swagger UI): `http://localhost:8000/docs`

---

## Test the API

You can test the API using `curl` or the Swagger UI.

### 1. Product Catalog RAG (Inventory check)
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What wireless headphones do we have in stock?"}'
```

### 2. Price Analysis (Math calculation)
The tool now supports advanced filtering, calculating averages, and finding exact prices.
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me products with margins below 50% in Electronics"}'
```

### 3. Web Search (Market trends)
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the current market price for noise-cancelling headphones?"}'
```

### 4. History & Feedback
- Get History: `GET /queries`
- Submit Feedback: `POST /feedback`

---

## Load Testing

I conducted load testing using Locust to ensure the system handles concurrency efficiently. Detailed reports are available in `tests/LOAD_TEST_REPORT.md`.

### Summary Results
| Metric | Result |
|--------|--------|
| **Requests/Sec (RPS)** | 6.1 |
| **Failure Rate** | 0% |
| **Mean Response Time** | ~4,900 ms |

To run the load test locally:

1. Install locust: `pip install locust`
2. Run locust:
   ```bash
   locust -f tests/locustfile.py --host=http://localhost:8000
   ```
3. Open `http://localhost:8089`.

---

---

## Code Structure

```
product-research-assistant/
├── src/
│   ├── agent.py          # Agent logic (LangChain), prompt engineering, and tool selection
│   ├── main.py           # FastAPI entry point, API endpoints (/query, /feedback)
│   ├── tools.py          # Custom tools (RAG, Price Analysis, Web Search) definition
│   ├── vector_store.py   # ChromaDB management, embedding generation, and retrieval
│   ├── data_manager.py   # CSV loading and data processing logic
│   └── database.py       # SQL database connection for logging history/feedback
├── tests/
│   ├── locustfile.py     # Load testing script using Locust
│   └── LOAD_TEST_REPORT.md # Detailed performance test results
├── data/
│   └── products_catalog.csv # Source data for products
├── architecture/         # System design diagrams and documentation
├── Dockerfile            # Container definition for the application
├── docker-compose.yml    # Orchestration for App + Database services
└── requirements.txt      # Python dependencies
```

## Limitations & Future Improvements

### What's Not Implemented
- **Unit Tests**: Comprehensive unit tests for individual tools and agents are not yet implemented.
- **Caching Implementation**: Currently, every query hits the LLM. Implementing a caching layer could improve latency for repeated queries.
- **CI/CD Pipeline**: Automated testing and deployment pipelines are not set up.

### What I Would Improve
- **Reranker Integration**: Implement a Cross-Encoder Reranker (e.g., BGE-Reranker) to ensure the correct chunks are ranked at the top.
- **Advanced Guardrails**: Integrate dedicated security models (ex. Llama Guard) to intercept and block malicious inputs *before* they reach the main LLM.
- **Monitoring Tools**: Integrate sophisticated monitoring platforms like **LangSmith** to track agent traces, latency, and token usage in production.
- **Experiments**: Conduct systematic experiments to compare different LLMs, chunking strategies, and retrieval methods to find the optimal configuration.

### What I Learned
- **RAG with CSV**: Transforming structured CSV rows into meaningful vector embeddings requires creating rich context strings (combining Brand, Price, Description) to maximize semantic search accuracy.
- **Locust Testing**: Gained hands-on experience using Locust to test and evaluate the system's performance under load.
- **Function-Based Tooling**: Learned how to implement custom Python functions as tools to ensure high accuracy and correctness in complex calculations.
- **System Design & Analysis**: Learned to look beyond code by analyzing system architecture, estimating real-world costs and analyzing security risks.

### Challenges Faced
- **Tool Selection Accuracy**: Initially, the Agent confused semantic search with quantitative questions (e.g., using `search_catalog` for "most expensive product" instead of `price_analysis_tool`), leading to incorrect answers. I resolved this by explicitly defining tool scopes in the System Prompt.
- **Synchronous Bottlenecks**: Early load tests failed because blocking synchronous calls caused timeouts. I refactored the architecture to handled requests validation asynchronously to handle concurrency efficiently.
- **Project Analysis**: I had never analyzed cost and security in such depth before. I took this opportunity to research and study these critical aspects to incorporate them into the project.
