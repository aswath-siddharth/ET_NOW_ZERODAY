from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
import datetime

app = FastAPI(title="ET AI Concierge API")

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    session_id: str

@app.get("/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.datetime.utcnow().isoformat()}

@app.post("/api/chat")
async def chat(request: ChatRequest):
    # This is a stub for the LangGraph Orchestrator Execution
    # In production, this would invoke exactly:
    # state = await graph.ainvoke({"conversation_history": [request.message]})
    # Here we simulate the routing to workers
    
    response_msg = ""
    lower_msg = request.message.lower()
    
    if "gold" in lower_msg or "market" in lower_msg or "buy" in lower_msg:
        response_msg = f"Based on your profile, I'm checking the real-time MCX Gold price via the Market Intelligence Agent, and fetching the latest ET Prime analysis for '{request.message}'."
    elif "loan" in lower_msg:
        response_msg = f"Let me connect you with the Marketplace Agent to compare SBI, HDFC, and Kotak rates considering your credit score."
    else:
        response_msg = "I am the ET AI Concierge. I've routed your query through our Knowledge Graph. Here are the top insights..."
        
    return {"message": response_msg, "session_id": request.session_id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
