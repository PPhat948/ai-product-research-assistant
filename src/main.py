from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from src.database import get_db, init_db, QueryLog, Feedback
from src.data_manager import product_data_manager
from src.vector_store import vector_store_manager
from src.agent import get_agent, process_agent_response
import os

app = FastAPI(title="AI Product Research Assistant")

# --- Pydantic Models ---
class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    query_id: int
    answer: str
    reasoning: Optional[List[str]] = []
    tools_used: Optional[List[str]] = []

class FeedbackRequest(BaseModel):
    query_id: int
    rating: int # 1-5
    comment: Optional[str] = None

class FeedbackResponse(BaseModel):
    message: str

class HistoryItem(BaseModel):
    id: int
    user_query: str
    agent_response: str
    timestamp: str
    rating: Optional[int] = None
    comment: Optional[str] = None

    class Config:
        from_attributes = True

@app.on_event("startup")
async def startup_event():
    print("Starting up...")
    # 1. Initialize Database
    init_db()
    
    # 2. Load Product Catalog
    csv_path = os.path.join("data", "products_catalog.csv")
    if os.path.exists(csv_path):
        product_data_manager.load_data(csv_path)
        
        # 3. Ingest Data into Vector Store
        df = product_data_manager.get_df()
        vector_store_manager.ingest_data(df)
    else:
        print("Warning: products_catalog.csv not found.")

@app.post("/query", response_model=QueryResponse)
async def run_query(request: QueryRequest, db: Session = Depends(get_db)):
    agent = get_agent()
    
    # Execute Agent Logic
    try:
        # Invoke agent with the standard messages pattern (ASYNC)
        raw_response = await agent.ainvoke({
            "messages": [{"role": "user", "content": request.query}]
        })
        
        # Process and standardize the agent's response using the helper function
        parsed_output = process_agent_response(raw_response)
        
        answer = parsed_output["answer"]
        reasoning_steps = parsed_output["reasoning"]
        tools_used = parsed_output["tools_used"]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # Persist interaction log to database
    log = QueryLog(user_query=request.query, agent_response=answer)
    db.add(log)
    db.commit()
    db.refresh(log)
    
    return QueryResponse(
        query_id=log.id, 
        answer=answer,
        reasoning=reasoning_steps,
        tools_used=list(set(tools_used))  # Remove duplicates
    )

@app.get("/queries", response_model=List[HistoryItem])
def get_history(limit: int = 10, db: Session = Depends(get_db)):
    logs = db.query(QueryLog).order_by(QueryLog.timestamp.desc()).limit(limit).all()
    history = []
    for l in logs:
        rating = None
        comment = None
        if l.feedbacks:
            # Get latest feedback
            last_feedback = l.feedbacks[-1]
            rating = last_feedback.rating
            comment = last_feedback.comment
            
        history.append({
            "id": l.id, 
            "user_query": l.user_query, 
            "agent_response": l.agent_response, 
            "timestamp": str(l.timestamp),
            "rating": rating,
            "comment": comment
        })
    return history

@app.post("/feedback")
def submit_feedback(request: FeedbackRequest, db: Session = Depends(get_db)):
    # Verify query_id exists
    log = db.query(QueryLog).filter(QueryLog.id == request.query_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Query ID not found")
        
    feedback = Feedback(query_id=request.query_id, rating=request.rating, comment=request.comment)
    db.add(feedback)
    db.commit()
    
    return {"message": "Feedback received"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
