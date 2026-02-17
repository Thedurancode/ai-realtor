"""
AI Agent Executor

Executes autonomous AI agents with tool calling and multi-step reasoning.
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from anthropic.types import Message, TextBlock, ToolUseBlock

from app.services.agent_tools import AgentTools
from app.services.llm_service import llm_service


class AgentExecutor:
    """
    Executes AI agents with tool use and multi-step reasoning.

    The agent can:
    - Make multiple tool calls
    - Reason about results
    - Chain operations together
    - Self-correct based on feedback
    """

    def __init__(self, db: Session):
        self.db = db
        self.agent_tools = AgentTools(db)
        self.max_iterations = 10  # Prevent infinite loops

    async def execute_agent(
        self,
        task: str,
        system_prompt: str,
        property_id: Optional[int] = None,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 4096,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Execute an AI agent with tool use.

        Args:
            task: The task for the agent to complete
            system_prompt: System prompt defining agent personality/role
            property_id: Optional property ID for context
            model: Claude model to use
            max_tokens: Max tokens per response
            temperature: Sampling temperature

        Returns:
            Dict with agent's final response, tool calls made, and execution trace
        """

        # Build conversation history
        messages = []

        # Add property context if provided
        if property_id:
            property_details = await self.agent_tools._get_property_details(property_id)
            if "error" not in property_details:
                context_message = self._format_property_context(property_details)
                messages.append({
                    "role": "user",
                    "content": f"Here's the property you're analyzing:\n\n{context_message}\n\nNow, here's your task: {task}"
                })
            else:
                messages.append({"role": "user", "content": task})
        else:
            messages.append({"role": "user", "content": task})

        # Execution trace for debugging/visibility
        execution_trace = []
        tool_calls_made = []
        iterations = 0

        # Agent execution loop
        while iterations < self.max_iterations:
            iterations += 1

            # Call Claude with tool schemas
            response = llm_service.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=messages,
                tools=self.agent_tools.get_tool_schemas()
            )

            # Log the iteration
            execution_trace.append({
                "iteration": iterations,
                "stop_reason": response.stop_reason,
                "content": self._serialize_content(response.content)
            })

            # Check stop reason
            if response.stop_reason == "end_turn":
                # Agent is done - extract final response
                final_text = self._extract_text_from_response(response)
                return {
                    "success": True,
                    "response": final_text,
                    "iterations": iterations,
                    "tool_calls_made": tool_calls_made,
                    "execution_trace": execution_trace
                }

            elif response.stop_reason == "tool_use":
                # Agent wants to use tools
                # Add assistant's response to conversation
                messages.append({
                    "role": "assistant",
                    "content": response.content
                })

                # Execute all tool calls
                tool_results = []
                for content_block in response.content:
                    if isinstance(content_block, ToolUseBlock):
                        tool_name = content_block.name
                        tool_input = content_block.input
                        tool_use_id = content_block.id

                        # Execute the tool
                        tool_result = await self.agent_tools.execute_tool(tool_name, tool_input)

                        # Log tool call
                        tool_calls_made.append({
                            "tool": tool_name,
                            "input": tool_input,
                            "result": tool_result
                        })

                        # Add tool result to conversation
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": str(tool_result)
                        })

                # Add tool results to conversation
                messages.append({
                    "role": "user",
                    "content": tool_results
                })

                # Continue loop - agent will process results

            elif response.stop_reason == "max_tokens":
                # Response was cut off
                final_text = self._extract_text_from_response(response)
                return {
                    "success": False,
                    "response": final_text,
                    "error": "Response truncated due to max_tokens limit",
                    "iterations": iterations,
                    "tool_calls_made": tool_calls_made,
                    "execution_trace": execution_trace
                }

            else:
                # Unknown stop reason
                return {
                    "success": False,
                    "response": "",
                    "error": f"Unexpected stop reason: {response.stop_reason}",
                    "iterations": iterations,
                    "tool_calls_made": tool_calls_made,
                    "execution_trace": execution_trace
                }

        # Max iterations reached
        return {
            "success": False,
            "response": "Agent reached maximum iteration limit",
            "error": "Max iterations exceeded",
            "iterations": iterations,
            "tool_calls_made": tool_calls_made,
            "execution_trace": execution_trace
        }

    def _extract_text_from_response(self, response: Message) -> str:
        """Extract text content from Claude response"""
        text_parts = []
        for content_block in response.content:
            if isinstance(content_block, TextBlock):
                text_parts.append(content_block.text)
        return "\n".join(text_parts)

    def _serialize_content(self, content: List) -> List[Dict]:
        """Serialize response content for logging"""
        serialized = []
        for block in content:
            if isinstance(block, TextBlock):
                serialized.append({"type": "text", "text": block.text})
            elif isinstance(block, ToolUseBlock):
                serialized.append({
                    "type": "tool_use",
                    "name": block.name,
                    "input": block.input
                })
        return serialized

    def _format_property_context(self, property_details: Dict) -> str:
        """Format property details for context"""
        return f"""Property Details:
- Address: {property_details['address']}, {property_details['city']}, {property_details['state']} {property_details['zip_code']}
- Price: ${property_details['price']:,}
- Beds/Baths: {property_details['bedrooms']}/{property_details['bathrooms']}
- Square Feet: {property_details['square_feet']:,}
- Year Built: {property_details['year_built']}
- Property Type: {property_details['property_type']}
- Status: {property_details['status']}
- Price per Sq Ft: ${property_details['price_per_sqft']}/sq ft"""
