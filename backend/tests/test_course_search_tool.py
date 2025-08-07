"""Tests for CourseSearchTool execute method - identifies parameter signature mismatch"""
import pytest
from unittest.mock import MagicMock
from tests.fixtures.mock_data import TEST_PARAMETERS, EXPECTED_SEARCH_TOOL_DEF


class TestCourseSearchTool:
    """Test CourseSearchTool functionality, focusing on parameter signature issues"""
    
    def test_tool_definition_structure(self, course_search_tool):
        """Test that tool definition matches expected Anthropic schema"""
        definition = course_search_tool.get_tool_definition()
        
        assert definition["name"] == "search_course_content"
        assert "description" in definition
        assert "input_schema" in definition
        
        schema = definition["input_schema"]
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "required" in schema
        assert schema["required"] == ["query"]
        
        # Verify all expected properties exist
        properties = schema["properties"] 
        assert "query" in properties
        assert "course_name" in properties
        assert "lesson_number" in properties
    
    def test_execute_with_named_parameters(self, course_search_tool):
        """Test execute with named parameters (current signature) - SHOULD WORK"""
        result = course_search_tool.execute(
            query="What is MCP?",
            course_name="MCP",
            lesson_number=1
        )
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert "MCP" in result
        print(f"[PASS] Named parameters work: {result[:50]}...")
    
    def test_execute_with_kwargs_unpacking(self, course_search_tool):
        """Test execute with **kwargs (how ToolManager calls it) - CRITICAL TEST"""
        # This is exactly how ToolManager.execute_tool() calls the tool
        kwargs = TEST_PARAMETERS["valid_kwargs"]
        
        # Let's see what actually happens when we call with **kwargs
        try:
            result = course_search_tool.execute(**kwargs)
            print(f"[UNEXPECTED SUCCESS] execute(**kwargs) worked: {result[:50]}...")
            print(f"[KWARGS USED] {kwargs}")
            print("[ANALYSIS] kwargs unpacking actually works because parameter names match!")
        except TypeError as e:
            print(f"[EXPECTED FAILURE] execute(**kwargs) failed: {e}")
            print("[ANALYSIS] Parameter signature mismatch confirmed")
        except Exception as e:
            print(f"[OTHER ERROR] execute(**kwargs) failed with: {type(e).__name__}: {e}")
            print("[ANALYSIS] Different error than expected - investigate further")
    
    def test_execute_query_only(self, course_search_tool):
        """Test execute with only query parameter"""
        result = course_search_tool.execute(query="What is machine learning?")
        
        assert isinstance(result, str)
        assert len(result) > 0
        print(f"[PASS] Query only works: {result[:50]}...")
    
    def test_execute_missing_required_query(self, course_search_tool):
        """Test execute without required query parameter"""
        with pytest.raises(TypeError):
            course_search_tool.execute(course_name="MCP", lesson_number=1)
    
    def test_format_results_method(self, course_search_tool, sample_search_results):
        """Test the _format_results method independently"""
        formatted = course_search_tool._format_results(sample_search_results)
        
        assert isinstance(formatted, str)
        assert "MCP Course" in formatted
        assert "Lesson 1" in formatted
        assert "Model Context Protocol" in formatted
        print(f"[PASS] Format results: {formatted[:100]}...")
    
    def test_empty_search_results(self, course_search_tool, mock_vector_store, empty_search_results):
        """Test handling of empty search results"""
        mock_vector_store.search.return_value = empty_search_results
        
        result = course_search_tool.execute(query="nonexistent content")
        
        assert "No relevant content found" in result
        print(f"[PASS] Empty results handled: {result}")
    
    def test_error_search_results(self, course_search_tool, mock_vector_store, error_search_results):
        """Test handling of error results from vector store"""
        mock_vector_store.search.return_value = error_search_results
        
        result = course_search_tool.execute(query="test query")
        
        assert result == "Database connection failed"
        print(f"[PASS] Error results handled: {result}")
    
    def test_sources_tracking(self, course_search_tool, sample_search_results):
        """Test that sources are properly tracked after execution"""
        # Mock the format results to use our sample data
        course_search_tool._format_results(sample_search_results)
        
        # Check sources were stored
        assert hasattr(course_search_tool, 'last_sources')
        assert isinstance(course_search_tool.last_sources, list)
        
        if course_search_tool.last_sources:
            print(f"[PASS] Sources tracked: {course_search_tool.last_sources}")
    
    def test_parameter_signature_comparison(self):
        """Document the signature mismatch issue"""
        from search_tools import Tool, CourseSearchTool, CourseOutlineTool
        import inspect
        
        # Get signatures
        tool_sig = inspect.signature(Tool.execute)
        search_sig = inspect.signature(CourseSearchTool.execute) 
        outline_sig = inspect.signature(CourseOutlineTool.execute)
        
        print(f"[DIAGNOSIS] Tool (abstract): {tool_sig}")
        print(f"[DIAGNOSIS] CourseSearchTool: {search_sig}")
        print(f"[DIAGNOSIS] CourseOutlineTool: {outline_sig}")
        
        # The issue: CourseSearchTool doesn't match the abstract interface
        assert str(tool_sig) == "(self, **kwargs) -> str"
        assert str(outline_sig) == "(self, **kwargs) -> str"
        assert str(search_sig) != "(self, **kwargs) -> str"  # This is the problem!
        
        print("[ROOT CAUSE] CourseSearchTool.execute() signature doesn't match Tool interface!")


def test_toolmanager_parameter_passing_investigation(tool_manager):
    """Investigate what actually happens in ToolManager -> CourseSearchTool flow"""
    # This mimics exactly what happens in the real system
    kwargs = TEST_PARAMETERS["valid_kwargs"]
    
    # ToolManager.execute_tool() calls tool.execute(**kwargs) 
    try:
        result = tool_manager.execute_tool("search_course_content", **kwargs)
        print(f"[UNEXPECTED SUCCESS] ToolManager -> CourseSearchTool works: {result[:50]}...")
        print(f"[ANALYSIS] Tool calling is actually working - issue must be elsewhere!")
    except Exception as e:
        print(f"[ERROR] ToolManager -> CourseSearchTool failed: {type(e).__name__}: {e}")
        print("[ANALYSIS] This could be the real issue")
    
    # Test outline tool for comparison
    try:
        outline_result = tool_manager.execute_tool("get_course_outline", course_title="MCP")
        print(f"[COMPARISON] OutlineTool works: {outline_result[:50]}...")
    except Exception as e:
        print(f"[ERROR] OutlineTool also failed: {e}")
    
    # Test with invalid parameters to see error handling
    try:
        invalid_result = tool_manager.execute_tool("search_course_content", invalid_param="test")
        print(f"[ERROR HANDLING] Invalid params: {invalid_result}")
    except Exception as e:
        print(f"[ERROR HANDLING] Invalid params raised: {e}")


if __name__ == "__main__":
    # Run with: uv run pytest tests/test_course_search_tool.py -v -s
    pytest.main([__file__, "-v", "-s"])