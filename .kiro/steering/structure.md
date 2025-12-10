# System Structure
- **Core Directories**:
  - `InsightEngine/`, `MediaEngine/`, `QueryEngine/`, `ReportEngine/`, `ForumEngine/`: Core agent logic.
  - `MindSpider/`: Data crawling subsystem.
  - `logs/`: Legacy communication medium.
- **New Structure (Target)**:
  - `src/agents/`: LangGraph nodes
  - `src/workflows/`: Hatchet workflows
  - `src/state/`: Typed state definitions
