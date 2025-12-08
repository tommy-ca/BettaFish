from typing import Any, Dict, List
from .base_node import BaseGraphNode
from ...state import ForumState
# Assuming MediaEngine has a similar structure. 
# Based on file listing, MediaEngine/agent.py exists.
# We will use dynamic import or assume the structure matches QueryEngine for now
# as we can't read every file. But standardizing is key.
from MediaEngine.agent import DeepSearchAgent as MediaDeepSearchAgent
from MediaEngine.utils.config import Settings as MediaSettings
import asyncio
from loguru import logger

class MediaAgentNode(BaseGraphNode):
    """
    Wraps the MediaEngine (and implicitly MindSpider via tools) into a Graph Node.
    """
    
    def __init__(self):
        super().__init__(name="MediaEngine")
        self.settings = MediaSettings()
        self.agent = MediaDeepSearchAgent(config=self.settings)

    async def run(self, state: ForumState) -> Dict[str, Any]:
        query = state["user_query"]
        logger.info(f"MediaAgentNode received query: {query}")
        
        try:
            # Execute MediaEngine research
            # Note: MediaEngine might need specific 'platforms' or mode config
            # For now we run the default research flow
            report_content = await asyncio.to_thread(self.agent.research, query, save_report=False)
            
            structured_data = {
                "paragraphs": [p.to_dict() for p in self.agent.state.paragraphs] if hasattr(self.agent, "state") else {},
                "final_report": report_content
            }
            
            summary = f"Completed media analysis on '{query}'."
            
            return self._create_output(
                summary=summary,
                data=structured_data
            )
            
        except Exception as e:
            logger.error(f"MediaAgentNode failed: {e}")
            return self._create_output(
                summary=f"Failed to execute media analysis: {str(e)}",
                data={"error": str(e)}
            )
