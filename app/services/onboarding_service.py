"""Agent onboarding questionnaire service.

Captures agent preferences, business info, and goals when they first join.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.agent import Agent
from app.services.memory_graph import memory_graph_service
from app.services.llm_service import llm_service


class OnboardingQuestion:
    """Single onboarding question."""

    def __init__(
        self,
        question_id: str,
        question: str,
        question_type: str,  # text, choice, multiselect, boolean, number
        options: Optional[List[str]] = None,
        placeholder: Optional[str] = None,
        required: bool = False,
        category: str = "general"
    ):
        self.question_id = question_id
        self.question = question
        self.question_type = question_type
        self.options = options or []
        self.placeholder = placeholder
        self.required = required
        self.category = category


# Core onboarding questions
ONBOARDING_QUESTIONS = [
    # Basic Info
    OnboardingQuestion(
        question_id="agent_name",
        question="What's your full name?",
        question_type="text",
        placeholder="John Smith",
        required=True,
        category="basic"
    ),
    OnboardingQuestion(
        question_id="agent_email",
        question="What's your email address?",
        question_type="text",
        placeholder="john@example.com",
        required=True,
        category="basic"
    ),
    OnboardingQuestion(
        question_id="brokerage_name",
        question="What's your brokerage or company name?",
        question_type="text",
        placeholder="Miami Realty Partners",
        required=True,
        category="basic"
    ),
    OnboardingQuestion(
        question_id="license_number",
        question="What's your real estate license number?",
        question_type="text",
        placeholder="RK12345678",
        required=False,
        category="basic"
    ),
    OnboardingQuestion(
        question_id="years_experience",
        question="How many years of real estate experience do you have?",
        question_type="choice",
        options=["Less than 1 year", "1-3 years", "3-5 years", "5-10 years", "10+ years"],
        required=True,
        category="basic"
    ),

    # Business Focus
    OnboardingQuestion(
        question_id="primary_market",
        question="What's your primary market area?",
        question_type="text",
        placeholder="Miami, FL",
        required=True,
        category="business"
    ),
    OnboardingQuestion(
        question_id="property_types",
        question="What property types do you specialize in?",
        question_type="multiselect",
        options=["Residential", "Commercial", "Land", "Multi-family", "Luxury", "Investment", "Condos", "Single-family"],
        required=True,
        category="business"
    ),
    OnboardingQuestion(
        question_id="price_range_min",
        question="What's your typical minimum property price?",
        question_type="choice",
        options=["Under $200k", "$200k-$400k", "$400k-$600k", "$600k-$1M", "$1M+"],
        required=True,
        category="business"
    ),
    OnboardingQuestion(
        question_id="price_range_max",
        question="What's your typical maximum property price?",
        question_type="choice",
        options=["Under $200k", "$200k-$400k", "$400k-$600k", "$600k-$1M", "$1M+"],
        required=True,
        category="business"
    ),
    OnboardingQuestion(
        question_id="deal_volume",
        question="How many deals do you typically close per month?",
        question_type="choice",
        options=["1-2 deals", "3-5 deals", "5-10 deals", "10+ deals"],
        required=True,
        category="business"
    ),

    # Target Clients
    OnboardingQuestion(
        question_id="target_clients",
        question="Who are your primary clients?",
        question_type="multiselect",
        options=["First-time buyers", "Investors", "Luxury buyers", "Sellers", "Relocation", "Vacation homes", "Rentals"],
        required=True,
        category="clients"
    ),
    OnboardingQuestion(
        question_id="lead_sources",
        question="What are your main lead sources?",
        question_type="multiselect",
        options=["Zillow", "Realtor.com", "Referrals", "Social media", "Website", "Cold calling", "Open houses", "Networking"],
        required=True,
        category="clients"
    ),

    # Technology & Tools
    OnboardingQuestion(
        question_id="current_crm",
        question="Do you currently use a CRM system?",
        question_type="choice",
        options=["Yes", "No", "Looking for one"],
        required=True,
        category="technology"
    ),
    OnboardingQuestion(
        question_id="crm_name",
        question="Which CRM do you use?",
        question_type="text",
        placeholder="Follow Up Boss, KVCore, etc.",
        required=False,
        category="technology"
    ),
    OnboardingQuestion(
        question_id="tech_savviness",
        question="How comfortable are you with technology?",
        question_type="choice",
        options=["Very comfortable", "Somewhat comfortable", "Learning", "Prefer traditional methods"],
        required=True,
        category="technology"
    ),

    # Goals & Preferences
    OnboardingQuestion(
        question_id="monthly_goals",
        question="What's your monthly revenue goal?",
        question_type="choice",
        options=["Under $10k", "$10k-$25k", "$25k-$50k", "$50k-$100k", "$100k+"],
        required=True,
        category="goals"
    ),
    OnboardingQuestion(
        question_id="biggest_challenge",
        question="What's your biggest business challenge?",
        question_type="choice",
        options=["Finding qualified leads", "Following up consistently", "Closing deals", "Managing time", "Staying organized", "Marketing"],
        required=True,
        category="goals"
    ),
    OnboardingQuestion(
        question_id="want_help_with",
        question="What do you want AI help with most?",
        question_type="multiselect",
        options=[
            "Lead follow-up automation",
            "Property research & analysis",
            "Contract management",
            "Market insights",
            "Daily planning",
            "Client communication",
            "Task reminders",
            "Deal negotiation"
        ],
        required=True,
        category="goals"
    ),

    # Communication
    OnboardingQuestion(
        question_id="preferred_hours",
        question="What are your preferred working hours?",
        question_type="choice",
        options=["Early bird (6AM-2PM)", "Standard (9AM-5PM)", "Flexible", "Night owl (12PM-8PM)"],
        required=True,
        category="communication"
    ),
    OnboardingQuestion(
        question_id="notification_preference",
        question="How do you prefer to receive updates?",
        question_type="multiselect",
        options=["Email digest", "SMS alerts", "Push notifications", "Daily briefing", "Weekly summary"],
        required=True,
        category="communication"
    ),
    OnboardingQuestion(
        question_id="weekly_checkin",
        question="Would you like a weekly performance summary?",
        question_type="boolean",
        required=True,
        category="communication"
    ),
]


class OnboardingService:
    """Agent onboarding questionnaire service."""

    @staticmethod
    def get_questions(category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get onboarding questions, optionally filtered by category."""
        questions = ONBOARDING_QUESTIONS

        if category:
            questions = [q for q in questions if q.category == category]

        return [
            {
                "question_id": q.question_id,
                "question": q.question,
                "type": q.question_type,
                "options": q.options,
                "placeholder": q.placeholder,
                "required": q.required,
                "category": q.category
            }
            for q in questions
        ]

    @staticmethod
    def get_categories() -> List[str]:
        """Get all question categories."""
        categories = set(q.category for q in ONBOARDING_QUESTIONS)
        return sorted(categories)

    @staticmethod
    async def save_onboarding_answers(
        db: Session,
        agent_id: int,
        answers: Dict[str, Any],
        session_id: str
    ) -> Dict[str, Any]:
        """Save onboarding answers to memory graph."""

        try:
            # Update agent record with basic info
            agent = db.query(Agent).filter(Agent.id == agent_id).first()
            if not agent:
                return {"status": "error", "message": "Agent not found"}

            # Update basic fields
            if "agent_name" in answers:
                agent.name = answers["agent_name"]
            if "agent_email" in answers:
                agent.email = answers["agent_email"]
            if "brokerage_name" in answers:
                # Store in agent preferences or settings
                pass
            db.commit()

            # Store identity in memory graph
            memory_graph_service.remember_identity(
                db=db,
                session_id=session_id,
                entity_type="agent",
                entity_id=str(agent_id),
                identity_data={
                    "name": answers.get("agent_name", agent.name),
                    "email": answers.get("agent_email", agent.email),
                    "brokerage": answers.get("brokerage_name"),
                    "license": answers.get("license_number"),
                    "experience": answers.get("years_experience"),
                    "summary": f"{answers.get('agent_name', agent.name)} - {answers.get('brokerage_name', 'Agent')}"
                }
            )

            # Store business focus as facts
            if "primary_market" in answers:
                memory_graph_service.remember_fact(
                    db=db,
                    session_id=session_id,
                    fact=f"Primary market: {answers['primary_market']}",
                    category="business_focus"
                )

            if "property_types" in answers:
                memory_graph_service.remember_fact(
                    db=db,
                    session_id=session_id,
                    fact=f"Specializes in: {', '.join(answers['property_types'])}",
                    category="business_focus"
                )

            # Store price range
            if "price_range_min" in answers and "price_range_max" in answers:
                memory_graph_service.remember_fact(
                    db=db,
                    session_id=session_id,
                    fact=f"Typical price range: {answers['price_range_min']} - {answers['price_range_max']}",
                    category="business_focus"
                )

            # Store deal volume as fact
            if "deal_volume" in answers:
                memory_graph_service.remember_fact(
                    db=db,
                    session_id=session_id,
                    fact=f"Typical deal volume: {answers['deal_volume']}",
                    category="business_metrics"
                )

            # Store target clients as preferences
            if "target_clients" in answers:
                for client_type in answers["target_clients"]:
                    memory_graph_service.remember_preference(
                        db=db,
                        session_id=session_id,
                        preference=f"Targets {client_type.lower()}",
                        entity_type="agent",
                        entity_id=str(agent_id)
                    )

            # Store lead sources
            if "lead_sources" in answers:
                memory_graph_service.remember_fact(
                    db=db,
                    session_id=session_id,
                    fact=f"Lead sources: {', '.join(answers['lead_sources'])}",
                    category="business_strategy"
                )

            # Store goals
            if "monthly_goals" in answers:
                memory_graph_service.remember_goal(
                    db=db,
                    session_id=session_id,
                    goal=f"Achieve {answers['monthly_goals']} in monthly revenue",
                    metadata={"goal_type": "revenue", "amount": answers['monthly_goals']},
                    priority="high"
                )

            # Store biggest challenge as observation
            if "biggest_challenge" in answers:
                memory_graph_service.remember_observation(
                    db=db,
                    session_id=session_id,
                    observation=f"Biggest challenge: {answers['biggest_challenge']}",
                    category="business_challenge",
                    confidence=1.0
                )

            # Store AI help preferences
            if "want_help_with" in answers:
                for help_area in answers["want_help_with"]:
                    memory_graph_service.remember_preference(
                        db=db,
                        session_id=session_id,
                        preference=f"Wants AI help with {help_area.lower()}",
                        entity_type="agent",
                        entity_id=str(agent_id)
                    )

            # Store communication preferences
            if "preferred_hours" in answers:
                memory_graph_service.remember_preference(
                    db=db,
                    session_id=session_id,
                    preference=f"Prefers working hours: {answers['preferred_hours']}",
                    entity_type="agent",
                    entity_id=str(agent_id)
                )

            if "notification_preference" in answers:
                memory_graph_service.remember_fact(
                    db=db,
                    session_id=session_id,
                    fact=f"Notification preferences: {', '.join(answers['notification_preference'])}",
                    category="communication"
                )

            if "weekly_checkin" in answers:
                memory_graph_service.remember_preference(
                    db=db,
                    session_id=session_id,
                    preference=f"Wants weekly checkin: {answers['weekly_checkin']}",
                    entity_type="agent",
                    entity_id=str(agent_id)
                )

            return {
                "status": "success",
                "message": "Onboarding answers saved successfully",
                "agent_id": agent_id,
                "answers_saved": len(answers)
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to save answers: {str(e)}"
            }

    @staticmethod
    async def generate_personalized_welcome(
        db: Session,
        agent_id: int,
        session_id: str
    ) -> Dict[str, Any]:
        """Generate personalized welcome message based on onboarding answers."""

        try:
            # Get agent's memory summary
            summary = memory_graph_service.get_session_summary(db, session_id, max_nodes=50)

            # Get agent info
            agent = db.query(Agent).filter(Agent.id == agent_id).first()
            if not agent:
                return {"status": "error", "message": "Agent not found"}

            # Build context for AI
            context = {
                "agent_name": agent.name,
                "brokerage": summary["session_state"].get("brokerage_name"),
                "experience": summary["session_state"].get("years_experience"),
                "market": summary["session_state"].get("primary_market"),
                "property_types": summary["session_state"].get("property_types"),
                "price_range": f"{summary['session_state'].get('price_range_min')} - {summary['session_state'].get('price_range_max')}",
                "deal_volume": summary["session_state"].get("deal_volume"),
                "target_clients": summary["session_state"].get("target_clients"),
                "biggest_challenge": summary["session_state"].get("biggest_challenge"),
                "want_help_with": summary["session_state"].get("want_help_with"),
                "goals": summary["session_state"].get("monthly_goals")
            }

            # Generate AI welcome message
            prompt = f"""You are an AI real estate assistant welcoming a new agent.

Agent Name: {context['agent_name']}
Brokerage: {context.get('brokerage', 'Independent')}
Experience: {context.get('experience', 'New agent')}
Market: {context.get('market', 'Not specified')}
Property Types: {', '.join(context.get('property_types', ['Not specified']))}
Price Range: {context.get('price_range', 'Not specified')}
Deal Volume: {context.get('deal_volume', 'Not specified')}
Target Clients: {', '.join(context.get('target_clients', ['Not specified']))}
Biggest Challenge: {context.get('biggest_challenge', 'Not specified')}
Goals: {context.get('goals', 'Not specified')}
Wants Help With: {', '.join(context.get('want_help_with', ['Not specified']))}

Generate a warm, personalized welcome message that:
1. Welcomes them by name
2. Acknowledges their experience level
3. References their specific market/focus
4. Addresses their biggest challenge
5. Mentions how AI can help with their goals
6. Is 3-4 paragraphs max
7. Is conversational and friendly

Don't use markdown. Just plain text."""

            response = await llm_service.generate_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500
            )

            welcome_message = response.get("content", "").strip()

            return {
                "status": "success",
                "welcome_message": welcome_message,
                "agent_name": agent.name,
                "onboarding_complete": True
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to generate welcome: {str(e)}"
            }

    @staticmethod
    async def complete_onboarding_wizard(
        db: Session,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Complete onboarding from landing page wizard and create agent account."""

        try:
            from app.models.agent import Agent
            from app.models.agent_onboarding import AgentOnboarding
            import secrets
            from datetime import datetime

            # Check if email already exists
            existing_agent = db.query(Agent).filter(Agent.email == data.get("email")).first()
            if existing_agent:
                return {
                    "status": "error",
                    "message": "An account with this email already exists"
                }

            # Create agent account
            agent = Agent(
                name=f"{data.get('first_name')} {data.get('last_name')}",
                email=data.get("email"),
                phone=data.get("phone"),
                city=data.get("city"),
                created_at=datetime.utcnow()
            )
            db.add(agent)
            db.flush()  # Get the agent ID

            # Create onboarding record
            # Handle skipped license number
            license_number = data.get("license_number")
            if license_number == "_SKIPPED_":
                license_number = None

            onboarding = AgentOnboarding(
                agent_id=agent.id,
                first_name=data.get("first_name"),
                last_name=data.get("last_name"),
                age=data.get("age"),
                city=data.get("city"),
                address=data.get("address"),
                phone=data.get("phone"),
                email=data.get("email"),
                license_number=license_number,
                business_name=data.get("business_name"),
                business_card_image=data.get("business_card_image"),
                logo_url=data.get("logo"),
                colors=data.get("colors"),
                schedule=data.get("schedule"),
                weekend_schedule=data.get("weekend_schedule"),
                contacts_uploaded=bool(data.get("contacts_file")),
                social_media=data.get("social_media"),
                music_preferences=data.get("music_preferences", []),
                contracts_used=data.get("contracts", []),
                calendar_connected=data.get("connect_calendar", False),
                primary_market=data.get("primary_market"),
                secondary_markets=data.get("secondary_markets"),
                service_radius=data.get("service_radius"),
                office_locations=data.get("office_locations"),
                assistant_name=data.get("assistant_name"),
                assistant_style=data.get("assistant_style"),
                personality_traits=data.get("personality"),
                completed_at=datetime.utcnow(),
                onboarding_complete=True
            )
            db.add(onboarding)

            # Store in memory graph for AI context
            session_id = secrets.token_urlsafe(16)

            # Identity
            memory_graph_service.remember_identity(
                db=db,
                session_id=session_id,
                entity_type="agent",
                entity_id=str(agent.id),
                identity_data={
                    "name": agent.name,
                    "email": agent.email,
                    "phone": agent.phone,
                    "city": agent.city,
                    "business": data.get("business_name"),
                    "assistant_name": data.get("assistant_name"),
                    "summary": f"{agent.name} from {agent.city} - {data.get('business_name')}"
                }
            )

            # Schedule preferences
            if data.get("schedule"):
                for day, times in data["schedule"].items():
                    if not times.get("off"):
                        memory_graph_service.remember_preference(
                            db=db,
                            session_id=session_id,
                            preference=f"Works {day.capitalize()} from {times.get('start')} to {times.get('end')}",
                            entity_type="agent",
                            entity_id=str(agent.id)
                        )

            # Market info
            memory_graph_service.remember_fact(
                db=db,
                session_id=session_id,
                fact=f"Primary market: {data.get('primary_market')}",
                category="business_focus"
            )

            if data.get("secondary_markets"):
                memory_graph_service.remember_fact(
                    db=db,
                    session_id=session_id,
                    fact=f"Secondary markets: {data.get('secondary_markets')}",
                    category="business_focus"
                )

            # Social media
            if data.get("social_media"):
                for platform, handle in data["social_media"].items():
                    if handle:
                        memory_graph_service.remember_fact(
                            db=db,
                            session_id=session_id,
                            fact=f"{platform.capitalize()}: {handle}",
                            category="social_media"
                        )

            # Music preferences
            if data.get("music_preferences"):
                memory_graph_service.remember_preference(
                    db=db,
                    session_id=session_id,
                    preference=f"Listening to: {', '.join(data['music_preferences'])}",
                    entity_type="agent",
                    entity_id=str(agent.id)
                )

            # Contracts
            if data.get("contracts"):
                memory_graph_service.remember_fact(
                    db=db,
                    session_id=session_id,
                    fact=f"Uses contracts: {', '.join(data['contracts'])}",
                    category="business_strategy"
                )

            # Assistant personality
            if data.get("personality"):
                personality_desc = ", ".join([f"{trait}: {value}/100" for trait, value in data["personality"].items()])
                memory_graph_service.remember_preference(
                    db=db,
                    session_id=session_id,
                    preference=f"Assistant style: {data.get('assistant_style')} ({personality_desc})",
                    entity_type="assistant",
                    entity_id=data.get("assistant_name", "AI")
                )

            db.commit()

            return {
                "status": "success",
                "message": "Account created successfully",
                "agent_id": agent.id,
                "session_id": session_id,
                "assistant_name": data.get("assistant_name"),
                "assistant_style": data.get("assistant_style")
            }

        except Exception as e:
            db.rollback()
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "message": f"Failed to create account: {str(e)}"
            }


onboarding_service = OnboardingService()
