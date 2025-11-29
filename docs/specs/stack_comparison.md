# Stack Comparison: LangGraph vs. Claude Agent SDK

## Executive Summary
We are evaluating two modern stacks for the BettaFish agent system. Both use **Hatchet** for durable workflow orchestration but differ in the **Agent Framework**.

| Feature | **Stack A: LangGraph + Hatchet** | **Stack B: Claude Agent SDK + Hatchet** |
| :--- | :--- | :--- |
| **Core Philosophy** | **Graph-based State Machine**. Explicit control over every transition and state update. | **Agentic Swarm**. LLM-driven reasoning loop with native tool calling and sub-agents. |
| **Control Level** | **High**. You define the exact edges and nodes. | **Medium**. You define tools and goals; Claude decides the steps. |
| **Complexity** | **High**. Requires defining state schemas, nodes, and conditional edges. | **Low**. "Give me a task and tools, I'll figure it out." |
| **Flexibility** | **High**. Model-agnostic (Works with OpenAI, Anthropic, Llama, etc.). | **Low**. Tightly coupled with Anthropic's Claude models. |
| **Best For...** | Complex, deterministic business logic where you need strict control over the process. | Open-ended research and tasks requiring high-level reasoning and autonomy. |

## Detailed Analysis

### 1. LangGraph + Hatchet
**"The Structured Engineer's Choice"**

*   **Architecture**:
    *   **LangGraph**: Manages the *internal* conversation loop (StateGraph). It handles the "micro-orchestration" of the debate.
    *   **Hatchet**: Manages the *external* execution (scheduling, retries, durability). It triggers the LangGraph run.
*   **Pros**:
    *   **Model Agnostic**: Can switch between GPT-4o, Claude 3.5, or local Llama 3 models easily.
    *   **Explicit State**: The `ForumState` schema makes the data flow crystal clear.
    *   **Control**: You can force specific paths (e.g., "Always critique before searching").
*   **Cons**:
    *   **Boilerplate**: Requires writing significant code for nodes, edges, and state management.
    *   **Cognitive Load**: You must mentally model the entire graph.

### 2. Claude Agent SDK + Hatchet
**"The AI Native Choice"**

*   **Architecture**:
    *   **Claude SDK**: Manages the agent's "brain". It handles context, tool calling, and sub-agent delegation automatically.
    *   **Hatchet**: Wraps the agent execution to ensure it finishes (durable execution).
*   **Pros**:
    *   **Development Speed**: Extremely fast to set up. Just define tools and a prompt.
    *   **Native Capabilities**: Leverages Claude's specific training for tool use and agentic behaviors.
    *   **Context Management**: Built-in handling of token limits and history.
*   **Cons**:
    *   **Vendor Lock-in**: strictly tied to Anthropic.
    *   **Opaque Logic**: Harder to debug *why* the agent took a specific path compared to a rigid graph.

## Recommendation

*   **Choose LangGraph** if:
    *   You need to support multiple LLM providers (e.g., local models for privacy).
    *   The "Forum" logic is very specific and rigid (e.g., strict regulatory compliance steps).
*   **Choose Claude Agent SDK** if:
    *   You are happy using Claude 3.5 Sonnet (currently SOTA for agents).
    *   You want to move fast and rely on the model's reasoning capabilities.
    *   The tasks are open-ended research (BettaFish's core use case).

**Verdict for BettaFish**: **Claude Agent SDK** is likely the better fit for "Deep Research" and "Social Sentiment" analysis, as these are open-ended tasks where Claude 3.5 excels. However, keeping **LangGraph** as an option is wise if model independence is a future requirement.
