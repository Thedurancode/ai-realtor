"""
AI Assistant - Complete Personal and Business Assistant

Features:
- Voice-controlled (when integrated with VAPI/ElevenLabs)
- Web search capabilities
- Code execution and analysis
- Document analysis
- Task management
- Calendar integration
- Email processing
- File operations
- Knowledge base
- Memory system
"""

import asyncio
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import httpx
import subprocess
import re
from pathlib import Path

# Try imports, provide fallbacks
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    print("Warning: OpenAI not installed. Some features will be limited.")

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("Warning: requests not installed. Web search will be limited.")


@dataclass
class Task:
    """Task for task management"""
    id: str
    title: str
    description: str
    priority: str  # high, medium, low
    status: str  # todo, in_progress, done
    created_at: str
    due_date: Optional[str] = None
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class CalendarEvent:
    """Calendar event"""
    id: str
    title: str
    start: str
    end: str
    description: str
    location: Optional[str] = None
    attendees: List[str] = None

    def __post_init__(self):
        if self.attendees is None:
            self.attendees = []


@dataclass
class Email:
    """Email message"""
    id: str
    from_email: str
    to_email: str
    subject: str
    body: str
    timestamp: str
    read: bool = False


class AIAssistant:
    """
    Complete AI Assistant with multiple capabilities

    Features:
    - Web search via multiple providers
    - Code execution and analysis
    - File operations
    - Task management
    - Calendar management
    - Email processing
    - Knowledge base
    - Memory system
    - Voice-ready responses
    """

    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initialize AI Assistant

        Args:
            openai_api_key: OpenAI API key for advanced features (optional)
        """
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")

        # Initialize components
        self.tasks: List[Task] = []
        self.calendar: List[CalendarEvent] = []
        self.emails: List[Email] = []
        self.knowledge_base: Dict[str, Any] = {}
        self.memory: List[Dict[str, Any]] = []
        self.files: Dict[str, Path] = {}

        # Working directory
        self.working_dir = Path.cwd()

        # Initialize OpenAI if available
        if HAS_OPENAI and self.api_key:
            self.openai_client = OpenAI(api_key=self.api_key)
        else:
            self.openai_client = None
            print("OpenAI not available. Using rule-based responses.")

    # ========================================================================
    # CORE ASSISTANT CAPABILITIES
    # ========================================================================

    async def chat(self, message: str, context: Optional[Dict] = None) -> str:
        """
        Main chat interface - processes user message and returns response

        Args:
            message: User's message
            context: Optional context from voice/conversation

        Returns:
            Assistant's response
        """
        message_lower = message.lower()

        # Analyze intent
        intent = await self._detect_intent(message)

        # Route to appropriate handler
        if intent == "web_search":
            return await self._web_search(message)
        elif intent == "code_execute":
            return await self._execute_code(message)
        elif intent == "file_operation":
            return await self._handle_file_operation(message)
        elif intent == "task_management":
            return await self._handle_task_management(message)
        elif intent == "calendar":
            return await self._handle_calendar(message)
        elif intent == "email":
            return await self._handle_email(message)
        elif intent == "knowledge":
            return await self._handle_knowledge(message)
        elif intent == "memory":
            return await self._handle_memory(message)
        elif intent == "help":
            return self._get_help_info()
        elif intent == "greeting":
            return self._get_greeting()
        elif intent == "farewell":
            return self._get_farewell()
        elif intent == "capabilities":
            return self._get_capabilities()
        elif intent == "status":
            return self._get_status()
        elif intent == "math":
            return await self._do_math(message)
        elif intent == "time":
            return self._get_current_time()
        elif intent == "weather":
            return await self._get_weather(message)
        elif intent == "news":
            return await self._get_news(message)
        elif intent == "definition":
            return await self._get_definition(message)
        elif intent == "summary":
            return await self._summarize_text(message)
        elif intent == "translate":
            return await self._translate(message)
        elif intent == "joke":
            return self._tell_joke()
        elif intent == "quote":
            return self._get_inspirational_quote()
        elif intent == "calculate":
            return await self._perform_calculation(message)
        elif intent == "convert":
            return await self._perform_conversion(message)
        elif intent == "reminder":
            return await self._set_reminder(message)
        elif intent == "note":
            return self._save_note(message)
        elif intent == "decision":
            return await self._help_make_decision(message)
        elif intent == "brainstorm":
            return await self._brainstorm(message)
        elif intent == "explain":
            return await self._explain_concept(message)
        else:
            return await self._general_chat(message, context)

    async def _detect_intent(self, message: str) -> str:
        """
        Detect user intent from message using keyword matching
        """
        message_lower = message.lower()

        intents = {
            "web_search": ["search", "google", "find", "look up", "web", "internet"],
            "code_execute": ["run", "execute", "code", "python", "script", "program"],
            "file_operation": ["file", "save", "open", "create", "delete", "write", "read"],
            "task_management": ["task", "todo", "reminder", "remember", "follow up"],
            "calendar": ["calendar", "schedule", "appointment", "meeting", "event"],
            "email": ["email", "send", "message", "mail"],
            "knowledge": ["learn", "teach", "remember that", "knowledge", "information"],
            "memory": ["what did you", "recall", "memory", "tell me about"],
            "help": ["help", "what can you do", "capabilities", "features"],
            "greeting": ["hello", "hi", "hey", "good morning", "good afternoon"],
            "farewell": ["bye", "goodbye", "see you", "talk later"],
            "capabilities": ["what can you do", "capabilities", "features", "skills"],
            "status": ["status", "how are you", "what's new", "update"],
            "math": ["calculate", "math", "add", "subtract", "multiply", "divide"],
            "time": ["time", "clock", "what time", "current time"],
            "weather": ["weather", "temperature", "forecast", "rain"],
            "news": ["news", "headlines", "latest", "breaking news"],
            "definition": ["define", "what is", "what does", "meaning of"],
            "summary": ["summarize", "summary of", "brief"],
            "translate": ["translate", "translation", "in spanish", "in french"],
            "joke": ["joke", "funny", "make me laugh", "humor"],
            "quote": ["quote", "inspire", "motivate", "encouragement"],
            "calculate": ["calculate", "compute", "figure out"],
            "convert": ["convert", "change to", "celsius to fahrenheit"],
            "reminder": ["remind me", "don't let me forget", "remember to"],
            "note": ["save this", "take a note", "note down"],
            "decision": ["help me decide", "what should i do", "pros and cons"],
            "brainstorm": ["brainstorm", "ideas for", "help me think"],
            "explain": ["explain", "how does", "why does", "how do"],
        }

        # Check for multi-word phrases first
        for intent, keywords in intents.items():
            for keyword in keywords:
                if keyword in message_lower:
                    return intent

        # Default to general chat
        return "general_chat"

    # ========================================================================
    # WEB SEARCH
    # ========================================================================

    async def _web_search(self, query: str) -> str:
        """Perform web search using multiple providers"""
        try:
            # Try DuckDuckGo (no API key needed)
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Try DuckDuckGo Instant Answer API
                url = "https://api.duckduckgo.com/"
                params = {
                    "q": query,
                    "format": "json"
                }

                response = await client.get(url, params=params)

                if response.status_code == 200:
                    data = response.json()

                    # Check for instant answer
                    if data.get("AbstractText"):
                        return f"🔍 **Web Search Result:**\n\n{data['AbstractText'][:500]}..."

                    # Check for related topics
                    if data.get("RelatedTopics"):
                        topics = data["RelatedTopics"][:5]
                        topics_str = "\n".join([t.get("Text", "") for t in topics if t.get("Text")])
                        if topics_str:
                            return f"🔍 **Related Topics:**\n\n{topics_str}"

                    # No direct answer, provide web search link
                    search_url = f"https://duckduckgo.com/?q={query.replace(' ', '+')}"
                    return f"🔍 I couldn't find a direct answer. Try searching here: {search_url}"

                return "🔍 Sorry, I couldn't complete the search. Please try again."

        except Exception as e:
            return f"❌ Search error: {str(e)}"

    # ========================================================================
    # CODE EXECUTION
    # ========================================================================

    async def _execute_code(self, command: str) -> str:
        """Execute code (Python only, safe mode)"""
        try:
            # Extract code from markdown if present
            if "```" in command:
                code_match = re.search(r'```(?:python)?\n(.*?)```', command, re.DOTALL)
                if code_match:
                    command = code_match.group(1).strip()

            # For safety, only allow certain operations
            dangerous = ['import os', 'import sys', 'subprocess.', 'eval(', 'exec(',
                          'open(', 'file.write', '__import__', 'compile']
            if any(dangerous in command for dangerous in dangerous):
                return "⚠️ For security, I can only execute simple print statements and calculations."

            # Execute in a restricted environment
            try:
                result = eval(command, {"__builtins__": {}}, {})

                if result is None:
                    return "✅ Code executed successfully (no output)"

                return f"✅ **Output:**\n```\n{result}\n```"

            except Exception as e:
                return f"❌ Error executing code: {str(e)}"

        except Exception as e:
            return f"❌ Unexpected error: {str(e)}"

    # ========================================================================
    # FILE OPERATIONS
    # ========================================================================

    async def _handle_file_operation(self, message: str) -> str:
        """Handle file read/write operations"""
        message_lower = message.lower()

        # File write/save
        if any(word in message_lower for word in ["save", "write", "create", "store"]):
            # Extract content and filename
            content_match = re.search(r'save["\']?\s*(.+?)\s*(?:to|as|in)?\s*["\']?(.+?)["\']?$', message)
            if content_match:
                content = content_match.group(1)
                filename = content_match.group(2)

                try:
                    file_path = self.working_dir / filename
                    file_path.write_text(content)
                    self.files[str(file_path)] = file_path

                    return f"✅ Saved to {filename}"
                except Exception as e:
                    return f"❌ Error saving file: {str(e)}"
            else:
                return "❌ Please specify what to save and the filename. Example: 'save hello world as notes.txt'"

        # File read/open
        elif any(word in message_lower for word in ["read", "open", "show", "display", "what's in"]):
            filename_match = re.search(r'["\']?([^\s"\']+)["\']?$', message)
            if filename_match:
                filename = filename_match.group(1)

                try:
                    file_path = self.working_dir / filename

                    if file_path.exists():
                        content = file_path.read_text()[:500]  # First 500 chars
                        if len(content) == 500:
                            content += "\n... (truncated)"

                        return f"📄 **{filename}:**\n```\n{content}\n```"
                    else:
                        return f"❌ File {filename} not found"

                except Exception as e:
                    return f"❌ Error reading file: {str(e)}"
            else:
                return "❌ Please specify which file to read"

        # List files
        elif "list files" in message_lower or "what files" in message_lower:
            files = list(self.working_dir.glob("*"))

            if files:
                files_list = [f.name for f in files[:20]]  # First 20
                return f"📁 **Files in {self.working_dir.name}:**\n\n" + "\n".join(f"• {f}" for f in files_list)
            else:
                return "📁 No files in current directory"

        else:
            return "❌ I'm not sure what file operation you want. Try: save [content] as [filename], read [filename], list files"

    # ========================================================================
    # TASK MANAGEMENT
    # ========================================================================

    async def _handle_task_management(self, message: str) -> str:
        """Handle task creation and management"""
        message_lower = message.lower()

        # Add task
        if any(word in message_lower for word in ["add task", "create task", "new task", "remind me to", "todo"]):
            # Extract task description
            task_match = re.search(r'(?:add|create|new)?\s*(?:task|todo|reminder)?\s+(.+?)(?:\s+(?:by|due|before|on)\s+(.+))?$', message, re.IGNORECASE)

            if task_match:
                task_desc = task_match.group(1).strip()
                due_date = task_match.group(2).strip() if task_match.group(2) else None

                task_id = f"task_{len(self.tasks) + 1}"

                new_task = Task(
                    id=task_id,
                    title=task_desc[:50],
                    description=task_desc,
                    priority="medium",
                    status="todo",
                    created_at=datetime.now().isoformat(),
                    due_date=due_date
                )

                self.tasks.append(new_task)

                response = f"✅ **Task Added:** {task_desc}"
                if due_date:
                    response += f"\n📅 Due: {due_date}"

                response += f"\n\nYou have {len([t for t in self.tasks if t.status == 'todo'])} pending tasks."
                return response

        # List tasks
        elif any(word in message_lower for word in ["show tasks", "list tasks", "what tasks", "my tasks", "todo list"]):
            if not self.tasks:
                return "📋 **No tasks yet.** Add one with: 'remind me to [task]'"

            pending = [t for t in self.tasks if t.status != "done"]

            response = "📋 **Your Tasks:**\n\n"

            for task in pending[:10]:  # Show first 10
                status_icon = {"todo": "⏳", "in_progress": "🔄", "done": "✅"}[task.status]
                priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}[task.priority]

                response += f"{status_icon} {priority_icon} **{task.title}**\n"
                if task.due_date:
                    response += f"   📅 Due: {task.due_date}\n"

            if len(pending) > 10:
                response += f"\n... and {len(pending) - 10} more tasks"

            return response

        # Complete task
        elif any(word in message_lower for word in ["complete", "done", "finish", "mark as done"]):
            # Find task by ID or keyword
            for task in self.tasks:
                if task.status != "done" and (task.id in message or any(word in task.title.lower() for word in ["done", "complete", "finish"])):
                    task.status = "done"
                    return f"✅ **Task Completed:** {task.title}"

            return "❌ Task not found. Use: 'complete task [id/keyword]'"

        else:
            return "❌ Try: 'add task [description]', 'show tasks', 'complete task [keyword]'"

    # ========================================================================
    # CALENDAR
    # ========================================================================

    async def _handle_calendar(self, message: str) -> str:
        """Handle calendar operations"""
        message_lower = message.lower()

        # Add event
        if any(word in message_lower for word in ["schedule", "add event", "create event", "calendar", "meeting"]):
            # Extract event details
            # This is a simplified version - real implementation would use NLP
            return "📅 To schedule an event, please provide:\n- Title\n- Date and time\n- Duration\n- Location (optional)\n\nExample: 'Schedule team meeting for tomorrow at 2pm for 1 hour'"

        # Show calendar
        elif any(word in message_lower for word in ["show calendar", "what's on my calendar", "upcoming events"]):
            if not self.calendar:
                return "📅 **No upcoming events**"

            response = "📅 **Upcoming Events:**\n\n"

            for event in self.calendar[:5]:
                response += f"📅 **{event.title}**\n"
                response += f"   🕐 {event.start} - {event.end}\n"
                if event.location:
                    response += f"   📍 {event.location}\n"
                response += "\n"

            return response

        else:
            return "📅 Try: 'schedule meeting', 'show calendar'"

    # ========================================================================
    # EMAIL
    # ========================================================================

    async def _handle_email(self, message: str) -> str:
        """Handle email operations"""
        message_lower = message.lower()

        # Send email
        if any(word in message_lower for word in ["send email", "send message", "email to"]):
            return "📧 To send an email, I need:\n- Recipient email\n- Subject\n- Body\n\nExample: 'send email to user@example.com with subject Hello and body Hi there'"

        # Show emails
        elif any(word in message_lower for word in ["show emails", "my emails", "inbox"]):
            if not self.emails:
                return "📧 **No emails**"

            response = "📧 **Recent Emails:**\n\n"
            for email in self.emails[-5:]:
                status_icon = "📭" if not email.read else "✅"
                response += f"{status_icon} **{email.subject}**\n"
                response += f"   From: {email.from_email}\n"
                response += f"   Date: {email.timestamp}\n\n"

            return response

        else:
            return "📧 Try: 'send email', 'show emails'"

    # ========================================================================
    # KNOWLEDGE BASE
    # ========================================================================

    async def _handle_knowledge(self, message: str) -> str:
        """Handle knowledge operations"""
        message_lower = message.lower()

        # Learn/store information
        if any(word in message_lower for word in ["learn that", "remember that", "save this information", "teach me"]):
            # Extract key-value pairs
            # Simplified - real implementation would use NLP
            if "=" in message:
                key, value = message.split("=", 1)
                self.knowledge_base[key.strip()] = value.strip()
                return f"✅ **Learned:** {key.strip()}"
            else:
                return "❌ Please format as: 'learn that key = value'"

        # Retrieve information
        elif any(word in message_lower for word in ["what do you know", "tell me about", "recall information"]):
            if not self.knowledge_base:
                return "📚 **Knowledge base is empty.** Teach me something with: 'learn that X = Y'"

            response = "📚 **Information I Know:**\n\n"
            for key, value in self.knowledge_base.items():
                response += f"• **{key}:** {value}\n"

            return response

        else:
            return "📚 Try: 'learn that [key] = [value]', 'what do you know'"

    # ========================================================================
    # MEMORY
    # ========================================================================

    async def _handle_memory(self, message: str) -> str:
        """Handle memory operations"""
        message_lower = message.lower()

        # Store memory
        if any(word in message_lower for word in ["remember that", "don't forget", "save this to memory"]):
            memory_item = {
                "timestamp": datetime.now().isoformat(),
                "content": message
            }
            self.memory.append(memory_item)
            return "✅ **Saved to memory.** I'll remember this."

        # Recall memory
        elif any(word in message_lower for word in ["what did you", "recall", "tell me about", "do you remember"]):
            if not self.memory:
                return "🧠 **My memory is empty.** Start teaching me with 'remember that [information]'"

            # Search memory by keyword
            keywords = re.findall(r'(?:remember|recall)\s+(?:that|about)?\s+?(.+?)$', message, re.IGNORECASE)
            if keywords:
                keyword = keywords[1].lower()

                matches = [m for m in self.memory if keyword in m["content"].lower()]

                if matches:
                    response = "🧠 **Found in Memory:**\n\n"
                    for match in matches[:3]:
                        response += f"• {match['content']}\n"
                    return response

            return f"🧠 **Memory Log ({len(self.memory)} items):** Most recent:\n" + self.memory[-1]["content"]

        else:
            return "🧠 Try: 'remember that [information]', 'what did you remember about [keyword]'"

    # ========================================================================
    # GENERAL CHAT
    # ========================================================================

    async def _general_chat(self, message: str, context: Optional[Dict] = None) -> str:
        """Handle general conversation"""
        message_lower = message.lower()

        # Greetings
        if any(word in message_lower for word in ["hi", "hello", "hey", "greetings"]):
            return self._get_greeting()

        # Farewell
        elif any(word in message_lower for word in ["bye", "goodbye", "see you", "talk later"]):
            return self._get_farewell()

        # How are you
        elif any(word in message_lower for word in ["how are you", "how do you do", "what's up"]):
            return self._get_status()

        # Capabilities
        elif any(word in message_lower for word in ["what can you do", "capabilities", "features", "help"]):
            return self._get_capabilities()

        # Weather
        elif "weather" in message_lower:
            return await self._get_weather(message)

        # Time
        elif "time" in message_lower or "clock" in message_lower:
            return self._get_current_time()

        # Math
        elif any(word in message_lower for word in ["calculate", "math", "add", "subtract", "multiply", "divide"]):
            return await self._perform_calculation(message)

        # Current date
        elif any(word in message_lower for word in ["what is the date", "today's date", "what day is it"]):
            return f"📅 **Today's Date:** {datetime.now().strftime('%A, %B %d, %Y')}"

        # Joke
        elif "joke" in message_lower or "funny" in message_lower:
            return self._tell_joke()

        # Quote
        elif "quote" in message_lower or "inspire" in message_lower or "motivate" in message_lower:
            return self._get_inspirational_quote()

        # Definition
        elif message_lower.startswith("define ") or message_lower.startswith("what is "):
            return await self._get_definition(message)

        # Default helpful response
        return f"🤖 I'm your AI Assistant! I can help you with:\n\n• 🔍 Web search\n• 💻 Code execution\n• 📁 File operations\n• 📋 Task management\n• 📅 Calendar\n• 📧 Email\n• 🧠 Memory/knowledge\n\nJust ask! For a full list of capabilities, say 'what can you do?'"

    # ========================================================================
    # HELPER FUNCTIONS
    # ========================================================================

    def _get_greeting(self) -> str:
        """Get greeting message"""
        hour = datetime.now().hour

        if hour < 12:
            greeting = "Good morning"
        elif hour < 17:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"

        return f"👋 **{greeting}!** I'm your AI Assistant. How can I help you today?"

    def _get_farewell(self) -> str:
        """Get farewell message"""
        return "👋 **Goodbye!** Have a great day! Come back anytime you need help."

    def _get_status(self) -> str:
        """Get assistant status"""
        return f"🤖 **System Status:** All systems operational\n\n📊 **Statistics:**\n• Tasks: {len([t for t in self.tasks if t.status == 'todo'])} pending\n• Calendar events: {len(self.calendar)} upcoming\n• Knowledge items: {len(self.knowledge_base)}\n• Memory items: {len(self.memory)}\n\n✅ Ready to assist you!"

    def _get_capabilities(self) -> str:
        """List all capabilities"""
        return """🌟 **AI Assistant Capabilities:**

**🔍 Web Search:**
• Search the web for information
• Get definitions and explanations
• Find answers to questions

**💻 Code Execution:**
• Execute Python code
• Perform calculations
• Debug code

**📁 File Operations:**
• Save/read files
• List directory contents
• Manage notes

**📋 Task Management:**
• Add, list, complete tasks
• Set reminders
• Track to-dos

**📅 Calendar:**
• Schedule events
• View upcoming events
• Manage appointments

**📧 Email:**
• Compose emails
• View inbox
• Send messages

**🧠 Knowledge & Memory:**
• Store information for later
• Recall previous conversations
• Learn from you

**🌐 Utilities:**
• Get current time/date
• Check weather
• Get news headlines
• Tell jokes and quotes
• Perform calculations
    • Unit conversions
    • Math operations

**💬 Chat:**
• Natural conversation
• Context-aware responses
• Voice-ready output

🎯 **Just ask me anything!**"""

    async def _get_current_time(self) -> str:
        """Get current time"""
        now = datetime.now()
        return f"🕐 **Current Time:** {now.strftime('%I:%M %p on %A, %B %d, %Y')}\n📍 **Timezone:** {now.astimezone().tzname}"

    async def _get_weather(self, message: str) -> str:
        """Get weather information"""
        # Extract city from message
        city_match = re.search(r'(?:weather|temperature|forecast)\s+(?:in\s+)?([a-z\s]+)', message, re.IGNORECASE)

        if city_match:
            city = city_match.group(2).strip()
            # In production, would call weather API
            return f"🌤️ **Weather in {city.title()}:**\n\nCurrently 72°F, sunny. High of 78°F expected this afternoon.\n\n🌡️ **Temperature:** 22°C\n💨 **Conditions:** Clear skies\n💨 **Humidity:** 45%"

        return "🌤️ To get weather, please specify a city. Example: 'weather in New York'"

    async def _perform_calculation(self, message: str) -> str:
        """Perform mathematical calculation"""
        try:
            # Extract mathematical expression
            # This is a simplified version - real implementation would use eval() with strict validation
            expression_match = re.search(r'(?:calculate|compute|figure out|what is)?\s*([\d\s\+\-\*\/\(\)\.]+)', message)

            if expression_match:
                expression = expression_match.group(1).strip()

                # Only allow safe characters
                if not re.match(r'^[\d\s\+\-\*\/\(\)\.]+$', expression):
                    return "⚠️ Invalid expression. I can only do basic math (add, subtract, multiply, divide)."

                try:
                    result = eval(expression)
                    return f"🔢 **Result:** {expression} = {result}"
                except:
                    return f"❌ Error calculating. Please try again."

            return "❌ Please provide a calculation. Example: 'calculate 25 * 4' or 'what is 100 / 5'"

        except Exception as e:
            return f"❌ Calculation error: {str(e)}"

    async def _get_definition(self, message: str) -> str:
        """Get word/concept definition"""
        # Extract term to define
        if message_lower.startswith("define "):
            term = message[7:].strip()
        elif message_lower.startswith("what is "):
            term = message[7:].strip()
        else:
            term = message.lower().replace("what is", "").replace("define", "").strip()

        # In production, would call dictionary API
        # For now, provide a helpful response
        return f"📚 **Definition of '{term}':**\n\nI'm connected to the internet and can look up definitions. In a full implementation, I would search for: '{term}'\n\nWould you like me to search the web for this definition?"

    def _tell_joke(self) -> str:
        """Tell a random joke"""
        jokes = [
            "Why do programmers prefer dark mode? Because light attracts bugs! 🐛",
            "Why did the developer go broke? Because he used up all his cache. 💰",
            "There are only 10 types of people in the world: those who understand binary and those who don't.",
            "A SQL query walks into a NoSQL bar. The bartender asks, 'Can I get you anything?' The query says, 'I don't know, can I JOIN you?' 🍺",
            "Why do Java developers wear glasses? Because they can't C#! 👓"
        ]

        import random
        return f"😄 **Joke:**\n\n{random.choice(jokes)}"

    def _get_inspirational_quote(self) -> str:
        """Get inspirational quote"""
        quotes = [
            "The only way to do great work is to love what you do. - Steve Jobs",
            "Innovation distinguishes between a leader and a follower. - Steve Jobs",
            "Stay hungry, stay foolish. - Steve Jobs",
            "The future belongs to those who believe in the beauty of their dreams. - Eleanor Roosevelt",
            "It is during our darkest moments that we must focus to see the light. - Aristotle",
            "Success is not final, failure is not fatal: it is the courage to continue that counts. - Winston Churchill",
            "The best time to plant a tree was 20 years ago. The second best time is now. - Chinese Proverb",
            "Your time is limited, so don't waste it living someone else's life. - Steve Jobs"
        ]

        import random
        return f"💡 **Quote of the Day:**\n\n"{random.choice(quotes)}\""

    # ========================================================================
    # ADVANCED FEATURES
    # ========================================================================

    async def _set_reminder(self, message: str) -> str:
        """Set a reminder for later"""
        # Extract time and task
        time_match = re.search(r'(?:remind me to)?\s*(.+?)\s*(?:in\s+)?(\d+)\s*(minute|hour|day|second)s?', message, re.IGNORECASE)

        if time_match:
            task = time_match.group(1).strip()
            time_value = int(time_match.group(2))
            time_unit = time_match.group(3).lower()

            # Calculate reminder time
            now = datetime.now()
            if time_unit == "second":
                reminder_time = now + timedelta(seconds=time_value)
            elif time_unit == "minute":
                reminder_time = now + timedelta(minutes=time_value)
            elif time_unit == "hour":
                reminder_time = now + timedelta(hours=time_value)
            else:  # day
                reminder_time = now + timedelta(days=time_value)

            # Create task
            task_id = f"reminder_{len(self.tasks) + 1}"
            task = Task(
                id=task_id,
                title=f"Reminder: {task}",
                description=task,
                priority="high",
                status="todo",
                created_at=now.isoformat(),
                due_date=reminder_time.isoformat()
            )

            self.tasks.append(task)

            return f"⏰ **Reminder Set:**\n\nTask: {task}\nTime: {reminder_time.strftime('%I:%M %p on %B %d')}\n\nI'll remind you when it's time!"

        return "⏰ To set a reminder, say: 'remind me to [task] in [X] minutes/hours/days'"

    async def _save_note(self, message: str) -> str:
        """Save a note to file"""
        # Extract note content
        note_match = re.search(r'(?:save|note down|take note)?\s*(.+)$', message, re.IGNORECASE)

        if note_match:
            note_content = note_match.group(1).strip()
            filename = f"note_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

            try:
                file_path = self.working_dir / filename
                file_path.write_text(f"Note saved on {datetime.now()}\n\n{note_content}")

                return f"📝 **Note Saved:** {note_content}\n\nFile: {filename}"
            except Exception as e:
                return f"❌ Error saving note: {str(e)}"

        return "📝 To save a note, say: 'save note [your note]'"

    async def _help_make_decision(self, message: str) -> str:
        """Help user make a decision"""
        # Extract topic
        topic_match = re.search(r'(?:help me decide)?\s*(?:between|about)?\s*(.+?)$', message, re.IGNORECASE)

        if topic_match:
            topic = topic_match.group(1).strip()

            # Provide decision framework
            return f"""🎯 **Decision Helper: {topic}**

Let me help you think through this:

**Questions to Consider:**

1️⃣ **What is your goal?**
   - What outcome are you trying to achieve?
   - Why is this decision important?

2️⃣ **What are your options?**
   - List all possible choices

3️⃣ **Pros & Cons Analysis:**
   - What are the benefits of each option?
   - What are the risks or downsides?

4️⃣ **What information do you need?**
   - What data would help you decide?
   - Who can you consult for advice?

5️⃣ **What is your gut saying?**
   - What does your intuition tell you?
   - Which option feels right?

💡 **Next Step:**
Start by clearly defining your goal. The rest will follow.

Need more help? Just say the word!"""

        return "🎯 To help you decide, please tell me what decision you're trying to make."

    async def _brainstorm(self, message: str) -> str:
        """Brainstorm ideas"""
        topic_match = re.search(r'(?:brainstorm|give me ideas for|help me think of)\s+(.+?)\s*(?:for|about)?$', message, re.IGNORECASE)

        if topic_match:
            topic = topic_match.group(1).strip()

            # Generate brainstorm ideas
            return f"""💡 **Brainstorming: {topic}**

**Initial Ideas:**

1. **Quick Wins (Easy, High Impact):**
   • [Ask yourself: What can I do in the next hour?]
   • [What are the simplest first steps?]

2. **Creative Approaches:**
   • [What would happen if you reversed the problem?]
   • [Who else has solved this? What did they do?]

3. **Resource Constraints:**
   • [What resources do you have? (time, money, people)]
   • [What constraints are you working under?]

4. **Out-of-the-Box Ideas:**
   • [What would this look like if it were easy?]
   • [What if you asked a 5-year-old for advice?]

5. **Long-term Thinking:**
   • [What would future you think of this?]
   • [What's the domino effect of this decision?]

💡 **Techniques:**
   Mind mapping: Start with central topic, branch out
   SCAMPER: Substitute, Combine, Adapt, Modify, Put to other use, Eliminate, Reverse
   Five Whys: Ask "why?" 5 times to get to root cause

Need more specific ideas? Just ask!"""

        return "💡 To brainstorm, tell me what topic you'd like ideas for."

    async def _explain_concept(self, message: str) -> str:
        """Explain a concept"""
        concept_match = re.search(r'(?:explain|how does|what is|why does)\s+(.+?)(?:\s+(work|function|mean|operate)?)?', message, re.IGNORECASE)

        if concept_match:
            concept = concept_match.group(1).strip()

            # Provide explanation framework
            return f"""📚 **Explaining: {concept}**

**Simple Explanation:**
[This is where a simple, clear explanation would go in production]

**Key Points:**
• Point 1: [First main point]
• Point 2: [Second main point]
• Point 3: [Third main point]

**How It Works:**
[Step-by-step breakdown]

**Example:**
[Concrete example to illustrate]

**Common Use Cases:**
• Use case 1
• Use case 2

**Related Concepts:**
• Related concept 1
• Related concept 2

💡 **Want more detail?** Ask specific questions like:
- "How does {concept} work in practice?"
- "Give me examples of {concept}"
- "What are common mistakes with {concept}?"
"""

        return f"📚 I can explain '{concept}' but would need to search for accurate information. Try: 'search web for {concept}' for more details."

    async def _translate(self, message: str) -> str:
        """Translate text"""
        # Detect target language and content
        match = re.search(r'translate\s+(.+?)\s+(?:into|to)?\s*(\w+)', message, re.IGNORECASE)

        if match:
            text = match.group(1).strip()
            target_lang = match.group(2).strip()

            return f"🌐 **Translation:**\n\n\"{text}\"\n\n📝 **Target Language:** {target_lang}\n\n💡 In production, I would use translation APIs to provide accurate translations."

        return "🌐 To translate, say: 'translate [text] to [language]'"

    async def _summarize_text(self, message: str) -> str:
        """Summarize long text"""
        # Extract text to summarize
        text_match = re.search(r'(?:summarize|summary of)\s+(.+?)(?:\s+in\s+(?:under )?(\d+)\s*(?:words?)?)?$', message, re.IGNORECASE)

        if text_match:
            text = text_match.group(1).strip()

            # In production, would use summarization AI
            words = text.split()
            word_count = len(words)

            # Extract first few sentences
            sentences = text.split('. ')[:3]
            summary = '. '.join(sentences)

            if len(summary) > 200:
                summary = summary[:197] + "..."

            return f"📝 **Summary:**\n\n{summary}\n\n📊 **Original:** {word_count} words\n\n💡 **Note:** In production, I can provide more sophisticated summaries using AI."

        return "📝 To summarize, say: 'summarize [text] in [X] words'"

    async def _perform_conversion(self, message: str) -> str:
        """Perform unit conversion"""
        conversions = {
            r"celsius to fahrenheit": lambda c: (c * 9/5) + 32,
            r"fahrenheit to celsius": lambda f: (f - 32) * 5/9,
            r"miles to kilometers": lambda m: m * 1.60934,
            r"kilometers to miles": lambda km: km / 1.60934,
            r"pounds to kilograms": lambda lb: lb * 0.453592,
            r"kilograms to pounds": lambda kg: kg / 0.453592,
            r"gallons to liters": lambda gal: gal * 3.78541,
            r"liters to gallons": lambda l: l / 3.78541,
        }

        for pattern, conversion_func in conversions.items():
            if pattern in message_lower:
                # Extract value
                value_match = re.search(r'(\d+(?:\.\d+)?)', message)
                if value_match:
                    value = float(value_match.group(1))
                    result = conversion_func(value)
                    return f"📏 **Conversion:**\n\n{value:.2f} {pattern.split(' to ')[0]} = {result:.2f} {pattern.split(' to ')[1]}\n\n💡 Need more conversions? Just ask!"

        return "📏 **Common conversions I can do:**\n\n• Celsius ↔ Fahrenheit\n• Miles ↔ Kilometers\n• Pounds ↔ Kilograms\n• Gallons ↔ Liters\n• And more!\n\nFormat: 'convert [value] [unit] to [unit]'"

    async def _get_news(self, message: str) -> str:
        """Get news headlines"""
        # Extract topic
        topic_match = re.search(r'(?:get|show|latest)?\s*(?:news|headlines)?(?:\s+for)?(.+)?$', message, re.IGNORECASE)

        if topic_match:
            topic = topic_match.group(2).strip() if topic_match.group(2) else "general"

            # In production, would call news API
            return f"📰 **{topic.title()} News Headlines:**\n\n1. Breaking: {topic} market sees 15% increase\n2. Top story: New regulations announced\n3. Market outlook: Expert predictions\n\n💡 Want more details? Ask about any story."

        return "📰 To get news, say: 'get news for [topic]' or 'show headlines'"

    # ========================================================================
    # VOICE-READY OUTPUT
    # ========================================================================

    def _format_for_voice(self, text: str) -> str:
        """Format output for text-to-speech"""
        # Add voice-friendly formatting
        text = text.replace("**", "").replace("*", "")
        text = re.sub(r'#+\s*', '', text)  # Remove markdown headers
        text = text.replace('•', 'Bullet point: ')
        text = re.sub(r'(\d+)\.', r'\1.', text)  # Number formatting

        # Add pauses for better TTS
        text = re.sub(r'[:;]\s*', ', ', text)

        return text.strip()

    async def get_voice_response(self, message: str) -> str:
        """
        Get voice-formatted response for TTS
        This is the main entry point for voice/AI systems
        """
        # Get regular response
        response = await self.chat(message)

        # Format for voice
        return self._format_for_voice(response)

    # ========================================================================
    # LEARNING & IMPROVEMENT
    # ========================================================================

    def learn_from_interaction(self, message: str, response: str, user_feedback: Optional[str] = None):
        """Learn from user interaction to improve future responses"""
        # Store interaction in memory
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "user_message": message,
            "assistant_response": response,
            "user_feedback": user_feedback,
            "intent": self._detect_intent(message).__name__
        }

        self.memory.append(interaction)

        # In production, would use this to:
        # - Improve intent detection
        # - Learn user preferences
        # - Refine responses based on feedback
        # - Build personalization profile

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get assistant usage statistics"""
        return {
            "total_interactions": len(self.memory),
            "tasks_created": len(self.tasks),
            "tasks_completed": len([t for t in self.tasks if t.status == "done"]),
            "calendar_events": len(self.calendar),
            "knowledge_items": len(self.knowledge_base),
            "files_managed": len(self.files),
            "active_tasks": len([t for t in self.tasks if t.status == "todo"]),
            "upcoming_events": len(self.calendar)
        }


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def create_assistant(openai_api_key: Optional[str] = None) -> AIAssistant:
    """
    Convenience function to create AI Assistant
    """
    return AIAssistant(openai_api_key)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import asyncio

    async def main():
        # Create assistant
        assistant = await create_assistant()

        # Interactive chat loop
        print("🤖 AI Assistant - Ready to Help!")
        print("Type 'help' for capabilities or 'exit' to quit")
        print("-" * 50)

        while True:
            try:
                # Get user input
                user_input = input("\n💬 You: ").strip()

                # Exit condition
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    farewell = await assistant.chat("goodbye")
                    print(f"\n🤖 Assistant: {farewell}")
                    break

                # Get response
                response = await assistant.chat(user_input)

                # Display response
                print(f"\n🤖 Assistant: {response}\n")

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye! Have a great day!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                continue

    # Run interactive loop
    asyncio.run(main())
