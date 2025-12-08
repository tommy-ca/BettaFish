from langgraph.graph import StateGraph, END
from .state import ForumState
from .nodes.supervisor import SupervisorNode
from .nodes.query_agent import QueryAgentNode
from .nodes.media_agent import MediaAgentNode
from .nodes.insight_agent import InsightAgentNode
# We reuse ReportAgentNode logic or wrap it similarly.
# For Phase 1, if ReportEngine isn't wrapped yet, we can mock it or wrap it now.
# The plan listed "Report Agent Node" as Phase 5, but the graph needs a valid node.
# We will create a simple placeholder wrapper for ReportEngine to complete the graph.
from ReportEngine.agent import ReportAgent # Assuming this exists
from ReportEngine.flask_interface import ReportTask # Just for type checking if needed

# We need a simple ReportAgentNode to close the loop
from .nodes.base_node import BaseGraphNode
from typing import Dict, Any

class ReportAgentNode(BaseGraphNode):
    def __init__(self):
        super().__init__(name="ReportEngine")
        # In a real impl, we'd init ReportAgent
    
    async def run(self, state: ForumState) -> Dict[str, Any]:
        # Placeholder for Phase 1
        summary = "Report generation triggered (Placeholder)."
        return self._create_output(summary=summary)

def create_graph():
    """
    Constructs and compiles the BettaFish Forum Graph.
    """
    workflow = StateGraph(ForumState)

    # Initialize Nodes
    supervisor = SupervisorNode()
    query_agent = QueryAgentNode()
    media_agent = MediaAgentNode()
    insight_agent = InsightAgentNode()
    report_agent = ReportAgentNode()

    # Add Nodes
    workflow.add_node("supervisor", supervisor.run)
    workflow.add_node("query_agent", query_agent.run)
    workflow.add_node("media_agent", media_agent.run)
    workflow.add_node("insight_agent", insight_agent.run)
    workflow.add_node("report_agent", report_agent.run)

    # Set Entry Point
    workflow.set_entry_point("supervisor")

    # Define Conditional Edges from Supervisor
    workflow.add_conditional_edges(
        "supervisor",
        lambda state: state["next_speaker"],
        {
            "QueryEngine": "query_agent",
            "MediaEngine": "media_agent",
            "InsightEngine": "insight_agent",
            "ReportEngine": "report_agent",
            "FINISH": END
        }
    )

    # Define Edges back to Supervisor
    workflow.add_edge("query_agent", "supervisor")
    workflow.add_edge("media_agent", "supervisor")
    workflow.add_edge("insight_agent", "supervisor")
    
    # ReportEngine ends the flow
    workflow.add_edge("report_agent", END)

    # Compile
    app = workflow.compile()
    return app
