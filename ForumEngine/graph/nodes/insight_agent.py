from typing import Any, Dict, List
from .base_node import BaseGraphNode
from ...state import ForumState
from InsightEngine.agent import DeepSearchAgent as InsightDeepSearchAgent
from InsightEngine.utils.config import Settings as InsightSettings
import asyncio
from loguru import logger

class InsightAgentNode(BaseGraphNode):
    """
    Wraps the InsightEngine (Private DB mining) into a Graph Node.
    """
    
    def __init__(self):
        super().__init__(name="InsightEngine")
        self.settings = InsightSettings()
        self.agent = InsightDeepSearchAgent(config=self.settings)

    async def run(self, state: ForumState) -> Dict[str, Any]:
        query = state["user_query"]
        logger.info(f"InsightAgentNode received query: {query}")
        
        try:
            # Execute InsightEngine research
            # Typically looks for internal DB records matching the query
            report_content = await asyncio.to_thread(self.agent.research, query, save_report=False)
            
            structured_data = {
                "paragraphs": [p.to_dict() for p in self.agent.state.paragraphs] if hasattr(self.agent, "state") else {},
                "final_report": report_content
            }
            
            summary = f"Completed internal insight analysis on '{query}'."
            
            return self._create_output(
                summary=summary,
                data=structured_data
            )
            
        except Exception as e:
            logger.error(f"InsightAgentNode failed: {e}")
            return self._create_output(
                summary=f"Failed to execute insight analysis: {str(e)}",
                data={"error": str(e)}
            )
