"""Test realistic scenarios that might cause 'query failed' in the real system"""
import pytest
from unittest.mock import MagicMock, patch
import os

class TestRealWorldScenarios:
    """Test scenarios that might cause the actual 'query failed' issue"""
    
    def test_anthropic_parameter_variations(self, tool_manager):
        """Test various parameter combinations that Anthropic might send"""
        
        # Scenario 1: Perfect parameters (should work)
        perfect_params = {"query": "What is MCP?", "course_name": "MCP", "lesson_number": 1}
        try:
            result = tool_manager.execute_tool("search_course_content", **perfect_params)
            print(f"[PASS] Perfect params: {result[:30]}...")
        except Exception as e:
            print(f"[FAIL] Perfect params failed: {e}")
        
        # Scenario 2: Query only (should work) 
        query_only = {"query": "What is machine learning?"}
        try:
            result = tool_manager.execute_tool("search_course_content", **query_only)
            print(f"[PASS] Query only: {result[:30]}...")
        except Exception as e:
            print(f"[FAIL] Query only failed: {e}")
        
        # Scenario 3: Extra parameters Anthropic might add
        extra_params = {"query": "What is MCP?", "course_name": "MCP", "extra_param": "unexpected"}
        try:
            result = tool_manager.execute_tool("search_course_content", **extra_params)
            print(f"[FAIL] Extra params should have failed but didn't: {result[:30]}...")
        except TypeError as e:
            print(f"[EXPECTED] Extra params failed correctly: {e}")
        except Exception as e:
            print(f"[UNEXPECTED] Extra params failed with other error: {e}")
        
        # Scenario 4: Wrong parameter names
        wrong_names = {"search_query": "What is MCP?", "course": "MCP"}
        try:
            result = tool_manager.execute_tool("search_course_content", **wrong_names)
            print(f"[FAIL] Wrong names should have failed but didn't: {result[:30]}...")
        except TypeError as e:
            print(f"[EXPECTED] Wrong names failed correctly: {e}")
        except Exception as e:
            print(f"[UNEXPECTED] Wrong names failed with other error: {e}")
    
    def test_vector_store_failure_scenarios(self, tool_manager, mock_vector_store):
        """Test what happens when vector store operations fail"""
        from vector_store import SearchResults
        
        # Scenario 1: Vector store returns error
        mock_vector_store.search.return_value = SearchResults.empty("Database connection failed")
        
        try:
            result = tool_manager.execute_tool("search_course_content", query="test")
            print(f"[VECTOR ERROR] {result}")
            assert result == "Database connection failed"
        except Exception as e:
            print(f"[UNEXPECTED] Vector error handling failed: {e}")
        
        # Scenario 2: Vector store raises exception
        mock_vector_store.search.side_effect = Exception("Database crashed")
        
        try:
            result = tool_manager.execute_tool("search_course_content", query="test")
            print(f"[EXCEPTION] Result when vector store crashes: {result}")
        except Exception as e:
            print(f"[EXCEPTION] Tool execution failed when vector store crashed: {e}")
    
    @patch.dict(os.environ, {}, clear=True)
    def test_missing_environment_variables(self):
        """Test what happens when required environment variables are missing"""
        # This might cause issues in the real system
        try:
            from ai_generator import AIGenerator
            ai_gen = AIGenerator("fake_key", "claude-3-sonnet-20240229")
            print("[ENV] AIGenerator created with fake key - this might cause real-world failures")
        except Exception as e:
            print(f"[ENV] Environment issue: {e}")
    
    def test_tool_execution_error_handling(self, tool_manager):
        """Test how tool execution errors are handled"""
        
        # Simulate a tool that always raises an exception
        class BrokenTool:
            def get_tool_definition(self):
                return {"name": "broken_tool", "description": "Always fails"}
            
            def execute(self, **kwargs):
                raise Exception("Simulated tool failure")
        
        # Register broken tool
        broken_tool = BrokenTool()
        tool_manager.register_tool(broken_tool)
        
        # Test execution
        try:
            result = tool_manager.execute_tool("broken_tool", query="test")
            print(f"[ERROR HANDLING] Broken tool result: {result}")
        except Exception as e:
            print(f"[ERROR HANDLING] Broken tool raised: {e}")
            print("[ANALYSIS] This might be how errors propagate to 'query failed'")
    
    @patch('anthropic.Anthropic')
    def test_full_ai_generator_flow_with_realistic_errors(self, mock_anthropic, tool_manager):
        """Test the full AI Generator flow with realistic error scenarios"""
        from ai_generator import AIGenerator
        
        # Setup mock client that simulates network/API errors
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        
        # Scenario 1: API connection error
        mock_client.messages.create.side_effect = Exception("API connection failed")
        
        ai_gen = AIGenerator("test_key", "claude-3-sonnet-20240229")
        
        try:
            response = ai_gen.generate_response(
                "What is MCP?",
                tools=tool_manager.get_tool_definitions(),
                tool_manager=tool_manager
            )
            print(f"[API ERROR] Unexpected success: {response}")
        except Exception as e:
            print(f"[API ERROR] Expected API failure: {e}")
            print("[ANALYSIS] API errors might cause 'query failed' in real system")
    
    def test_identify_actual_error_source(self, tool_manager):
        """Try to identify where 'query failed' actually comes from"""
        
        print("\n[DIAGNOSIS] Searching for 'query failed' error source...")
        
        # Check if it's in tool execution
        try:
            result = tool_manager.execute_tool("search_course_content", query="test")
            if "query failed" in result.lower():
                print("[FOUND] 'query failed' comes from tool execution")
            else:
                print("[NOT FOUND] 'query failed' not in tool result")
        except Exception as e:
            if "query failed" in str(e).lower():
                print("[FOUND] 'query failed' comes from tool exception")
            else:
                print(f"[NOT FOUND] Tool exception doesn't contain 'query failed': {e}")
        
        # The error might be in the web API layer or error handling
        print("[HYPOTHESIS] 'query failed' might come from:")
        print("1. Web API error handling (app.py)")
        print("2. RAG system error handling")
        print("3. Session management issues")
        print("4. Network/timeout errors")


if __name__ == "__main__":
    # Run with: uv run pytest tests/test_real_world_scenario.py -v -s
    pytest.main([__file__, "-v", "-s"])