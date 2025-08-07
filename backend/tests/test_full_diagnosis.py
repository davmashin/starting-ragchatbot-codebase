"""Comprehensive test to reproduce the exact 'query failed' issue"""
import pytest
from unittest.mock import MagicMock, patch
import os


class TestFullDiagnosis:
    """Final comprehensive test to identify the real root cause"""
    
    def test_complete_tool_calling_chain_diagnosis(self):
        """Test the complete tool calling chain to find where it breaks"""
        print("\n" + "="*80)
        print("COMPLETE TOOL CALLING CHAIN DIAGNOSIS")
        print("="*80)
        
        # Test each layer independently
        print("\n1. TESTING CourseSearchTool directly...")
        self._test_course_search_tool_direct()
        
        print("\n2. TESTING ToolManager -> CourseSearchTool...")
        self._test_tool_manager_integration()
        
        print("\n3. TESTING AIGenerator -> ToolManager...")
        self._test_ai_generator_integration()
        
        print("\n4. TESTING RAG System end-to-end...")
        self._test_rag_system_integration()
        
        print("\n5. TESTING with real Anthropic parameter patterns...")
        self._test_anthropic_parameter_patterns()
    
    def _test_course_search_tool_direct(self):
        """Test CourseSearchTool execute method directly"""
        from search_tools import CourseSearchTool
        from unittest.mock import MagicMock
        from vector_store import SearchResults
        
        mock_store = MagicMock()
        mock_store.search.return_value = SearchResults(
            documents=["Test content"], 
            metadata=[{"course_title": "Test", "lesson_number": 1}],
            distances=[0.5]
        )
        
        tool = CourseSearchTool(mock_store)
        
        # Test various parameter combinations
        test_cases = [
            {"query": "test"},
            {"query": "test", "course_name": "MCP"},
            {"query": "test", "course_name": "MCP", "lesson_number": 1},
        ]
        
        for i, params in enumerate(test_cases):
            try:
                result = tool.execute(**params)
                print(f"   Case {i+1}: SUCCESS - {params}")
            except Exception as e:
                print(f"   Case {i+1}: FAILED - {params} -> {e}")
    
    def _test_tool_manager_integration(self):
        """Test ToolManager calling CourseSearchTool"""
        from search_tools import ToolManager, CourseSearchTool
        from unittest.mock import MagicMock
        from vector_store import SearchResults
        
        mock_store = MagicMock()
        mock_store.search.return_value = SearchResults(
            documents=["Test content"], 
            metadata=[{"course_title": "Test", "lesson_number": 1}],
            distances=[0.5]
        )
        
        manager = ToolManager()
        tool = CourseSearchTool(mock_store)
        manager.register_tool(tool)
        
        test_cases = [
            {"query": "test"},
            {"query": "test", "course_name": "MCP"},
            {"query": "test", "extra_param": "should_fail"},
        ]
        
        for i, params in enumerate(test_cases):
            try:
                result = manager.execute_tool("search_course_content", **params)
                print(f"   Case {i+1}: SUCCESS - {params}")
            except Exception as e:
                print(f"   Case {i+1}: FAILED - {params} -> {e}")
                if i == 2:  # Expected failure case
                    print("   ^^ This is the likely root cause!")
    
    @patch('anthropic.Anthropic')
    def _test_ai_generator_integration(self, mock_anthropic):
        """Test AIGenerator with tool use"""
        from ai_generator import AIGenerator
        from search_tools import ToolManager, CourseSearchTool
        from unittest.mock import MagicMock
        from vector_store import SearchResults
        
        # Setup tool chain
        mock_store = MagicMock()
        mock_store.search.return_value = SearchResults(
            documents=["Test content"], 
            metadata=[{"course_title": "Test", "lesson_number": 1}],
            distances=[0.5]
        )
        
        manager = ToolManager()
        tool = CourseSearchTool(mock_store)
        manager.register_tool(tool)
        
        # Setup mock Anthropic client
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        
        # Test different tool use scenarios
        scenarios = [
            # Scenario 1: Perfect parameters
            {"query": "test"},
            # Scenario 2: Parameters with course name
            {"query": "test", "course_name": "MCP"},
            # Scenario 3: Parameters that might cause issues
            {"query": "test", "course": "MCP"},  # Wrong parameter name
        ]
        
        for i, params in enumerate(scenarios):
            # Mock tool use response
            mock_tool_response = MagicMock()
            mock_tool_response.stop_reason = "tool_use"
            mock_tool_block = MagicMock()
            mock_tool_block.type = "tool_use"
            mock_tool_block.name = "search_course_content"
            mock_tool_block.id = f"tool_{i}"
            mock_tool_block.input = params
            mock_tool_response.content = [mock_tool_block]
            
            # Mock final response
            mock_final_response = MagicMock()
            mock_final_response.stop_reason = "stop"
            mock_final_text = MagicMock()
            mock_final_text.text = "Final response"
            mock_final_response.content = [mock_final_text]
            
            mock_client.messages.create.side_effect = [mock_tool_response, mock_final_response]
            
            ai_gen = AIGenerator("test_key", "claude-3-sonnet-20240229")
            
            try:
                response = ai_gen.generate_response(
                    "test query",
                    tools=manager.get_tool_definitions(),
                    tool_manager=manager
                )
                print(f"   Scenario {i+1}: SUCCESS - {params}")
            except Exception as e:
                print(f"   Scenario {i+1}: FAILED - {params} -> {e}")
                if "unexpected keyword argument" in str(e):
                    print("   ^^ FOUND THE ROOT CAUSE: Wrong parameter names from Anthropic!")
    
    @patch('rag_system.VectorStore')
    @patch('rag_system.DocumentProcessor') 
    @patch('rag_system.SessionManager')
    @patch('anthropic.Anthropic')
    def _test_rag_system_integration(self, mock_anthropic, mock_session, mock_doc_proc, mock_vector):
        """Test complete RAG system"""
        from rag_system import RAGSystem
        from vector_store import SearchResults
        
        # Setup mocks
        mock_vector_instance = MagicMock()
        mock_vector.return_value = mock_vector_instance
        mock_vector_instance.search.return_value = SearchResults(
            documents=["Test content"], 
            metadata=[{"course_title": "Test", "lesson_number": 1}],
            distances=[0.5]
        )
        
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.get_conversation_history.return_value = None
        
        # Setup Anthropic mock with problematic parameters
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        
        mock_tool_response = MagicMock()
        mock_tool_response.stop_reason = "tool_use"
        mock_tool_block = MagicMock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.name = "search_course_content"
        mock_tool_block.id = "tool_123"
        # This is likely what causes the real issue - wrong parameter names
        mock_tool_block.input = {"query": "test", "course": "MCP"}  # 'course' instead of 'course_name'
        mock_tool_response.content = [mock_tool_block]
        
        mock_final_response = MagicMock()
        mock_final_response.stop_reason = "stop"
        mock_final_text = MagicMock()
        mock_final_text.text = "Final response"
        mock_final_response.content = [mock_final_text]
        
        mock_client.messages.create.side_effect = [mock_tool_response, mock_final_response]
        
        # Test RAG system
        from config import config as mock_config
        rag = RAGSystem(mock_config)
        
        try:
            response, sources = rag.query("What is MCP?")
            print(f"   RAG SUCCESS: {response[:50]}...")
        except Exception as e:
            print(f"   RAG FAILED: {e}")
            print("   ^^ This is likely the source of 'query failed'!")
    
    def _test_anthropic_parameter_patterns(self):
        """Test common parameter patterns that Anthropic might send"""
        print("\nTesting parameter patterns that might cause issues:")
        
        from search_tools import CourseSearchTool
        from unittest.mock import MagicMock
        from vector_store import SearchResults
        
        mock_store = MagicMock()
        mock_store.search.return_value = SearchResults(
            documents=["Test"], metadata=[{"course_title": "Test", "lesson_number": 1}], distances=[0.5]
        )
        
        tool = CourseSearchTool(mock_store)
        
        # Common parameter variations that might come from Anthropic
        problem_patterns = [
            {"query": "test", "course": "MCP"},  # 'course' instead of 'course_name'
            {"query": "test", "lesson": 1},      # 'lesson' instead of 'lesson_number'
            {"query": "test", "course_title": "MCP"},  # 'course_title' instead of 'course_name'
            {"query": "test", "search_query": "test"},  # Wrong query parameter
            {"query": "test", "filters": {"course": "MCP"}},  # Nested parameters
        ]
        
        for i, params in enumerate(problem_patterns):
            try:
                result = tool.execute(**params)
                print(f"   Pattern {i+1}: UNEXPECTED SUCCESS - {params}")
            except TypeError as e:
                print(f"   Pattern {i+1}: EXPECTED FAILURE - {params}")
                print(f"     Error: {e}")
                if "unexpected keyword argument" in str(e):
                    print("     ^^ THIS IS THE ROOT CAUSE!")


def test_final_diagnosis():
    """Run the complete diagnosis"""
    test = TestFullDiagnosis()
    test.test_complete_tool_calling_chain_diagnosis()


if __name__ == "__main__":
    # Run with: uv run pytest tests/test_full_diagnosis.py -v -s
    pytest.main([__file__, "-v", "-s"])