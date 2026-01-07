# Load Test Report
Date: 2026-01-05

## 1. Test Configuration
- **Tool**: Locust
- **Users**: 20 Concurrent Users
- **Spawn Rate**: 5 Users/sec
- **Host**: http://localhost:8000

## 2. Summary Results
| Metric | Result |
|--------|--------|
| **Total Requests** | 46 |
| **Requests/Sec (RPS)** | ~2.3 RPS |
| **Failure Rate** | **0%** (Stable) |
| **Median Response Time** | 4,300 ms (4.3s) |
| **Max Response Time** | 16,585 ms |

## 3. Observations
- **Stability**: The system remained stable with **0% failure rate** throughout the test.
- **Latency**: 
  - The `/health` endpoint responded instantly (**~3ms**).
  - The `/query` endpoint averaged **~4.6s**, which is expected as it waits for the **Gemini 2.5 Flash** API.

## 4. Recommendations for Scaling

Based on these results, here are my strategies to scale the system:

1.  **Horizontal Scaling (GCP Cloud Run)**
    - I can deploy this application to **Google Cloud Run**.
    - This allows the system to automatically spin up more containers when there are many users using the app.

2.  **Caching**
    - Many queries are repetitive (e.g., "bestsellers").
    - I would implement a **Caching** system. If a user asks the same question, the system can return the answer instantly without calling the AI model again.

3.  **Managed Vector Database**
    - Currently, the database runs inside the container (local file).
    - To support millions of products, I would switch to a cloud service like **Pinecone** which is built for scale.
