# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Commands

**Install dependencies:**
```bash
uv sync
```

**Run the application:**
```bash
./run.sh
# OR manually:
cd backend && uv run uvicorn app:app --reload --port 8000
```

**Environment setup:**
Create `.env` file in root:
```
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

## Development Guidelines

- Use `uv` to run python files and to manage all dependencies, never use pip directly or just python

## Architecture Overview

This is a **Retrieval-Augmented Generation (RAG) system** for course materials with AI-powered semantic search. The system uses a **tool-based approach** where Claude decides autonomously when to search vs. provide direct answers.

### Core Flow Architecture

**Query Processing Pipeline:**
1. **Frontend** (script.js) → POST `/api/query` 
2. **FastAPI** (app.py) → Session management + RAG orchestration
3. **RAG System** (rag_system.py) → Coordinates AI + search tools
4. **AI Generator** (ai_generator.py) → Claude API with tool calling
5. **Search Tools** (search_tools.py) → Tool execution interface
6. **Vector Store** (vector_store.py) → ChromaDB semantic search
7. **Response** → Sources tracked and returned to frontend

### Key Components

**Document Processing Pipeline:**
- `document_processor.py` - Parses course files with metadata extraction and sentence-based chunking
- Expected format: `Course Title:`, `Course Link:`, `Course Instructor:`, followed by `Lesson N:` sections
- Creates contextual chunks: `"Course [title] Lesson [N] content: [chunk]"`

**Vector Storage Architecture:**
- **Two ChromaDB collections**: `course_catalog` (metadata) + `course_content` (chunks)
- **SentenceTransformers** embeddings (configurable model in config.py)
- **Smart course resolution**: Fuzzy matching on course names via vector search

**AI Tool System:**
- `search_tools.py` implements extensible **Tool interface**
- `CourseSearchTool` provides semantic search with course/lesson filtering
- **Tool Manager** handles registration, execution, and source tracking
- AI system prompt optimized for educational content with tool usage guidelines

**Session Management:**
- Conversation history preserved across queries
- Session-scoped context for multi-turn conversations
- Configurable history limits in config.py

### Configuration

All settings in `backend/config.py`:
- **Chunking**: 800 chars with 100 char overlap
- **Search**: Max 5 results per query
- **History**: 2 conversation messages retained
- **Models**: Claude Sonnet 4, all-MiniLM-L6-v2 embeddings

### Data Flow

**Startup**: Automatically processes `docs/*.txt` files into vector store
**Query**: Claude autonomously chooses direct answer vs. tool-based search
**Search**: Semantic similarity + metadata filtering (course/lesson)
**Response**: Sources tracked from tool calls and displayed in frontend

### Frontend Integration

- **Real-time UI**: Loading states, progressive response display
- **Source attribution**: Collapsible sources from ChromaDB metadata
- **Session continuity**: Automatic session creation and management

### Vector Database Details

- **Two collections in the vector database**:
  - `course_catalog`: 
    - Stores course titles for name resolution
    - Metadata for each course includes:
      - title
      - instructor
      - course_link
      - lesson_count
      - lessons_json (list of lessons with lesson_number, lesson_title, lesson_link)
  - `course_content`:
    - Stores text chunks for semantic search
    - Metadata for each chunk includes:
      - course_title
      - lesson_number
      - chunk_index