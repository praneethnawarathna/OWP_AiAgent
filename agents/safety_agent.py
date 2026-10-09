import time
import logging
from typing import Dict, Any, List
from agents.state import GraphState

logger = logging.getLogger("OleenaAIAgent")

APPROVAL_THRESHOLD_LKR = 100000.0


def safety_agent_node(state: GraphState) -> Dict[str, Any]:
    """
    Node 4: Safety & Policy Gatekeeper Agent (Deterministic Math Audit & Gatekeeper Policy):
    - Audits line items and calculates exact sum of costs.
    - Validates total estimate against line item summation.
    - Applies Gatekeeper Policy: Any workflow with total estimate > LKR 100,000
      requires human supervisor/coordinator approval (requires_approval = True,
      workflow_status = 'RequiresApproval'). Otherwise 'Approved'.
    - Formulates user-facing ai_reply_message with detailed breakdown.
    - Appends execution trace to agent_traces.
    """
    t0 = time.time()
    traces = list(state.get("agent_traces") or [])

    print("\n" + "-" * 80)
    print("[AGENT 4 - SAFETY AGENT]: Initiating deterministic math audit and policy gatekeeper evaluation...")
    logger.info("[AGENT 4 - SAFETY AGENT]: Initiating deterministic math audit and policy gatekeeper evaluation...")

    line_items: List[Dict[str, Any]] = list(state.get("line_items") or [])
    state_estimate = float(state.get("total_estimate") or 0.0)

    # ── 1. Deterministic Math Audit ───────────────────────────────────────────
    computed_sum = 0.0
    for item in line_items:
        amount = float(item.get("amount_lkr") or 0.0)
        computed_sum += amount

    computed_sum = round(computed_sum, 2)
    
    # If state_estimate is 0 but we have computed sum, use computed sum
    if state_estimate <= 0.0 and computed_sum > 0.0:
        total_estimate = computed_sum
    elif abs(state_estimate - computed_sum) > 1.0 and computed_sum > 0.0:
        logger.warning(
            f"[AGENT 4 - SAFETY AGENT]: Math audit mismatch detected. State estimate: {state_estimate}, "
            f"Line items sum: {computed_sum}. Using audited line items sum."
        )
        total_estimate = computed_sum
    else:
        total_estimate = round(state_estimate if state_estimate > 0.0 else computed_sum, 2)

    math_audit_passed = abs(total_estimate - computed_sum) <= 1.0 or (len(line_items) == 0 and total_estimate >= 0.0)

    # ── 2. Gatekeeper Approval Policy ────────────────────────────────────────
    requires_approval = bool(total_estimate > APPROVAL_THRESHOLD_LKR)
    workflow_status = "RequiresApproval" if requires_approval else "Approved"

    location = state.get("location") or "Sri Lanka"
    guest_count = state.get("guest_count") or 100
    requested_category = state.get("requested_category")
    selected_venue = state.get("selected_venue_name") or "Selected Venue"
    recommended_vendors = state.get("recommended_vendors") or []

    print(
        f"[AGENT 4 - SAFETY AGENT]: Math Audit: {'PASSED' if math_audit_passed else 'RECONCILED'}. "
        f"Total Estimate: LKR {total_estimate:,.2f} across {len(line_items)} line items."
    )
    print(
        f"[AGENT 4 - SAFETY AGENT]: Policy Gatekeeper Check: Threshold=LKR {APPROVAL_THRESHOLD_LKR:,.2f} -> "
        f"requires_approval={requires_approval}, status='{workflow_status}'."
    )
    logger.info(
        f"[AGENT 4 - SAFETY AGENT]: Evaluated total estimate LKR {total_estimate:,.2f}. "
        f"RequiresApproval={requires_approval}, Status={workflow_status}."
    )

    # ── 3. Conversational AI Reply Formulation ───────────────────────────────
    if requested_category:
        cat_title = requested_category.replace("_", " ").title()
        reply_lines = [
            f"Here are the top-rated recommendations for **{cat_title}** in **{location}** (Guest count: {guest_count}):\n"
        ]
        if recommended_vendors:
            reply_lines.append(f"We found **{len(recommended_vendors)}** matching vendor(s) tailored to your preferences:")
            for v in recommended_vendors[:5]:
                v_name = v.get("name") or v.get("title") or "Vendor"
                v_price = v.get("price") or v.get("base_price") or v.get("pricing")
                price_str = f" - LKR {v_price:,.2f}" if isinstance(v_price, (int, float)) else ""
                v_loc = v.get("location") or location
                reply_lines.append(f"• **{v_name}** ({v_loc}){price_str}")
            reply_lines.append("")
        
        reply_lines.append(f"**Total Estimate for {cat_title}:** LKR {total_estimate:,.2f}")
    else:
        reply_lines = [
            f"We have prepared a comprehensive wedding plan for **{guest_count} guests** in **{location}**!\n",
            f"**Recommended Primary Venue:** {selected_venue}\n",
            "**Budget & Service Allocation Breakdown:**"
        ]
        for item in line_items:
            cat = item.get("category", "Service")
            amt = float(item.get("amount_lkr") or 0.0)
            desc = item.get("description", "")
            desc_text = f" ({desc})" if desc else ""
            reply_lines.append(f"• **{cat}**: LKR {amt:,.2f}{desc_text}")

        reply_lines.append(f"\n**Total Estimated Investment:** **LKR {total_estimate:,.2f}**")

    if requires_approval:
        reply_lines.append(
            "\n*Note: Because this estimate exceeds the automated threshold of LKR 100,000.00, "
            "it has been flagged for human wedding coordinator verification and approval.*"
        )
    else:
        reply_lines.append(
            "\n*Note: This estimate falls within automatic pre-approval limits and is ready for booking.*"
        )

    ai_reply_message = "\n".join(reply_lines)

    # ── 4. Telemetry and Trace Recording ─────────────────────────────────────
    execution_time_ms = round((time.time() - t0) * 1000, 2)
    trace = {
        "step_name": "Node 4: Safety & Policy Gatekeeper Agent",
        "status": "SUCCESS",
        "execution_time_ms": execution_time_ms,
        "output": {
            "audited_line_items_count": len(line_items),
            "audited_total_estimate_lkr": total_estimate,
            "math_audit_passed": math_audit_passed,
            "requires_approval": requires_approval,
            "approval_threshold_lkr": APPROVAL_THRESHOLD_LKR,
            "workflow_status": workflow_status,
            "policy_rule": "Deterministic Math Audit & Gatekeeper Policy (>100k LKR)"
        }
    }
    traces.append(trace)

    print("[AGENT 4 - SAFETY AGENT]: Safety audit and policy gatekeeper execution completed.")
    logger.info("[AGENT 4 - SAFETY AGENT]: Safety audit completed successfully.")

    return {
        "total_estimate": total_estimate,
        "requires_approval": requires_approval,
        "workflow_status": workflow_status,
        "ai_reply_message": ai_reply_message,
        "confidence_score": 1.0 if math_audit_passed else 0.95,
        "agent_traces": traces
    }
