# Technology Stack

## Core Technologies
- **Programming Language**: Python 3.x
- **Frameworks**:
    - **FastAPI**: For the API layer.
    - **Uvicorn**: As the ASGI server.
    - **LangGraph**: For the agent orchestration and state management.

## Primary Libraries
- **Data Validation**: Pydantic v2
- **Network Requests**: Requests
- **Parsing/Scraping**: BeautifulSoup4, LXML
- **CLI/Formatting**: Rich
- **Environment Management**: Python-dotenv
- **Patching**: Diff-match-patch

## Infrastructure & APIs
- **LLM Provider**: Google Gemini API (via custom client in `src/core/gemini_client.py`)
- **Asset Processing**: Playwright / CairoSVG (for SVG rendering and conversion)

## Architecture
- **Type**: Modular Agent-based (Generative AI loop)
- **Pattern**: Generate-Audit-Repair loop utilizing Vision-Language Models (VLM) for visual quality audits.
