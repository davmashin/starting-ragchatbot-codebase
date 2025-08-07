"""Mock data and utilities for testing"""

# Sample course content chunks
SAMPLE_COURSE_CHUNKS = [
    {
        "content": "The Model Context Protocol (MCP) is a new standard for connecting AI assistants to external data sources and tools.",
        "metadata": {"course_title": "MCP: Build Rich-Context AI Apps with Anthropic", "lesson_number": 0, "chunk_index": 0}
    },
    {
        "content": "MCP enables AI applications to securely access databases, APIs, and other resources through a standardized interface.",
        "metadata": {"course_title": "MCP: Build Rich-Context AI Apps with Anthropic", "lesson_number": 1, "chunk_index": 1}
    },
    {
        "content": "Vector databases like Chroma enable semantic search by storing embeddings that represent the meaning of text.",
        "metadata": {"course_title": "Advanced Retrieval for AI with Chroma", "lesson_number": 1, "chunk_index": 0}
    }
]

# Sample course metadata
SAMPLE_COURSE_METADATA = {
    "title": "MCP: Build Rich-Context AI Apps with Anthropic",
    "instructor": "DeepLearning.AI",
    "course_link": "https://learn.deeplearning.ai/courses/mcp-build-rich-context-ai-apps-with-anthropic",
    "lesson_count": 8,
    "lessons_json": '[{"lesson_number": 0, "lesson_title": "Introduction", "lesson_link": "https://example.com/lesson0"}]'
}

# Test parameters for different scenarios
TEST_PARAMETERS = {
    "valid_kwargs": {
        "query": "What is MCP?",
        "course_name": "MCP", 
        "lesson_number": 1
    },
    "query_only": {
        "query": "What is machine learning?"
    },
    "missing_query": {
        "course_name": "MCP",
        "lesson_number": 1
    },
    "empty_query": {
        "query": ""
    }
}

# Expected tool definitions
EXPECTED_SEARCH_TOOL_DEF = {
    "name": "search_course_content",
    "description": "Search course materials with smart course name matching and lesson filtering",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "What to search for in the course content"},
            "course_name": {"type": "string", "description": "Course title (partial matches work, e.g. 'MCP', 'Introduction')"},
            "lesson_number": {"type": "integer", "description": "Specific lesson number to search within (e.g. 1, 2, 3)"}
        },
        "required": ["query"]
    }
}