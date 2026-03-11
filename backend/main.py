from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from backend.counselor_graph import app as graph_app
from langchain_core.messages import HumanMessage, AIMessage
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI Career Counselor API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    messages: List[dict]
    user_id: str
    cv_data: str | None = None

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        # Convert dict messages to LangChain objects
        input_messages = []
        for msg in request.messages:
            if msg["role"] == "user":
                input_messages.append(HumanMessage(content=msg["content"]))
            else:
                input_messages.append(AIMessage(content=msg["content"]))
        
        # Invoke LangGraph
        # In a real app, we'd use thread_id for persistence, 
        # but for MVP we pass the full history
        result = graph_app.invoke({
            "messages": input_messages,
            "cv_data": request.cv_data or "",
        })
        
        last_message = result["messages"][-1]
        content = last_message.content
        # Newer Gemini models return content as a list of parts
        if isinstance(content, list):
            content = " ".join(
                part["text"] if isinstance(part, dict) and "text" in part else str(part)
                for part in content
            )
        return {
            "content": content,
            "phase": result.get("phase", "unknown")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
