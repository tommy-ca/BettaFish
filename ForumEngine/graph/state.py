from typing import TypedDict, List, Dict, Any, Annotated, Optional
from langchain_core.messages import BaseMessage
import operator

class AgentOutput(TypedDict):
    """Structured output from a specific agent's turn."""
    agent_name: str
    summary: str             # High-level summary of findings
    data: Dict[str, Any]     # Raw structured data (e.g., search results, crawl stats)
    artifacts: List[str]     # Paths to generated files (images, PDFs)

def merge_research_findings(left: Dict[str, List[AgentOutput]], right: Dict[str, List[AgentOutput]]) -> Dict[str, List[AgentOutput]]:
    """Merges research findings, appending new outputs to existing lists."""
    if not left:
        left = {}
    if not right:
        return left
        
    merged = left.copy()
    for key, value in right.items():
        if key in merged:
            merged[key] = merged[key] + value
        else:
            merged[key] = value
    return merged

class ForumState(TypedDict):
    """
    The shared state of the Forum Graph.
    Acts as the 'blackboard' where agents read history and write findings.
    """
    # --- Conversation History ---
    # The linear history of the "debate" for the LLM Supervisor to read.
    messages: Annotated[List[BaseMessage], operator.add]
    
    # --- Structured Knowledge Base ---
    # Aggregated findings from each engine, keyed by engine name (e.g. "QueryEngine", "MediaEngine").
    # Uses a custom merger to append lists rather than overwrite.
    research_findings: Annotated[Dict[str, List[AgentOutput]], merge_research_findings]
    
    # --- Control Flow ---
    user_query: str          # The original objective
    iteration_count: int     # To prevent infinite loops
    next_speaker: str        # Set by Supervisor to route to specific node
    
    # --- Metadata ---
    session_id: str
    timestamp: str
