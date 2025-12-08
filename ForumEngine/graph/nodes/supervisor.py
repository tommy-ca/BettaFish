from typing import Any, Dict, List, Literal, TypedDict
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from .base_node import BaseGraphNode
from ...state import ForumState
from loguru import logger
import os
import json

class SupervisorOutput(TypedDict):
    next_speaker: Literal["QueryEngine", "MediaEngine", "InsightEngine", "ReportEngine", "FINISH"]
    reasoning: str

class SupervisorNode(BaseGraphNode):
    """
    The Host/Router of the Forum.
    Decides which agent should speak next based on conversation history.
    """
    
    def __init__(self):
        super().__init__(name="Supervisor")
        # We use a smart model for routing. 
        # Ideally configured via Settings, but for now we default to environment
        self.llm = ChatOpenAI(
            api_key=os.getenv("FORUM_HOST_API_KEY") or os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("FORUM_HOST_BASE_URL"),
            model=os.getenv("FORUM_HOST_MODEL_NAME", "gpt-4-turbo"),
            temperature=0
        )
        self.MAX_ITERATIONS = 5

    async def run(self, state: ForumState) -> Dict[str, Any]:
        """
        Analyzes the state and routes to the next agent.
        """
        messages = state["messages"]
        user_query = state["user_query"]
        iteration_count = state.get("iteration_count", 0)
        
        logger.info(f"Supervisor evaluating state. Iteration: {iteration_count}")

        # Force termination if max iterations reached
        if iteration_count >= self.MAX_ITERATIONS:
            logger.warning("Max iterations reached. Forcing report generation.")
            return {"next_speaker": "ReportEngine", "iteration_count": iteration_count + 1}
        
        # Construct prompt for the Router
        system_prompt = (
            "You are the Supervisor of a multi-agent research forum. "
            "Your goal is to coordinate agents to fully answer the user's query.\n"
            "The available agents are:\n"
            "- QueryEngine: Searches the web for news and general information.\n"
            "- MediaEngine: Analyzes social media sentiment and specific platforms (Weibo, XHS).\n"
            "- InsightEngine: Searches internal databases for historical context.\n"
            "- ReportEngine: Compiles the final report (select this when research is sufficient).\n\n"
            "Review the conversation history. If the query is new, usually start with QueryEngine or InsightEngine. "
            "If information is missing, call the relevant agent. "
            "If sufficient information has been gathered to answer the query comprehensively, route to ReportEngine. "
            "Return a JSON object with 'next_speaker' and 'reasoning'."
        )
        
        # We only pass recent history to save tokens/confusion if long
        # But for global context, we might need summaries. 
        # For Phase 1, we pass the full message list (it's list of BaseMessage) 
        
        try:
            structured_llm = self.llm.with_structured_output(SupervisorOutput)
            response = await structured_llm.ainvoke(
                [SystemMessage(content=system_prompt)] + messages + [HumanMessage(content=f"Current Objective: {user_query}")]
            )
            
            logger.info(f"Supervisor decision: {response['next_speaker']} ({response['reasoning']})")
            
            return {
                "next_speaker": response["next_speaker"],
                "iteration_count": iteration_count + 1
            }
            
        except Exception as e:
            logger.error(f"Supervisor failed to route: {e}. Defaulting to ReportEngine.")
            return {
                "next_speaker": "ReportEngine",
                "iteration_count": iteration_count + 1
            }
