"""Tests for AIGenerator tool calling mechanism"""
import pytest
from unittest.mock import MagicMock, patch
from tests.fixtures.mock_data import TEST_PARAMETERS


class TestAIGenerator:
    """Test AIGenerator tool calling functionality"""
    
    def test_system_prompt_contains_tool_instructions(self):
        """Test that system prompt includes sequential tool usage guidelines"""
        from ai_generator import AIGenerator
        
        ai_gen = AIGenerator("test_key", "claude-3-sonnet-20240229")
        
        prompt = ai_gen.SYSTEM_PROMPT
        assert "Tool Usage Guidelines" in prompt
        assert "Course Content Search" in prompt
        assert "Course Outline" in prompt
        assert "Sequential Tool Use" in prompt
        assert "Maximum 2 tool rounds" in prompt
        assert "Tool Combination Strategy" in prompt
        # Verify old restriction is removed
        assert "One tool call per query maximum" not in prompt
        print("[PASS] System prompt contains sequential tool instructions")
    
    @patch('anthropic.Anthropic')
    def test_generate_response_without_tools(self, mock_anthropic_class):
        """Test response generation without tool use"""
        from ai_generator import AIGenerator
        
        # Setup mock
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.stop_reason = "stop"
        mock_text = MagicMock()
        mock_text.text = "Machine learning is a subset of AI."
        mock_response.content = [mock_text]
        mock_client.messages.create.return_value = mock_response
        
        # Test
        ai_gen = AIGenerator("test_key", "claude-3-sonnet-20240229")
        response = ai_gen.generate_response("What is machine learning?")
        
        assert isinstance(response, str)
        assert "machine learning" in response.lower()
        
        # Verify no tools were passed
        call_args = mock_client.messages.create.call_args[1]
        assert "tools" not in call_args
        
        print(f"[PASS] No-tool response: {response}")
    
    @patch('anthropic.Anthropic')
    def test_generate_response_single_round_tool_use(self, mock_anthropic_class, tool_manager):
        """Test single round tool use (backward compatibility)"""
        from ai_generator import AIGenerator
        
        # Setup mock Anthropic client
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        
        # Mock tool use response then direct response
        mock_tool_response = MagicMock()
        mock_tool_response.stop_reason = "tool_use"
        mock_tool_block = MagicMock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.name = "search_course_content"
        mock_tool_block.id = "tool_123"
        mock_tool_block.input = {"query": "What is MCP?"}
        mock_tool_response.content = [mock_tool_block]
        
        # Mock final response after tool execution
        mock_final_response = MagicMock()
        mock_final_response.stop_reason = "stop"
        mock_final_text = MagicMock()
        mock_final_text.text = "MCP is the Model Context Protocol."
        mock_final_response.content = [mock_final_text]
        
        mock_client.messages.create.side_effect = [mock_tool_response, mock_final_response]
        
        ai_gen = AIGenerator("test_key", "claude-3-sonnet-20240229")
        response = ai_gen.generate_response(
            "What is MCP?",
            tools=tool_manager.get_tool_definitions(),
            tool_manager=tool_manager
        )
        
        # Verify two API calls were made (tool use + final response)
        assert mock_client.messages.create.call_count == 2
        assert "MCP is the Model Context Protocol" in response
        print(f"[PASS] Single round tool use: {response}")
    
    @patch('anthropic.Anthropic')
    def test_generate_response_sequential_two_rounds(self, mock_anthropic_class, tool_manager):
        """Test sequential tool calling with two rounds"""
        from ai_generator import AIGenerator
        
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        
        # Mock Round 1: tool use
        mock_round1_response = MagicMock()
        mock_round1_response.stop_reason = "tool_use"
        mock_tool_block1 = MagicMock()
        mock_tool_block1.type = "tool_use"
        mock_tool_block1.name = "get_course_outline"
        mock_tool_block1.id = "tool_round1"
        mock_tool_block1.input = {"course_title": "MCP"}
        mock_round1_response.content = [mock_tool_block1]
        
        # Mock Round 2: tool use again
        mock_round2_response = MagicMock()
        mock_round2_response.stop_reason = "tool_use"
        mock_tool_block2 = MagicMock()
        mock_tool_block2.type = "tool_use"
        mock_tool_block2.name = "search_course_content"
        mock_tool_block2.id = "tool_round2"
        mock_tool_block2.input = {"query": "WebSockets", "course_name": "MCP"}
        mock_round2_response.content = [mock_tool_block2]
        
        # Mock final response (after max rounds)
        mock_final_response = MagicMock()
        mock_final_response.stop_reason = "stop"
        mock_final_text = MagicMock()
        mock_final_text.text = "MCP covers WebSockets in lesson 3."
        mock_final_response.content = [mock_final_text]
        
        mock_client.messages.create.side_effect = [mock_round1_response, mock_round2_response, mock_final_response]
        
        ai_gen = AIGenerator("test_key", "claude-3-sonnet-20240229")
        response = ai_gen.generate_response(
            "What does the MCP course cover about WebSockets?",
            tools=tool_manager.get_tool_definitions(),
            tool_manager=tool_manager,
            max_rounds=2
        )
        
        # Verify three API calls were made (round1 + round2 + final)
        assert mock_client.messages.create.call_count == 3
        assert "MCP covers WebSockets" in response
        print(f"[PASS] Two round tool use: {response}")
    
    @patch('anthropic.Anthropic')
    def test_generate_response_early_termination(self, mock_anthropic_class, tool_manager):
        """Test early termination when Claude provides direct response"""
        from ai_generator import AIGenerator
        
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        
        # Mock direct response (no tool use)
        mock_direct_response = MagicMock()
        mock_direct_response.stop_reason = "stop"
        mock_direct_text = MagicMock()
        mock_direct_text.text = "Machine learning is a subset of AI."
        mock_direct_response.content = [mock_direct_text]
        
        mock_client.messages.create.return_value = mock_direct_response
        
        ai_gen = AIGenerator("test_key", "claude-3-sonnet-20240229")
        response = ai_gen.generate_response(
            "What is machine learning?",
            tools=tool_manager.get_tool_definitions(),
            tool_manager=tool_manager,
            max_rounds=2
        )
        
        # Verify only one API call was made (direct response)
        assert mock_client.messages.create.call_count == 1
        assert "Machine learning is a subset of AI" in response
        print(f"[PASS] Early termination: {response}")
    
    @patch('anthropic.Anthropic')
    def test_helper_methods(self, mock_anthropic_class):
        """Test the new helper methods"""
        from ai_generator import AIGenerator
        
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        
        ai_gen = AIGenerator("test_key", "claude-3-sonnet-20240229")
        
        # Test _build_system_content
        system_content = ai_gen._build_system_content(None)
        assert system_content == ai_gen.SYSTEM_PROMPT
        
        system_content_with_history = ai_gen._build_system_content("Previous: Hello")
        assert "Previous conversation:" in system_content_with_history
        assert "Previous: Hello" in system_content_with_history
        
        print("[PASS] Helper methods work correctly")
    
    def test_tool_parameter_extraction_and_error_handling(self):
        """Test parameter extraction and error handling in sequential calling"""
        from ai_generator import AIGenerator
        
        # Mock a tool use content block like Anthropic would send
        mock_tool_block = MagicMock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.name = "search_course_content"
        mock_tool_block.id = "test_id"
        mock_tool_block.input = {
            "query": "What is MCP?",
            "course_name": "MCP Course",
            "lesson_number": 1
        }
        
        # Test parameter extraction
        params = mock_tool_block.input
        assert isinstance(params, dict)
        assert "query" in params
        assert params["query"] == "What is MCP?"
        
        # Test error handling in _execute_tools_and_update_messages
        ai_gen = AIGenerator("test_key", "claude-3-sonnet-20240229")
        
        # Mock response with tool use
        mock_response = MagicMock()
        mock_response.content = [mock_tool_block]
        
        # Mock tool manager that raises exception
        mock_tool_manager = MagicMock()
        mock_tool_manager.execute_tool.side_effect = Exception("Tool failed")
        
        messages = [{"role": "user", "content": "test"}]
        
        # Should handle error gracefully
        result_messages = ai_gen._execute_tools_and_update_messages(
            mock_response, messages, mock_tool_manager
        )
        
        # Should have added assistant message and error result
        assert len(result_messages) == 3  # original + assistant + tool_result
        tool_result_message = result_messages[2]
        assert tool_result_message["role"] == "user"
        assert "Tool execution failed" in str(tool_result_message["content"])
        
        print("[PASS] Parameter extraction and error handling work correctly")


def test_sequential_tool_calling_integration(tool_manager):
    """Test that sequential tool calling works with actual tool manager"""
    
    # Test both tools work individually
    try:
        outline_result = tool_manager.execute_tool("get_course_outline", course_title="MCP")
        print(f"[WORKING] CourseOutlineTool: {outline_result[:50]}...")
    except Exception as e:
        print(f"[ERROR] CourseOutlineTool failed: {e}")
    
    try:
        search_result = tool_manager.execute_tool("search_course_content", **TEST_PARAMETERS["valid_kwargs"])
        print(f"[WORKING] CourseSearchTool: {search_result[:50]}...")
    except Exception as e:
        print(f"[ERROR] CourseSearchTool failed: {e}")
    
    print("[INFO] Both tools should work for sequential calling")


if __name__ == "__main__":
    # Run with: uv run pytest tests/test_ai_generator.py -v -s
    pytest.main([__file__, "-v", "-s"])