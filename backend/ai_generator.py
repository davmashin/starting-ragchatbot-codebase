import anthropic
from typing import List, Optional, Dict, Any

class AIGenerator:
    """Handles interactions with Anthropic's Claude API for generating responses"""
    
    # Static system prompt to avoid rebuilding on each call
    SYSTEM_PROMPT = """ You are an AI assistant specialized in course materials and educational content with access to comprehensive tools for course information.

Tool Usage Guidelines:
- **Sequential Tool Use**: You can use tools across multiple rounds to gather comprehensive information
- **Maximum 2 tool rounds**: Plan your tool usage strategically within this limit
- **Course Content Search**: Use for questions about specific course content or detailed educational materials
- **Course Outline**: Use for questions about course structure, lesson lists, course overviews, or "what is covered in [course]"
- **Tool Combination Strategy**: 
  - Round 1: Use outline tool to understand course structure, then search tool for specific content
  - Round 1: Use search tool with broad terms, then narrow down in Round 2
  - Choose the most efficient approach for each query
- Synthesize tool results into accurate, fact-based responses
- If tools yield no results, state this clearly without offering alternatives

Tool Selection Strategy:
- **Outline First**: When you need both structure AND content from a course
- **Search First**: When you need specific content but course structure is less important  
- **Iterative Refinement**: Use results from Round 1 to make more targeted Round 2 queries
- **Outline queries**: Course structure, lesson breakdown, course overview, "what lessons are in...", "outline of..."
- **Content queries**: Specific topics, detailed explanations, lesson-specific content
- **General knowledge**: Answer directly without tools

When using the outline tool, always include:
- Course title and instructor
- Course link (if available)
- Complete list of lessons with numbers and titles
- Lesson links (if available)

Response Protocol:
- **General knowledge questions**: Answer using existing knowledge without tools
- **Course-specific questions**: Use appropriate tools strategically across available rounds
- **No meta-commentary**:
 - Provide direct answers only — no reasoning process, tool explanations, or question-type analysis
 - Do not mention "based on the search results" or "using the outline tool"
- When you have gathered sufficient information through tools OR reached the round limit, provide your final answer without requesting more tools

All responses must be:
1. **Brief, Concise and focused** - Get to the point quickly
2. **Educational** - Maintain instructional value
3. **Clear** - Use accessible language
4. **Example-supported** - Include relevant examples when they aid understanding
Provide only the direct answer to what was asked.
"""
    
    def __init__(self, api_key: str, model: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        
        # Pre-build base API parameters
        self.base_params = {
            "model": self.model,
            "temperature": 0,
            "max_tokens": 800
        }
    
    def generate_response(self, query: str,
                         conversation_history: Optional[str] = None,
                         tools: Optional[List] = None,
                         tool_manager=None,
                         max_rounds: int = 2) -> str:
        """
        Generate AI response with sequential tool calling support.
        
        Args:
            query: The user's question or request
            conversation_history: Previous messages for context
            tools: Available tools the AI can use
            tool_manager: Manager to execute tools
            max_rounds: Maximum tool calling rounds (default 2)
            
        Returns:
            Generated response as string
        """
        
        # Build initial system content and messages
        system_content = self._build_system_content(conversation_history)
        messages = [{"role": "user", "content": query}]
        
        # Tool calling loop - support sequential rounds
        for round_num in range(max_rounds):
            response = self._make_api_call(messages, system_content, tools)
            
            # Check if Claude wants to use tools
            if response.stop_reason != "tool_use":
                # Direct response - we're done
                return response.content[0].text
            
            # Execute tools and prepare for next round
            if not tool_manager:
                # No tool manager available - return text response if any
                return response.content[0].text if response.content else "Tool execution not available"
            
            messages = self._execute_tools_and_update_messages(
                response, messages, tool_manager
            )
        
        # Final API call after max rounds reached (without tools to force response)
        final_response = self._make_api_call(messages, system_content, tools=None)
        return final_response.content[0].text
    
    def _build_system_content(self, conversation_history: Optional[str]) -> str:
        """
        Build system content with conversation history if provided.
        
        Args:
            conversation_history: Previous conversation context
            
        Returns:
            Complete system content string
        """
        if conversation_history:
            return f"{self.SYSTEM_PROMPT}\n\nPrevious conversation:\n{conversation_history}"
        return self.SYSTEM_PROMPT
    
    def _make_api_call(self, messages: List[Dict], system_content: str, 
                       tools: Optional[List] = None):
        """
        Make API call to Claude with consistent parameters.
        
        Args:
            messages: Message history for the conversation
            system_content: System prompt content
            tools: Available tools (None to disable tools)
            
        Returns:
            Claude API response
        """
        api_params = {
            **self.base_params,
            "messages": messages,
            "system": system_content
        }
        
        if tools:
            api_params["tools"] = tools
            api_params["tool_choice"] = {"type": "auto"}
        
        return self.client.messages.create(**api_params)
    
    def _execute_tools_and_update_messages(self, response, messages: List[Dict], 
                                         tool_manager) -> List[Dict]:
        """
        Execute tools and update message history for next round.
        
        Args:
            response: Claude response containing tool use requests
            messages: Current message history
            tool_manager: Tool execution manager
            
        Returns:
            Updated messages list with tool results
        """
        # Add Claude's tool use response to messages
        messages.append({"role": "assistant", "content": response.content})
        
        # Execute all tool calls and collect results
        tool_results = []
        for content_block in response.content:
            if content_block.type == "tool_use":
                try:
                    tool_result = tool_manager.execute_tool(
                        content_block.name,
                        **content_block.input
                    )
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": content_block.id,
                        "content": tool_result
                    })
                except Exception as e:
                    # Handle tool execution errors gracefully
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": content_block.id,
                        "content": f"Tool execution failed: {str(e)}"
                    })
        
        # Add tool results to messages
        if tool_results:
            messages.append({"role": "user", "content": tool_results})
        
        return messages