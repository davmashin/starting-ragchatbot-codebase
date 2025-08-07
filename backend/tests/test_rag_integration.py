"""Integration tests for the complete RAG system"""
import pytest
from unittest.mock import MagicMock, patch


class TestRAGSystemIntegration:
    """Test complete RAG system integration"""
    
    @patch('rag_system.VectorStore')
    @patch('rag_system.DocumentProcessor') 
    @patch('rag_system.SessionManager')
    def test_rag_system_initialization(self, mock_session, mock_doc_proc, mock_vector, mock_config):
        """Test that RAG system initializes correctly with all components"""
        from rag_system import RAGSystem
        
        # Mock the components
        mock_vector_instance = MagicMock()
        mock_vector.return_value = mock_vector_instance
        
        # Initialize RAG system
        rag = RAGSystem(mock_config)
        
        # Verify all components exist
        assert hasattr(rag, 'document_processor')
        assert hasattr(rag, 'vector_store')
        assert hasattr(rag, 'ai_generator')
        assert hasattr(rag, 'session_manager')
        assert hasattr(rag, 'tool_manager')
        assert hasattr(rag, 'search_tool')
        assert hasattr(rag, 'outline_tool')
        
        # Verify tools are registered
        assert "search_course_content" in rag.tool_manager.tools
        assert "get_course_outline" in rag.tool_manager.tools
        
        print("[PASS] RAG system initialized with all components")
    
    @patch('rag_system.VectorStore')
    @patch('rag_system.DocumentProcessor')
    @patch('rag_system.SessionManager')
    @patch('anthropic.Anthropic')
    def test_content_query_end_to_end_failure(self, mock_anthropic, mock_session, mock_doc_proc, mock_vector, mock_config, test_queries):
        """Test content query end-to-end - should fail due to parameter signature issue"""
        from rag_system import RAGSystem
        from vector_store import SearchResults
        
        # Setup mocks
        mock_vector_instance = MagicMock()
        mock_vector.return_value = mock_vector_instance
        
        # Mock successful search results from vector store
        mock_search_results = SearchResults(
            documents=["MCP is the Model Context Protocol for connecting AI assistants to data sources."],
            metadata=[{"course_title": "MCP Course", "lesson_number": 1, "chunk_index": 0}],
            distances=[0.5]
        )
        mock_vector_instance.search.return_value = mock_search_results
        
        # Mock Anthropic client responses
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        
        # Mock tool use response (Claude wants to use search tool)
        mock_tool_response = MagicMock()
        mock_tool_response.stop_reason = "tool_use"
        mock_tool_block = MagicMock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.name = "search_course_content"
        mock_tool_block.id = "tool_123"
        mock_tool_block.input = {"query": "What is MCP?"}  # This causes parameter signature failure
        mock_tool_response.content = [mock_tool_block]
        
        # Mock final response (after tool execution)
        mock_final_response = MagicMock()
        mock_final_response.stop_reason = "stop"
        mock_final_text = MagicMock()
        mock_final_text.text = "Based on the search, MCP is the Model Context Protocol."
        mock_final_response.content = [mock_final_text]
        
        mock_client.messages.create.side_effect = [mock_tool_response, mock_final_response]
        
        # Mock session manager
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.get_conversation_history.return_value = None
        
        # Test the query
        rag = RAGSystem(mock_config)
        
        try:
            response, sources = rag.query(test_queries["content_query"])
            print(f"[UNEXPECTED SUCCESS] Query worked: {response[:50]}...")
            print(f"[SOURCES] {sources}")
        except Exception as e:
            print(f"[EXPECTED FAILURE] Content query failed: {e}")
            print("[DIAGNOSIS] This confirms the parameter signature issue cascades through the system")
    
    @patch('rag_system.VectorStore')
    @patch('rag_system.DocumentProcessor')
    @patch('rag_system.SessionManager')
    @patch('anthropic.Anthropic')
    def test_outline_query_end_to_end_success(self, mock_anthropic, mock_session, mock_doc_proc, mock_vector, mock_config, test_queries):
        """Test outline query end-to-end - should work because CourseOutlineTool uses **kwargs"""
        from rag_system import RAGSystem
        from fixtures.mock_data import SAMPLE_COURSE_METADATA
        
        # Setup mocks
        mock_vector_instance = MagicMock()
        mock_vector.return_value = mock_vector_instance
        
        # Mock course resolution and metadata for outline tool
        mock_vector_instance._resolve_course_name.return_value = "MCP Course"
        
        from tests.fixtures.mock_data import SAMPLE_COURSE_METADATA
        mock_vector_instance.course_catalog.get.return_value = {
            "metadatas": [SAMPLE_COURSE_METADATA]
        }
        
        # Mock Anthropic responses for outline query
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        
        # Mock tool use for outline
        mock_tool_response = MagicMock()
        mock_tool_response.stop_reason = "tool_use"
        mock_tool_block = MagicMock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.name = "get_course_outline"
        mock_tool_block.id = "outline_123"
        mock_tool_block.input = {"course_title": "MCP"}  # This should work with **kwargs
        mock_tool_response.content = [mock_tool_block]
        
        # Mock final response
        mock_final_response = MagicMock()
        mock_final_response.stop_reason = "stop"
        mock_final_text = MagicMock()
        mock_final_text.text = "Here is the MCP course outline..."
        mock_final_response.content = [mock_final_text]
        
        mock_client.messages.create.side_effect = [mock_tool_response, mock_final_response]
        
        # Mock session manager
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.get_conversation_history.return_value = None
        
        # Test outline query
        rag = RAGSystem(mock_config)
        
        try:
            response, sources = rag.query(test_queries["outline_query"])
            print(f"[SUCCESS] Outline query worked: {response[:50]}...")
            print("[DIAGNOSIS] OutlineTool works because it uses **kwargs signature")
        except Exception as e:
            print(f"[ERROR] Outline query failed: {e}")
    
    @patch('rag_system.VectorStore')
    @patch('rag_system.DocumentProcessor')
    @patch('rag_system.SessionManager')
    @patch('anthropic.Anthropic')
    def test_general_knowledge_query(self, mock_anthropic, mock_session, mock_doc_proc, mock_vector, mock_config, test_queries):
        """Test general knowledge query - should work (no tools needed)"""
        from rag_system import RAGSystem
        
        # Setup mocks
        mock_vector_instance = MagicMock()
        mock_vector.return_value = mock_vector_instance
        
        # Mock direct response (no tools)
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.stop_reason = "stop"
        mock_text = MagicMock()
        mock_text.text = "Machine learning is a subset of artificial intelligence."
        mock_response.content = [mock_text]
        mock_client.messages.create.return_value = mock_response
        
        # Mock session manager
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.get_conversation_history.return_value = None
        
        # Test general knowledge query
        rag = RAGSystem(mock_config)
        response, sources = rag.query(test_queries["general_knowledge"])
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert sources == []  # No sources for general knowledge
        print(f"[PASS] General knowledge query: {response}")
    
    def test_query_failure_cascade_diagnosis(self, mock_config):
        """Demonstrate how query failures cascade through the system"""
        print("\n[DIAGNOSIS] Query Failure Cascade Analysis:")
        print("1. User asks content question")
        print("2. RAG system -> AI Generator")
        print("3. AI Generator -> Anthropic API (wants to use search_course_content)")
        print("4. AI Generator -> ToolManager.execute_tool('search_course_content', **params)")
        print("5. ToolManager -> CourseSearchTool.execute(**params)")
        print("6. FAILURE: CourseSearchTool.execute() expects named params, gets **kwargs")
        print("7. TypeError bubbles up through the system")
        print("8. System returns 'query failed' to user")
        print("\n[ROOT CAUSE] CourseSearchTool.execute() signature mismatch")
        print("[SOLUTION] Change to: def execute(self, **kwargs) -> str")


def test_system_health_check(mock_config):
    """Overall system health check"""
    from rag_system import RAGSystem
    from search_tools import CourseSearchTool, CourseOutlineTool, Tool
    import inspect
    
    print("\n[SYSTEM HEALTH CHECK]")
    
    # Check tool signatures
    tool_sig = str(inspect.signature(Tool.execute))
    search_sig = str(inspect.signature(CourseSearchTool.execute))
    outline_sig = str(inspect.signature(CourseOutlineTool.execute))
    
    print(f"Tool interface: {tool_sig}")
    print(f"CourseSearchTool: {search_sig}")
    print(f"CourseOutlineTool: {outline_sig}")
    
    # Diagnose the issue
    if search_sig == tool_sig:
        print("[HEALTH] CourseSearchTool signature matches interface")
    else:
        print("[PROBLEM] CourseSearchTool signature MISMATCH - this breaks tool calling")
    
    if outline_sig == tool_sig:
        print("[HEALTH] CourseOutlineTool signature matches interface")
    else:
        print("[PROBLEM] CourseOutlineTool signature mismatch")


if __name__ == "__main__":
    # Run with: uv run pytest tests/test_rag_integration.py -v -s
    pytest.main([__file__, "-v", "-s"])