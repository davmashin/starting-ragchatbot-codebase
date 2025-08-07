"""Pytest configuration and shared fixtures for RAG system tests"""
import pytest
import sys
import os
from unittest.mock import MagicMock, Mock
from typing import Dict, Any, List

# Add backend to path for imports
backend_path = os.path.dirname(os.path.abspath(__file__)).replace('tests', '')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

@pytest.fixture
def mock_vector_store():
    """Mock VectorStore for testing"""
    mock_store = MagicMock()
    
    # Mock successful search results
    from vector_store import SearchResults
    
    mock_search_results = SearchResults(
        documents=["MCP is the Model Context Protocol for connecting AI assistants to external data sources."],
        metadata=[{"course_title": "MCP Course", "lesson_number": 1, "chunk_index": 0}],
        distances=[0.5]
    )
    mock_store.search.return_value = mock_search_results
    
    # Mock course name resolution
    mock_store._resolve_course_name.return_value = "MCP Course"
    
    return mock_store

@pytest.fixture 
def sample_search_results():
    """Sample search results for testing"""
    from vector_store import SearchResults
    
    return SearchResults(
        documents=[
            "MCP is the Model Context Protocol for connecting AI assistants to external data sources.",
            "The protocol enables secure access to databases, APIs, and other resources."
        ],
        metadata=[
            {"course_title": "MCP Course", "lesson_number": 1, "chunk_index": 0},
            {"course_title": "MCP Course", "lesson_number": 2, "chunk_index": 1}
        ],
        distances=[0.5, 0.6]
    )

@pytest.fixture
def empty_search_results():
    """Empty search results for testing"""
    from vector_store import SearchResults
    return SearchResults(documents=[], metadata=[], distances=[])

@pytest.fixture
def error_search_results():
    """Error search results for testing"""
    from vector_store import SearchResults
    return SearchResults.empty("Database connection failed")

@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client for testing"""
    mock_client = MagicMock()
    
    # Mock text-only response
    mock_text_response = MagicMock()
    mock_text_response.stop_reason = "stop"
    mock_text_block = MagicMock()
    mock_text_block.text = "This is a direct response without tool use."
    mock_text_response.content = [mock_text_block]
    
    # Mock tool use response
    mock_tool_response = MagicMock()
    mock_tool_response.stop_reason = "tool_use"
    mock_tool_block = MagicMock()
    mock_tool_block.type = "tool_use"
    mock_tool_block.name = "search_course_content"
    mock_tool_block.id = "tool_123"
    mock_tool_block.input = {"query": "What is MCP?"}
    mock_tool_response.content = [mock_tool_block]
    
    # Mock final response after tool use
    mock_final_response = MagicMock()
    mock_final_response.stop_reason = "stop"
    mock_final_text = MagicMock()
    mock_final_text.text = "Based on the search results, MCP is the Model Context Protocol."
    mock_final_response.content = [mock_final_text]
    
    mock_client.messages.create.side_effect = [mock_tool_response, mock_final_response]
    return mock_client

@pytest.fixture
def course_search_tool(mock_vector_store):
    """CourseSearchTool instance for testing"""
    from search_tools import CourseSearchTool
    return CourseSearchTool(mock_vector_store)

@pytest.fixture
def course_outline_tool(mock_vector_store):
    """CourseOutlineTool instance for testing"""  
    from search_tools import CourseOutlineTool
    return CourseOutlineTool(mock_vector_store)

@pytest.fixture
def tool_manager(course_search_tool, course_outline_tool):
    """ToolManager with registered tools"""
    from search_tools import ToolManager
    
    manager = ToolManager()
    manager.register_tool(course_search_tool)
    manager.register_tool(course_outline_tool)
    return manager

@pytest.fixture
def mock_config():
    """Mock configuration for RAG system"""
    class MockConfig:
        CHUNK_SIZE = 800
        CHUNK_OVERLAP = 100
        CHROMA_PATH = "./test_chroma"
        EMBEDDING_MODEL = "all-MiniLM-L6-v2"
        MAX_RESULTS = 5
        ANTHROPIC_API_KEY = "test_key"
        ANTHROPIC_MODEL = "claude-3-sonnet-20240229"
        MAX_HISTORY = 2
    
    return MockConfig()

@pytest.fixture
def test_queries():
    """Common test queries"""
    return {
        "content_query": "What is the Model Context Protocol?",
        "outline_query": "What is the outline of the MCP course?", 
        "specific_lesson": "What is covered in lesson 1 of the MCP course?",
        "general_knowledge": "What is machine learning?",
        "invalid_query": ""
    }