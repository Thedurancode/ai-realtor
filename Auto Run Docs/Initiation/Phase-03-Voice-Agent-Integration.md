# Phase 03: Voice Agent Integration & Real-Time MCP Tracking

This phase connects the activity feed deeply with the voice agent and MCP tools, creating a seamless experience where every voice command and tool execution is beautifully visualized in real-time. The feed becomes a true "sidekick" to your AI assistant.

## Tasks

- [ ] Enhance MCP server to broadcast detailed tool execution events:
  - Update `/mcp_server/property_mcp.py` to capture and log detailed execution metadata for every tool call: start time, end time, input parameters, output data (truncated if large), error messages, user context
  - Add pre-execution logging that sends `tool_started` event via WebSocket with pending status
  - Add post-execution logging that sends `tool_completed` or `tool_failed` event with full results
  - Create execution correlation IDs to link start/complete events for the same tool call
  - Add user source detection: determine if call came from Claude Desktop, API, or voice assistant

- [ ] Build voice command visualization components:
  - Create `/frontend/components/ActivityFeed/VoiceCommandCard.tsx` specialized for voice input events with waveform animation visualization
  - Add speech-to-text transcript display that shows what the user said
  - Implement intent extraction display showing detected action, entity, and parameters
  - Add voice avatar with animated speaking indicator (pulsing rings) when voice commands are active
  - Show linked tool executions that resulted from the voice command with connecting line animations

- [ ] Create tool execution timeline with parent-child relationships:
  - Update `/frontend/components/ActivityFeed/ActivityTimeline.tsx` to support nested/grouped activities
  - Implement tree view where voice commands are parent nodes and tool executions are children
  - Add collapsible sections for complex workflows (e.g., "Create property" -> address lookup -> property creation -> notification sent)
  - Create connecting lines/arrows between related activities using SVG paths
  - Add duration indicators showing how long each step took and total workflow time

- [ ] Implement live execution tracking with progress indicators:
  - Create `/frontend/components/ActivityFeed/LiveExecutionPanel.tsx` that shows currently running tool executions
  - Add progress bars with indeterminate animation for long-running operations (enrichment, skip trace)
  - Implement estimated time remaining calculation based on historical execution times stored in database
  - Show spinning activity indicator with tool icon for pending operations
  - Add "Cancel" button for long-running operations that sends cancellation request to backend (if supported)
  - Display real-time logs/streaming output for operations that support it

- [ ] Add voice agent status display and conversation history:
  - Create `/frontend/components/ActivityFeed/VoiceAgentStatus.tsx` floating widget showing: agent online status, last command timestamp, active conversation session
  - Implement conversation thread view that groups related voice commands and tool executions into sessions
  - Add session timeline showing conversation flow: user speaks -> agent responds -> tools execute -> agent responds with results
  - Create collapsible conversation cards with full transcript of voice exchanges
  - Add "Replay" button that shows the sequence of events in slow motion with highlighted animations

- [ ] Integrate with existing voice hooks and test end-to-end voice workflow:
  - Update `/frontend/hooks/useVoiceIntegration.ts` to emit voice command events to the activity feed
  - Connect voice recognition events to create activity entries when speech is detected
  - Test complete voice workflow: speak command -> see waveform animation -> watch tools execute in real-time -> see results appear
  - Verify correlation between voice commands and resulting tool executions is visible
  - Create demonstration script `/scripts/demo_voice_workflow.py` that simulates a complete voice-to-execution flow
  - Document the integration in `/Auto Run Docs/Initiation/Working/phase-03-voice-integration.md`
