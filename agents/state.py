from typing import TypedDict, Optional, List, Dict, Any


class GraphState(TypedDict, total=False):
    """
    Shared stateful context passed sequentially through the 4 LangGraph agent nodes.
    """
    user_message: str
    conversation_messages: List[Dict[str, Any]]
    location: Optional[str]
    guest_count: Optional[int]
    budget: Optional[float]
    max_price: Optional[float]  # Strict price ceiling (e.g. 14000.0 from 'below LKR 14000')
    requested_category: Optional[str]  # "photography" | "hotel_venue" | "catering" | "decorations" | "music" | None
    total_estimate: float
    requires_approval: bool
    workflow_status: str  # "Approved" | "RequiresApproval" | "NeedsClarification" | "In_Progress"
    ai_reply_message: str
    agent_traces: List[Dict[str, Any]]

    # Intermediate architectural fields
    intent: Optional[str]
    missing_parameters: List[str]
    minimum_capacity: Optional[int]
    capacity_buffer_percentage: float
    geo_zone: Optional[str]
    search_radius_km: Optional[int]
    allocated_venue_budget: Optional[float]
    selected_venue_name: Optional[str]
    line_items: List[Dict[str, Any]]
    recommended_vendors: List[Dict[str, Any]]
    confidence_score: float

    # Category package snapshots from the 4 modular tools
    venue_package: Optional[Dict[str, Any]]
    catering_package: Optional[Dict[str, Any]]
    theme_package: Optional[Dict[str, Any]]
    budget_package: Optional[Dict[str, Any]]


# Backward compatibility alias
State = GraphState
