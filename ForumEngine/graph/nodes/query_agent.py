from typing import Any, Dict, List
from .base_node import BaseGraphNode
from ...state import ForumState
from QueryEngine.agent import DeepSearchAgent
from QueryEngine.utils.config import Settings
import asyncio
from loguru import logger

class QueryAgentNode(BaseGraphNode):
    """
    Wraps the legacy QueryEngine logic into a Graph Node.
    """
    
    def __init__(self):
        super().__init__(name="QueryEngine")
        # Initialize the legacy agent
        # We might need to adjust config to not use Streamlit-specific settings if any
        self.settings = Settings()
        self.agent = DeepSearchAgent(config=self.settings)

    async def run(self, state: ForumState) -> Dict[str, Any]:
        """
        Executes the DeepSearchAgent logic.
        
        Current Implementation Note:
        The legacy `DeepSearchAgent.research` is synchronous and heavy.
        In a real Hatchet worker, this should be offloaded or fine.
        For now, we run it in a thread executor to avoid blocking the async event loop if needed,
        though Hatchet workers are typically process-based so direct call is also okay.
        We will call it directly for simplicity in Phase 1.
        """
        query = state["user_query"]
        logger.info(f"QueryAgentNode received query: {query}")
        
        try:
            # We assume the agent performs the research and returns a report string
            # The legacy `research` method returns the final report markdown.
            # However, `research` also updates internal state which contains structured data.
            
            # Since `research` saves files by default, we might want to disable that
            # or capture the output. For now, we let it run as designed.
            report_content = await asyncio.to_thread(self.agent.research, query, save_report=False)
            
            # Extract structured data from the agent's internal state
            # The legacy agent stores paragraphs and search results in `self.agent.state`
            structured_data = {
                "paragraphs": [p.to_dict() for p in self.agent.state.paragraphs],
                "final_report": self.agent.state.final_report
            }
            
            summary = f"Completed deep research on '{query}'. generated {len(self.agent.state.paragraphs)} paragraphs."
            
            return self._create_output(
                summary=summary,
                data=structured_data,
                artifacts=[] # We could add paths if we enabled file saving
            )
            
        except Exception as e:
            logger.error(f"QueryAgentNode failed: {e}")
            return self._create_output(
                summary=f"Failed to execute research: {str(e)}",
                data={"error": str(e)}
            )
