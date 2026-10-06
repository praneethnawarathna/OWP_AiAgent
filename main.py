import os
import time
import logging
import traceback
from pathlib import Path
from typing import Dict, Any, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END

# ─── Environment Configuration ────────────────────────────────────────────────
ENV_FILE = Path(__file__).resolve().parent / ".env"
if ENV_FILE.exists():
    load_dotenv(dotenv_path=ENV_FILE)
else:
    load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("OleenaAIAgent")

# ─── Modular Agent Imports ────────────────────────────────────────────────────
from agents.state import GraphState, State
from agents.planner_agent import (
    planner_node,
    check_parameters_condition,
    OPENAI_MODEL,
    OPENAI_BASE_URL,
    OPENAI_API_KEY
)
from agents.domain_analyst_agent import domain_analyst_node
from agents.tool_agent import tool_agent_node
from agents.safety_agent import safety_agent_node


# ─────────────────────────────────────────────────────────────────────────────
# Strongly-Typed Pydantic Models for FastAPI
# ─────────────────────────────────────────────────────────────────────────────

class AgentTraceModel(BaseModel):
    step_name: str
    status: str = "SUCCESS"  # SUCCESS | FAILED | PAUSED
    execution_time_ms: float
    output: Dict[str, Any] = Field(default_factory=dict)


class WorkflowRequest(BaseModel):
    prompt: Optional[str] = None
    message: Optional[str] = None
    messages: Optional[List[Dict[str, Any]]] = None
    budget: Optional[float] = None
    max_price: Optional[float] = None
    location: Optional[str] = None
    guest_count: Optional[int] = None
    requested_category: Optional[str] = None
    category: Optional[str] = None


class WorkflowResponse(BaseModel):
    workflow_id: str
    workflow_status: str
    status: str
    confidence_score: float
    requires_approval: bool
    requires_human_approval: bool
    total_estimate: float
    total_estimate_lkr: float
    ai_reply_message: str
    final_response: str
    location: Optional[str] = None
    guest_count: Optional[int] = None
    budget: Optional[float] = None
    max_price: Optional[float] = None
    requested_category: Optional[str] = None
    recommended_vendors: List[Dict[str, Any]] = Field(default_factory=list)
    recommendedVendors: List[Dict[str, Any]] = Field(default_factory=list)
    line_items: List[Dict[str, Any]] = Field(default_factory=list)
    agent_traces: List[AgentTraceModel] = Field(default_factory=list)
    venue_package: Optional[Dict[str, Any]] = None
    catering_package: Optional[Dict[str, Any]] = None
    theme_package: Optional[Dict[str, Any]] = None
    budget_package: Optional[Dict[str, Any]] = None


# ─────────────────────────────────────────────────────────────────────────────
# LangGraph Workflow Graph Assembly & Compilation
# ─────────────────────────────────────────────────────────────────────────────

def create_wedding_agent_workflow():
    """
    Assembles and compiles the LangGraph StateGraph:
      START -> Planner -> [Condition: Missing Parameters?] -> END
                       -> [Condition: Complete] -> Domain Analyst -> Tool Agent -> Safety Agent -> END
    """
    workflow = StateGraph(GraphState)

    # 1. Register the 4 distinct modular agent nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("domain_analyst", domain_analyst_node)
    workflow.add_node("tool_agent", tool_agent_node)
    workflow.add_node("safety_agent", safety_agent_node)

    # 2. Entry edge
    workflow.add_edge(START, "planner")

    # 3. Conditional routing from Planner Node
    workflow.add_conditional_edges(
        "planner",
        check_parameters_condition,
        {
            "end": END,
            "domain_analyst": "domain_analyst"
        }
    )

    # 4. Sequential execution pipeline
    workflow.add_edge("domain_analyst", "tool_agent")
    workflow.add_edge("tool_agent", "safety_agent")
    workflow.add_edge("safety_agent", END)

    return workflow.compile()


# Compile global workflow runner
wedding_agent_graph = create_wedding_agent_workflow()


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI Web Application & CORS Setup
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Oleena Wedding Planner - LangGraph Multi-Agent API",
    description="Modular 4-Agent Sequential Pipeline powered by LangGraph, Neon PostgreSQL, and OpenAI-Compatible Engine",
    version="6.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    """Health check and architecture specification endpoint."""
    return {
        "status": "healthy",
        "architecture": "LangGraph Stateful 4-Agent Modular Pipeline",
        "llm_engine": {
            "model": OPENAI_MODEL,
            "endpoint": OPENAI_BASE_URL or "default",
            "configured": bool(OPENAI_API_KEY),
            "single_call_policy": "Node 1 (Planner Agent) only"
        },
        "graph_nodes": [
            {"node": "planner", "file": "agents/planner_agent.py", "type": f"LLM Intent & Parameter Extraction ({OPENAI_MODEL})"},
            {"node": "domain_analyst", "file": "agents/domain_analyst_agent.py", "type": "Deterministic Spatial & Capacity Engine (Pure Python)"},
            {"node": "tool_agent", "file": "agents/tool_agent.py", "type": "Deterministic PostgreSQL & Line Item Math Engine"},
            {"node": "safety_agent", "file": "agents/safety_agent.py", "type": "Deterministic Math Audit & Gatekeeper Policy (>100k LKR)"},
        ]
    }


# ─────────────────────────────────────────────────────────────────────────────
# Master LangGraph Workflow Endpoint: POST /api/agent/workflows
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/agent/workflows", response_model=WorkflowResponse)
def execute_langgraph_workflow(request: WorkflowRequest):
    """
    Executes the compiled LangGraph 4-agent state machine.
    """
    workflow_id = f"wf_{int(time.time() * 1000)}"

    # Robust State Management: Determine prompt text from message, prompt, or messages history
    prompt_str = ""
    if request.message and request.message.strip():
        prompt_str = request.message.strip()
    elif request.prompt and request.prompt.strip():
        prompt_str = request.prompt.strip()
    elif request.messages:
        for m in reversed(request.messages):
            if isinstance(m, dict) and m.get("role") in ("user", "human"):
                content = str(m.get("content", "")).strip()
                if content:
                    prompt_str = content
                    break
    if not prompt_str:
        prompt_str = "Hello"

    initial_state: GraphState = {
        "user_message": prompt_str,
        "conversation_messages": request.messages or [],
        "location": request.location,
        "guest_count": request.guest_count,
        "budget": request.budget,
        "max_price": request.max_price,
        "requested_category": request.requested_category or request.category,
        "total_estimate": 0.0,
        "requires_approval": False,
        "workflow_status": "Starting",
        "ai_reply_message": "",
        "agent_traces": [],
        "line_items": [],
        "recommended_vendors": [],
        "confidence_score": 1.0,
    }

    try:
        final_state: GraphState = wedding_agent_graph.invoke(initial_state)

        workflow_status = final_state.get("workflow_status", "Approved")
        confidence_score = final_state.get("confidence_score", 1.0)
        requires_approval = final_state.get("requires_approval", False)
        total_estimate = final_state.get("total_estimate", 0.0)
        ai_reply = final_state.get("ai_reply_message", "")
        recommended = final_state.get("recommended_vendors", [])
        line_items = final_state.get("line_items", [])
        traces = [AgentTraceModel(**t) for t in final_state.get("agent_traces", [])]

        return WorkflowResponse(
            workflow_id=workflow_id,
            workflow_status=workflow_status,
            status=workflow_status,
            confidence_score=confidence_score,
            requires_approval=requires_approval,
            requires_human_approval=requires_approval,
            total_estimate=total_estimate,
            total_estimate_lkr=total_estimate,
            ai_reply_message=ai_reply,
            final_response=ai_reply,
            location=final_state.get("location"),
            guest_count=final_state.get("guest_count"),
            budget=final_state.get("budget"),
            max_price=final_state.get("max_price"),
            requested_category=final_state.get("requested_category"),
            recommended_vendors=recommended,
            recommendedVendors=recommended,
            line_items=line_items,
            agent_traces=traces,
            venue_package=final_state.get("venue_package"),
            catering_package=final_state.get("catering_package"),
            theme_package=final_state.get("theme_package"),
            budget_package=final_state.get("budget_package")
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"[{workflow_id}] LangGraph execution failure: {exc}", exc_info=True)
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"LangGraph Workflow Error: {type(exc).__name__}: {str(exc)}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Backwards-Compatible Chat Endpoint: POST /api/agent/chat
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/agent/chat")
def chat_compatibility_endpoint(req: WorkflowRequest):
    """
    Backwards-compatible wrapper delegating to the LangGraph Multi-Agent Pipeline.
    Directly interfaces with Flutter chat and external frontend clients.
    """
    workflow_res = execute_langgraph_workflow(req)
    return {
        "textResponse": workflow_res.final_response,
        "recommendedVendors": workflow_res.recommendedVendors,
        "domain": "wedding_planning",
        "status": workflow_res.status,
        "workflow_id": workflow_res.workflow_id,
        "confidence_score": workflow_res.confidence_score,
        "requires_human_approval": workflow_res.requires_human_approval,
        "total_estimate_lkr": workflow_res.total_estimate_lkr,
        "location": workflow_res.location,
        "guest_count": workflow_res.guest_count,
        "budget": workflow_res.budget,
        "max_price": workflow_res.max_price,
        "requested_category": workflow_res.requested_category,
        "line_items": workflow_res.line_items,
        "venue_package": workflow_res.venue_package,
        "catering_package": workflow_res.catering_package,
        "theme_package": workflow_res.theme_package,
        "budget_package": workflow_res.budget_package,
        "agent_traces": [t.model_dump() for t in workflow_res.agent_traces]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
