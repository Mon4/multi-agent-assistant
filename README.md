# Advanced Autonomous Research Agent (AARA) — a multi-agent assistant built with Google ADK
This project implements an advanced, multi-agent autonomous research system built using the **Google Agent Development Kit (ADK)** and **Gemini 2.5 Flash/Pro**. 
It is designed to autonomously conduct research, synthesize information from multiple sources, and generate high-quality, professional documents.

AARA operates within an autonomous feedback loop, enabling agents to plan research objectives, gather and validate data, evaluate outputs, and iteratively refine results. Specialized agents collaborate to handle discovery, verification, synthesis, and document generation.

## System Architecture
The system follows a modular **"Plan-Execute-Critique-Refine"** architecture. It leverages a root orchestrator to manage specialized sub-agents and tools.

### Core Agents & Components:

**Root Agent** (Orchestrator): The brain of the system. It handles high-level planning, delegates tasks to specialized agents, and manages the state of the research loop.

**Finance Agent** (MCP Integration): Retrieves structured, real-time data for stocks, crypto, and currencies. It interfaces with an MCP (Model Context Protocol) server to fetch data from verified financial sources like Yahoo Finance.

**Web Agent**: Performs broad internet searches to gather public information and real-time news.

**RAG Agent**: Utilizes FAISS for in-memory vector search to query private, local knowledge bases.

**Critique Agent**: Acts as the quality gate. It evaluates the logic and completeness of the synthesized answer, providing actionable feedback for the next iteration.

## How It Works

The manager operates in an autonomous **Research → Critique → Refine** loop (max. 3 iterations):

```mermaid
flowchart TD
    U[User Query] --> M[Root Agent - Manager]
    M --> W[Web Agent]
    M --> F[Finance Agent - MCP]
    M --> R[RAG Agent - FAISS]
    W --> S[Synthesis]
    F --> S
    R --> S
    S --> C{Critique Agent}
    C -- "STATUS: APPROVED" --> O[Final Answer / Canvas Tool]
    C -- "STATUS: NEEDS_REVISION" --> M
```

## Key Features & Phases
### 1. Multi-Source Synthesis
The agent intelligently switches between local documents (RAG), live web data, and structured financial feeds. The Synthesizer component resolves conflicts between these sources to produce a unified response.

The Financial Agent has access to both cryptocurrencies and  currencies. However, it does not have direct access to the price of cryptocurrencies in every currency, so it is used twice. First, it gets the Bitcoin price in USD and then converts it to Euros. In the end, the critic accepts the generated answer.
![finance](images/finance.png)

### 2. Autonomous Refinement Loop

Unlike linear RAG systems, this agent features a self-critique loop.

- **Plan**: Identify necessary information.
- **Execute**: Gather data via sub-agents.
- **Critique**: The critique_agent identifies gaps or logic errors.
- **Refine**: If the quality threshold isn't met, the agent loops back to the planning phase to fill gaps.


First, an agent searches for historical information on the internet. Then, the critic agent checks if the agent correctly answered the user's question.

![critic](images/critic.png)

### 3. Canvas Tool (Output Generation)
The Canvas Tool handles the final presentation layer. It transforms raw research data into professional Markdown reports, HTML documents, or validated code snippets using structured templates.

Code formatting:

![code](images/code.png)

Markdown formatting:

![markdown](images/plan.png)

## Example Prompts

Try these in the ADK Web UI (`adk web`):

| Area | Example prompt |
|---|---|
| Finance (MCP) | `What is the current Bitcoin price in EUR?` |
| Web search | `What are the latest AI news?` |
| RAG (local PDF) | `What does Mercutio say about Queen Mab?` |
| Canvas (report) | `Prepare a markdown report comparing BTC and ETH prices` |

## Prerequisites

- Python 3.10+
- Docker Desktop (for the MCP fetch server)
- Google account: Gemini API key ([AI Studio](https://aistudio.google.com/apikey)) and/or GCP project with Vertex AI enabled
- (Optional) [Langfuse](https://cloud.langfuse.com) account for observability

## Installation & Setup
1. Clone the repository:

```Bash
git clone https://github.com/Mon4/multi-agent-assistant.git
cd multi-agent-assistant
```
2. Create virtual environment and install dependencies from `requirements.txt`

3. Set up Environment Variables: Copy `.env.example` to `.env` and fill in your credentials (Google API key, GCP project, optional Langfuse keys).
   
```
GCP_PROJECT_ID=[PROJECT_NAME]
GCP_LOCATION=[LOCATION]
```

4. Run the MCP Server (Docker):
   
```Bash
docker pull mcp/fetch-server
docker run -p 8080:8080 mcp/fetch-server
```

5. Launch the ADK Web Interface
   
```
adk web
```

## Project Structure

```
multi-agent-assistant/
├── personal_assistant/               # ADK agent package (manager + sub-agents)
│   └── agent.py                      # Root orchestrator and agent definitions
├── tools/
│   ├── financial.py                  # MCP fetch-server bridge (Yahoo Finance data)
│   ├── canvas.py                     # Report/code rendering (Jinja2 + Markdown)
│   └── rag/                          # RAG pipeline
│       ├── rag.py                    # Hybrid search: FAISS + BM25 + RRF + reranking
│       ├── vector_store_manager.py   # FAISS index build & load
│       ├── pdf_to_docs.py            # PDF parsing & chunking
│       └── search_knowledge_base.py  # Tool exposed to the RAG agent
├── templates/
│   └── canvas_base.html              # Canvas output template
├── data/
│   └── romeo-and-juliet.pdf          # Knowledge base document
├── images/                           # README screenshots
├── requirement.txt                   # Python dependencies
└── .env.example                      # Environment variables template
```
