from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Literal, Optional, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import uvicorn
import uuid

# --- LangGraph Setup ---

class AgentState(TypedDict):
    number: int
    prediction: Optional[str]
    human_feedback: Optional[str]
    final_result: Optional[str]

def predict_node(state: AgentState):
    """Predicts if the number is even or odd."""
    number = state["number"]
    prediction = "even" if number % 2 == 0 else "odd"
    return {"prediction": prediction}

def human_review_node(state: AgentState):
    """Processes human feedback."""
    feedback = state.get("human_feedback")
    prediction = state.get("prediction")
    
    if feedback == "confirm":
        return {"final_result": f"Confirmed: {prediction}"}
    else:
        # If user rejects, we might flip the prediction or just say rejected
        # For this simple logic, let's just say "User corrected to " + opposite
        corrected = "odd" if prediction == "even" else "even"
        return {"final_result": f"User corrected to: {corrected}"}

# Build the graph
builder = StateGraph(AgentState)
builder.add_node("predict", predict_node)
builder.add_node("human_review", human_review_node)

builder.set_entry_point("predict")
builder.add_edge("predict", "human_review")
builder.add_edge("human_review", END)

# IMPORTANT: Interrupt before human_review to allow HITL
memory = MemorySaver()
graph = builder.compile(checkpointer=memory, interrupt_before=["human_review"])


# --- FastAPI Setup ---

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PredictRequest(BaseModel):
    number: int
    thread_id: str

class FeedbackRequest(BaseModel):
    thread_id: str
    action: Literal["confirm", "reject"]

@app.post("/predict")
async def predict(req: PredictRequest):
    config = {"configurable": {"thread_id": req.thread_id}}
    initial_state = {"number": req.number}
    
    # Run the graph. It should stop before 'human_review'
    # stream_mode="values" returns the state after each step (or final)
    # We want to run until it pauses.
    
    events = list(graph.stream(initial_state, config))
    
    # Get the current state (snapshot) to see the prediction
    snapshot = graph.get_state(config)
    
    if not snapshot.values:
        return {"error": "Something went wrong"}
        
    return {
        "prediction": snapshot.values.get("prediction"),
        "status": "waiting_for_confirmation"
    }

@app.post("/confirm")
async def confirm(req: FeedbackRequest):
    config = {"configurable": {"thread_id": req.thread_id}}
    
    # Update the state with the human feedback
    # We pretend the 'human_review' node is receiving this input
    # Actually, we update the state and then RESUME
    
    # In LangGraph, to provide input for a resume, we usually update the state
    # or pass input to the resume command.
    # For this simple node, let's update state manually then resume.
    
    graph.update_state(config, {"human_feedback": req.action})
    
    # Resume the graph. None means "continue execution" from where it paused.
    # The 'human_review' node will now run with the updated state.
    events = list(graph.stream(None, config))
    
    # Get final result
    snapshot = graph.get_state(config)
    final_res = snapshot.values.get("final_result", "Done")
    
    return {"result": final_res}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
