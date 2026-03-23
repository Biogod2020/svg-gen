# Technology Stack

## Core Language & Runtime
- **Language**: Python 3.x
- **Runtime**: CPython

## Frameworks & Orchestration
- **API Framework**: FastAPI (for high-performance asynchronous web interfaces)
- **Server**: Uvicorn (ASGI server)
- **Agent Orchestration**: LangGraph (for building stateful, multi-actor applications with LLMs)

## Key Libraries & Utilities
- **Data Validation**: Pydantic v2 (for type safety and schema definition)
- **HTTP Client**: Requests (for API interactions)
- **Parsing & Scraping**: BeautifulSoup4, LXML (for SVG/XML manipulation and auditing)
- **CLI & UI**: Rich (for beautiful terminal output and status updates)
- **Environment**: Python-dotenv (for configuration management)
- **Patching**: Diff-match-patch (for efficient code/SVG modification)

## Infrastructure & External Services
- **LLM Provider**: Google Gemini API (via custom `gemini_client.py`)
- **Rendering/Conversion**: Playwright or CairoSVG (implied for visual auditing/rendering)

## Architecture
- **Pattern**: Modular Agent-based (Generative AI loop: Generate -> Audit -> Repair)
- **Strategy**: Asynchronous, state-driven workflow using LangGraph
