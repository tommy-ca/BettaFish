from typing import Any, Dict, Optional
from ..state import ForumState, AgentOutput
from langchain_core.messages import HumanMessage, AIMessage

class BaseGraphNode:
    """
    Base class for all Graph Nodes.
    Provides common helpers for State access and output formatting.
    """
    
    def __init__(self, name: str):
        self.name = name

    def _create_output(self, summary: str, data: Dict[str, Any] = None, artifacts: List[str] = None) -> Dict[str, Any]:
        """
        Helper to create a standard AgentOutput update for the state.
        Note: We return a dict that matches the partial structure of ForumState
        to be merged by LangGraph.
        """
        output: AgentOutput = {
            "agent_name": self.name,
            "summary": summary,
            "data": data or {},
            "artifacts": artifacts or []
        }
        
        # We also append a message to the conversation history
        message = AIMessage(content=f"[{self.name}] {summary}", name=self.name)
        
        return {
            "research_findings": {self.name: [output]},
            "messages": [message]
        }
        
    async def run(self, state: ForumState) -> Dict[str, Any]:
        """
        Main entry point for the node.
        Must be implemented by subclasses.
        """
        raise NotImplementedError
